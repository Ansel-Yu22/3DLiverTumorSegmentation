import DataPipeline.loader.transform as tf
import os
import torch
import numpy as np
import SimpleITK as sitk
from torch.utils.data import Dataset


class Train_Dataset(Dataset):
    def __init__(self, args):
        self.args = args
        # 加载训练数据路径列表并存储
        self.filename_list = self.load_file_name_list(os.path.join(self.args.final_data, 'train_path.txt'))
        # 定义数据增强操作
        self.transform = tf.Compose([
            # 随机深度裁剪
            tf.RandomCrop(self.args.rc_size),
            # 随机左右翻转
            tf.RandomFlipLR(self.args.prob),
            # 随机上下翻转
            tf.RandomFlipUD(self.args.prob),
            # 随机90度旋转
            tf.RandomRotation90(self.args.prob),
            # 随机平移
            tf.RandomTranslation(self.args.prob),
            # 随机高斯噪声
            tf.RandomNoise(self.args.prob)
        ])

    def __getitem__(self, index):
        # 读取CT图像和分割图像并换为NumPy数组
        ct = sitk.ReadImage(self.filename_list[index][0], sitk.sitkInt16)
        ct_array = sitk.GetArrayFromImage(ct)
        seg = sitk.ReadImage(self.filename_list[index][1], sitk.sitkUInt8)
        seg_array = sitk.GetArrayFromImage(seg)
        # 将CT图像的灰度值归一化
        ct_array = (ct_array + 100) / 400
        ct_array = ct_array.astype(np.float32)
        # 将NumPy数组转换为PyTorch张量，并为通道添加一个维度
        ct_array = torch.FloatTensor(ct_array).unsqueeze(0)
        seg_array = torch.FloatTensor(seg_array).unsqueeze(0)
        # 如果定义了数据增强变换，则进行变换
        if self.transform:
            ct_array, seg_array = self.transform(ct_array, seg_array)
        # 返回处理后的CT图像和分割图像
        return ct_array, seg_array.squeeze(0)

    def __len__(self):
        # 返回数据集的大小（即文件列表的长度）
        return len(self.filename_list)

    def load_file_name_list(self, file_path):
        # 从文件中读取所有图像路径，并按空白字符分割
        with open(file_path, 'r') as file_to_read:
            # 使用列表推导将每一行按空白字符分割后添加到列表中
            file_name_list = [line.strip().split() for line in file_to_read if line.strip()]
        # 返回文件路径列表
        return file_name_list

class Val_Dataset(Dataset):
    def __init__(self, args):
        self.args = args
        # 加载训练数据路径列表并存储
        self.filename_list = self.load_file_name_list(os.path.join(self.args.final_data, 'val_path.txt'))
        # 定义数据增强变换操作
        self.transforms = tf.Compose([
            # 中心裁剪，base是裁剪的最小尺寸，max_size是最大尺寸
            tf.CenterCrop(base=16, max_size=self.args.cc_size)
        ])

    def __getitem__(self, index):
        # 读取CT图像和分割图像并转换为NumPy数组
        ct = sitk.ReadImage(self.filename_list[index][0], sitk.sitkInt16)
        ct_array = sitk.GetArrayFromImage(ct)
        seg = sitk.ReadImage(self.filename_list[index][1], sitk.sitkUInt8)
        seg_array = sitk.GetArrayFromImage(seg)
        # 将CT图像的灰度值归一化
        ct_array = (ct_array + 100) / 400
        ct_array = ct_array.astype(np.float32)
        # 将NumPy数组转换为PyTorch张量，并为通道添加一个维度
        ct_array = torch.FloatTensor(ct_array).unsqueeze(0)
        seg_array = torch.FloatTensor(seg_array).unsqueeze(0)
        # 如果定义了数据增强变换，则进行变换
        if self.transforms:
            ct_array, seg_array = self.transforms(ct_array, seg_array)
        # 返回处理后的CT图像和分割图像
        return ct_array, seg_array.squeeze(0)

    def __len__(self):
        # 返回数据集的大小（即文件列表的长度）
        return len(self.filename_list)

    def load_file_name_list(self, file_path):
        # 从文件中读取所有图像路径，并按空白字符分割
        with open(file_path, 'r') as file_to_read:
            # 使用列表推导将每一行按空白字符分割后添加到列表中
            file_name_list = [line.strip().split() for line in file_to_read if line.strip()]
        # 返回文件路径列表
        return file_name_list
