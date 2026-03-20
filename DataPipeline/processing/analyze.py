import config
import os
import re
import numpy as np
import SimpleITK as sitk


def process(ct_file, seg_file, args):
    # 检查文件是否存在
    if not os.path.exists(ct_file):
        print(f"Error: CT file {ct_file} does not exist.")
        return 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
    if not os.path.exists(seg_file):
        print(f"Error: Segmentation file {seg_file} does not exist.")
        return 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
    try:
        # 读取CT图像和分割图像
        ct = sitk.ReadImage(ct_file, sitk.sitkInt16)
        ct_array = sitk.GetArrayFromImage(ct)
        seg = sitk.ReadImage(seg_file, sitk.sitkUInt8)
        seg_array = sitk.GetArrayFromImage(seg)
    except Exception as e:
        print(f"Error reading image files: {ct_file} or {seg_file}. Error: {e}")
        return 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
    # 提取肝脏区域（标签为1）和肿瘤区域（标签为2）
    liver_roi = ct_array[seg_array == 1]
    tumor_roi = ct_array[seg_array == 2]
    # 计算符合条件的像素点
    liver_roi_size, liver_inliers = compute_ratios(liver_roi, args.lower, args.upper)
    tumor_roi_size, tumor_inliers = compute_ratios(tumor_roi, args.lower, args.upper)
    # 统计没有肝脏的切片数量
    no_liver_slices = np.sum([np.sum(slice == 1) == 0 for slice in seg_array])
    # 统计没有肿瘤的切片数量
    no_tumor_slices = np.sum([np.sum(slice == 2) == 0 for slice in seg_array])
    # 获取肝脏和肿瘤切片数
    liver_slices = count_slices(seg_array, 1)
    tumor_slices = count_slices(seg_array, 2)
    # 获取总切片数
    total_slices = seg_array.shape[0]
    # 获取CT图像的大小 (width, height, depth)
    ct_size = ct.GetSize()
    return (liver_roi_size, liver_inliers, tumor_roi_size, tumor_inliers,
            no_liver_slices, no_tumor_slices, liver_slices, tumor_slices, total_slices, ct_size)

def compute_ratios(region, lower, upper):
    """
    计算符合条件的像素点数量和总像素点数量
    """
    inliers = np.sum((region < upper) & (region > lower))
    return region.size, inliers

def count_slices(seg_array, label_value):
    """
    统计含有指定标签的切片数量
    """
    return np.sum([np.sum(slice == label_value) > 0 for slice in seg_array])


if __name__ == '__main__':
    args = config.args
    # 构建路径
    ct_path = os.path.join(args.original_data, 'ct/')
    label_path = os.path.join(args.original_data, 'label/')
    # 获取CT图像和分割图像文件列表
    ct_images = [f for f in os.listdir(ct_path) if f.endswith('.nii')]
    seg_images = [f for f in os.listdir(label_path) if f.endswith('.nii')]
    # 从文件名中提取相同的标识符 ，并构建字典实现一一对应
    ct_image_dict = {f.split('-')[1]: f for f in ct_images}
    seg_image_dict = {f.split('-')[1]: f for f in seg_images}
    # 提取CT和分割图像中共有的标识符，并排序后依次处理（递增输出）
    common_keys = set(ct_image_dict.keys()).intersection(seg_image_dict.keys())
    # 通过正则表达式提取数字部分并进行排序
    sorted_keys = sorted(common_keys, key=lambda x: int(re.search(r'\d+', x).group()))
    total_ct_images = len(sorted_keys)
    # 数据初始化
    num_point = 0.0
    num_inlier_liver = 0.0
    num_inlier_tumor = 0.0
    total_no_liver_ct = 0
    total_no_tumor_ct = 0
    total_liver_slices = 0
    total_tumor_slices = 0
    total_total_slices = 0
    # 用于计算Liver Ratio和Tumor Ratio的平均值
    liver_ratios = []
    tumor_ratios = []
    for i, key in enumerate(sorted_keys, start=1):
        # 去除文件名后缀（.nii）
        volume_name = os.path.splitext(ct_image_dict[key])[0]
        ct_file = os.path.join(ct_path, ct_image_dict[key])
        label_file = os.path.join(label_path, seg_image_dict[key])
        # 处理每个图像
        (liver_roi_size, liver_inliers, tumor_roi_size, tumor_inliers,
         no_liver_slices, no_tumor_slices, liver_slices, tumor_slices,
         total_slices, ct_size) = process(ct_file, label_file, args)
        if liver_roi_size == 0 and tumor_roi_size == 0:
            print(f"========== {volume_name} ==========")
            print("No liver or tumor region detected.")
            continue
        # 计算当前CT体积的肝脏和肿瘤比例
        liver_ratio = liver_inliers / liver_roi_size * 100 if liver_roi_size > 0 else 0
        tumor_ratio = tumor_inliers / tumor_roi_size * 100 if tumor_roi_size > 0 else 0
        print(f"========== {volume_name} ==========")
        print(f"Liver Ratio: {liver_ratio:.4f}%")
        print(f"Tumor Ratio: {tumor_ratio:.4f}%")
        print(f"No Liver Slices: {no_liver_slices}")
        print(f"No Tumor Slices: {no_tumor_slices}")
        print(f"CT Size: {ct_size}")
        # 累加各项统计数据
        num_point += liver_roi_size + tumor_roi_size
        num_inlier_liver += liver_inliers
        num_inlier_tumor += tumor_inliers
        if liver_roi_size == 0:
            total_no_liver_ct += 1
        if tumor_roi_size == 0:
            total_no_tumor_ct += 1
        total_liver_slices += liver_slices
        total_tumor_slices += tumor_slices
        total_total_slices += total_slices
        if liver_ratio > 0:
            liver_ratios.append(liver_ratio)
        if tumor_ratio > 0:
            tumor_ratios.append(tumor_ratio)
    # 计算各比例的平均值（仅考虑大于0的情况）
    overall_liver_ratio = np.mean(liver_ratios) if liver_ratios else 0
    overall_tumor_ratio = np.mean(tumor_ratios) if tumor_ratios else 0
    # 输出总体结果
    print(f'\nOverall Liver Inlier Ratio: {overall_liver_ratio:.4f}%')
    print(f'Overall Tumor Inlier Ratio: {overall_tumor_ratio:.4f}%')
    no_liver_ct_ratio = (total_no_liver_ct / total_ct_images) * 100 if total_ct_images > 0 else 0
    no_tumor_ct_ratio = (total_no_tumor_ct / total_ct_images) * 100 if total_ct_images > 0 else 0
    print(f'Total number of CTs without liver: {total_no_liver_ct} ({no_liver_ct_ratio:.4f}%)')
    print(f'Total number of CTs without tumor: {total_no_tumor_ct} ({no_tumor_ct_ratio:.4f}%)')
    liver_slice_ratio = total_liver_slices / total_total_slices * 100 if total_total_slices > 0 else 0
    tumor_slice_ratio = total_tumor_slices / total_total_slices * 100 if total_total_slices > 0 else 0
    print(f'Overall Liver Slice Ratio: {liver_slice_ratio:.4f}%')
    print(f'Overall Tumor Slice Ratio: {tumor_slice_ratio:.4f}%')