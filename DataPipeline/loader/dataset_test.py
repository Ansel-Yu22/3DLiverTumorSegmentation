import os
import torch
import numpy as np
import SimpleITK as sitk
from glob import glob
from scipy import ndimage
from torch.utils.data import Dataset


class Test_DataSet(Dataset):
    def __init__(self, ct_path, label_path, args):
        self.n_label = args.n_label
        self.cut_size = args.tc_size
        self.cut_stride = args.tc_stride
        # 读取 ct 图像并转化为 numpy 数组
        self.ct = sitk.ReadImage(ct_path, sitk.sitkInt16)
        self.ct_np = sitk.GetArrayFromImage(self.ct)
        # 保存原始图像的形状 (深度, 高度, 宽度)
        self.ori_shape = self.ct_np.shape
        # 对图像进行缩放，z 轴和 xy 平面使用不同的缩放比例，双三次插值
        self.ct_np = ndimage.zoom(self.ct_np, (args.z_down_scale, args.xy_down_scale, args.xy_down_scale), order=3)
        # 保存缩放后的图像形状
        self.resized_shape = self.ct_np.shape
        # 将图像值限制在指定范围内
        self.ct_np[self.ct_np > args.upper] = args.upper
        self.ct_np[self.ct_np < args.lower] = args.lower
        # 对图像值进行归一化处理
        self.ct_np = (self.ct_np + 100) / 400
        self.ct_np = self.ct_np.astype(np.float32)
        # 对图像进行 padding，确保深度维度能被步长整除
        self.ct_np = self.padding_ct(self.ct_np, self.cut_size, self.cut_stride)
        # 保存 padding 后的图像形状
        self.padding_shape = self.ct_np.shape
        # 提取有序的重叠 patch，用于后续预测
        self.ct_np = self.extract_ordered_overlap(self.ct_np, self.cut_size, self.cut_stride)
        # 读取标签图像并转化为 numpy 数组
        self.seg = sitk.ReadImage(label_path, sitk.sitkInt8)
        self.label_np = sitk.GetArrayFromImage(self.seg)
        # 如果是二分类任务，将所有非零标签值设为 1
        if self.n_label == 2:
            self.label_np[self.label_np > 0] = 1
        # 将标签转换为 PyTorch 张量，并增加 batch 维度 (1, 深度, 高度, 宽度)
        self.label = torch.from_numpy(np.expand_dims(self.label_np, axis=0)).long()
        # 初始化预测结果，初始值为 None，后续存储模型输出
        self.result = None

    def __getitem__(self, index):
        # 从预处理后的 patch 数组中提取指定索引的 patch
        data = torch.from_numpy(self.ct_np[index])
        # 转换为浮点张量并增加通道维度，形状为 (1, 深度, 高度, 宽度)
        data = torch.FloatTensor(data).unsqueeze(0)
        # 返回 patch 数据
        return data

    def __len__(self):
        # 返回 patch 数组的第一维度大小，即 patch 数量
        return len(self.ct_np)

    def update_result(self, tensor):
        # 如果已有预测结果，则将新结果拼接起来
        if self.result is not None:
            self.result = torch.cat((self.result, tensor), dim=0)
        # 如果没有预测结果，则直接赋值
        else:
            self.result = tensor

    def recompone_result(self):
        # 获取 patch 的深度大小
        patch_s = self.result.shape[2]
        # 计算图像中的 patch 数量
        N_patches_ct = (self.padding_shape[0] - patch_s) // self.cut_stride + 1
        # 确保预测结果的 patch 数量与计算值一致
        assert (self.result.shape[0] == N_patches_ct)
        # 初始化完整概率张量，形状为 (类别数, 深度, 原始高度, 原始宽度)
        full_prob = torch.zeros((self.n_label, self.padding_shape[0], self.ori_shape[1], self.ori_shape[2]))
        # 初始化重叠次数张量，记录每个像素被多少个 patch 覆盖
        full_sum = torch.zeros((self.n_label, self.padding_shape[0], self.ori_shape[1], self.ori_shape[2]))
        # 遍历每个 patch，将预测概率累加到对应位置
        for s in range(N_patches_ct):
            full_prob[:, s * self.cut_stride:s * self.cut_stride + patch_s] += self.result[s]
            full_sum[:, s * self.cut_stride:s * self.cut_stride + patch_s] += 1
        # 确保每个位置至少被一个 patch 覆盖
        assert (torch.min(full_sum) >= 1.0)
        # 计算平均概率，消除重叠影响
        final_avg = full_prob / full_sum
        # 确保概率值在 [0, 1] 范围内
        assert (torch.max(final_avg) <= 1.0)
        assert (torch.min(final_avg) >= 0.0)
        # 裁剪到原始图像形状，去除 padding 部分
        ct = final_avg[:, :self.ori_shape[0], :self.ori_shape[1], :self.ori_shape[2]]
        # 增加 batch 维度返回，形状为 (1, 类别数, 深度, 高度, 宽度)
        return ct.unsqueeze(0)

    def padding_ct(self, ct, size, stride):
        # 打印原始形状
        # print("Original ct shape: " + str(self.ori_shape))
        # 确保输入图像是 3D 数组
        assert (len(ct.shape) == 3)
        # 获取图像的深度、高度和宽度
        ct_s, ct_h, ct_w = ct.shape
        # 计算深度维度除以步长后的余数
        leftover_s = (ct_s - size) % stride
        # 如果有余数，计算需要 padding 到的深度
        if (leftover_s != 0):
            s = ct_s + (stride - leftover_s)
        else:
            s = ct_s
        # 初始化 padding 后的图像数组，填充值为 0
        tmp_full_imgs = np.zeros((s, ct_h, ct_w), dtype=np.float32)
        # 将原始图像复制到新数组的前部
        tmp_full_imgs[:ct_s] = ct
        # 打印 padding 后的图像形状
        # print("Padded ct shape: " + str(tmp_full_imgs.shape))
        # 返回 padding 后的图像
        return tmp_full_imgs

    def extract_ordered_overlap(self, ct, size, stride):
        # 获取图像的深度、高度和宽度
        ct_s, ct_h, ct_w = ct.shape
        # 确保深度维度减去 patch 大小后能被步长整除
        assert (ct_s - size) % stride == 0
        # 计算 patch 数量
        N_patches_ct = (ct_s - size) // stride + 1
        # 打印 patch 数量
        # print("Patches number of the ct:{}".format(N_patches_ct))
        # 初始化 patch 数组，形状为 (patch 数量, 深度, 高度, 宽度)
        patches = np.empty((N_patches_ct, size, ct_h, ct_w), dtype=np.float32)
        # 遍历并提取每个 patch
        for s in range(N_patches_ct):
            patch = ct[s * stride: s * stride + size]
            patches[s] = patch
        # 返回 patch 数组
        return patches

def Test_Datasets(dataset_path, args):
    # 获取 CT 图像和标签图像路径列表并排序
    ct_list = sorted(glob(os.path.join(dataset_path, 'ct/*')))
    label_list = sorted(glob(os.path.join(dataset_path, 'label/*')))
    # 打印测试样本数量
    print("The number of test samples is: ", len(ct_list))
    # 遍历 CT 和标签路径对
    for ct_path, label_path in zip(ct_list, label_list):
        # 打印当前处理的 CT 图像文件名
        print("========== {} ==========".format(os.path.basename(ct_path)))
        # 创建 Test_DataSet 实例并返回，同时返回文件名
        yield Test_DataSet(ct_path, label_path, args=args), ct_path.split('-')[-1]