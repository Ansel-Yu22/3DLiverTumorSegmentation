import config
import os
import random
import numpy as np
import SimpleITK as sitk
from os.path import join
from scipy import ndimage


class DataPreprocess:
    def __init__(self, args, original_data, final_data):
        self.args = args
        self.original_data = original_data
        self.final_data = final_data
        self.n_label = args.n_label
        self.upper = args.upper
        self.lower = args.lower
        self.xy_down_scale = args.xy_down_scale
        self.z_down_scale = args.z_down_scale
        self.expand_slice = args.expand_slice
        self.min_slice = args.min_slice
        self.valid_rate = args.valid_rate

    def integrate_data(self):
        # 创建目录结构
        if not os.path.exists(self.final_data):
            os.makedirs(join(self.final_data, 'ct'))
            os.makedirs(join(self.final_data, 'label'))
        # 获取文件列表并统计样本数
        file_list = os.listdir(join(self.original_data, 'ct'))
        num = len(file_list)
        print('The total number of samples is:', num)
        # 循环每一个CT及其对应标签图像
        for ct_file, i in zip(file_list, range(num)):
            print("========== {} | {}/{} ==========".format(ct_file, i + 1, num))
            ct_path = os.path.join(self.original_data, 'ct', ct_file)
            seg_path = os.path.join(self.original_data, 'label', ct_file.replace('volume', 'segmentation'))
            # 处理每个CT图像
            new_ct, new_seg = self.process(ct_path, seg_path, self.n_label)
            # 保存处理后的数据
            if new_ct is not None and new_seg is not None:
                sitk.WriteImage(new_ct, os.path.join(self.final_data, 'ct', str(ct_file)))
                sitk.WriteImage(new_seg, os.path.join(self.final_data, 'label',
                                                      str(ct_file.replace('volume', 'segmentation').replace('.nii',
                                                                                                            '.nii.gz'))))

    def process(self, ct_path, seg_path, n_label):
        # 读取CT图像和标签图像并转化为numpy数组
        ct = sitk.ReadImage(ct_path, sitk.sitkInt16)
        ct_array = sitk.GetArrayFromImage(ct)
        seg = sitk.ReadImage(seg_path, sitk.sitkInt8)
        seg_array = sitk.GetArrayFromImage(seg)
        print("Original shape:", ct_array.shape, seg_array.shape)
        # 合并标签
        if n_label == 2:
            seg_array[seg_array > 0] = 1
        # 图像灰度值阈值处理
        ct_array[ct_array > self.upper] = self.upper
        ct_array[ct_array < self.lower] = self.lower
        # 图像降采样
        ct_array = ndimage.zoom(ct_array, (ct.GetSpacing()[-1] / self.z_down_scale,
                                           self.xy_down_scale, self.xy_down_scale), order=3)
        seg_array = ndimage.zoom(seg_array, (ct.GetSpacing()[-1] / self.z_down_scale,
                                             self.xy_down_scale, self.xy_down_scale), order=0)
        # 提取切片区域
        z = np.any(seg_array, axis=(1, 2))
        start_slice, end_slice = np.where(z)[0][[0, -1]]
        # 扩展切片区域
        if start_slice - self.expand_slice < 0:
            start_slice = 0
        else:
            start_slice -= self.expand_slice
        if end_slice + self.expand_slice >= seg_array.shape[0]:
            end_slice = seg_array.shape[0] - 1
        else:
            end_slice += self.expand_slice
        # 检查是否有足够的切片
        slice_count = end_slice - start_slice + 1
        if slice_count < self.min_slice:
            print(f"Sample {ct_path} is skipped due to insufficient slices: {slice_count}")
            return None, None
        # 裁剪并调整图像大小
        ct_array = ct_array[start_slice:end_slice + 1, :, :]
        seg_array = seg_array[start_slice:end_slice + 1, :, :]
        print("Preprocessed shape:", ct_array.shape, seg_array.shape)
        # 将处理后的数据转换回SimpleITK图像，保持空间大小不变
        new_ct = sitk.GetImageFromArray(ct_array)
        new_ct.SetDirection(ct.GetDirection())
        new_ct.SetOrigin(ct.GetOrigin())
        new_ct.SetSpacing((ct.GetSpacing()[0] * int(1 / self.xy_down_scale),
                           ct.GetSpacing()[1] * int(1 / self.xy_down_scale), self.z_down_scale))
        new_seg = sitk.GetImageFromArray(seg_array)
        new_seg.SetDirection(ct.GetDirection())
        new_seg.SetOrigin(ct.GetOrigin())
        new_seg.SetSpacing((ct.GetSpacing()[0] * int(1 / self.xy_down_scale),
                            ct.GetSpacing()[1] * int(1 / self.xy_down_scale), self.z_down_scale))
        return new_ct, new_seg

    def divide_data(self):
        # 获取数据文件名列表
        data_name = os.listdir(join(self.final_data, "ct"))
        data_num = len(data_name)
        print('The total number of samples processed is:', data_num)
        # 随机打乱文件名列表
        random.shuffle(data_name)
        # 切分训练集和验证集
        assert self.valid_rate < 1.0
        train_name_list = data_name[0:int(data_num * (1 - self.valid_rate))]
        val_name_list = data_name[int(data_num * (1 - self.valid_rate)):
                                  int(data_num * ((1 - self.valid_rate) + self.valid_rate))]
        # 保存训练集和验证集文件名列表
        self.write(train_name_list, "train_path.txt")
        self.write(val_name_list, "val_path.txt")

    def write(self, name_list, file_name):
        f = open(join(self.final_data, file_name), 'w')
        # 遍历文件名列表并生成路径
        for name in name_list:
            ct_path = os.path.join(self.final_data, 'ct', name)
            seg_path = os.path.join(self.final_data, 'label', str(name.replace('volume', 'segmentation')))
            f.write(ct_path + ' ' + seg_path + "\n")
        f.close()


if __name__ == '__main__':
    args = config.args
    work = DataPreprocess(args, args.original_data, args.final_data)
    # 处理并保存原始数据集
    work.integrate_data()
    # 分离并写入训练集和验证集
    work.divide_data()