import config
import os
import SimpleITK as sitk


class Expand:
    def __init__(self, ct_path, label_path):
        self.ct_path = ct_path
        self.label_path = label_path

    def histogram_equalization(self):
        for i in range(131):
            # 构建文件路径
            ct = f"{self.ct_path}volume-{i}.nii"
            label = f"{self.label_path}segmentation-{i}.nii"
            try:
                # 读取CT图像
                ct_image = sitk.ReadImage(ct)
                # 直方图均衡化
                sitk_hisequal = sitk.AdaptiveHistogramEqualizationImageFilter()
                sitk_hisequal.SetAlpha(0.9)
                sitk_hisequal.SetBeta(0.9)
                sitk_hisequal.SetRadius(3)
                ct_image_eq = sitk_hisequal.Execute(ct_image)
                # 保存处理后的CT图像
                new_ct_filename = f"{self.ct_path}volume-{i + 131}.nii"
                sitk.WriteImage(ct_image_eq, new_ct_filename)
                # 读取标签图像（标签保持不变）
                label_image = sitk.ReadImage(label)
                # 保存标签图像
                new_label_filename = f"{self.label_path}segmentation-{i + 131}.nii"
                sitk.WriteImage(label_image, new_label_filename)
                # 打印进度信息
                print(f"Processing volume-{i}... done")
            except Exception as e:
                print(f"Error processing {ct}: {e}")
        print("All CT files have been histogram equalized.")

    def laplace_sharpen(self):
        for i in range(131):
            # 构建文件路径
            ct = f"{self.ct_path}volume-{i}.nii"
            label = f"{self.label_path}segmentation-{i}.nii"
            try:
                # 读取CT图像
                ct_image = sitk.ReadImage(ct)
                # 拉普拉斯锐化
                sitk_laplaciansharp = sitk.LaplacianSharpeningImageFilter()
                sitk_laplaciansharp.UseImageSpacingOn()
                ct_image_sharp = sitk_laplaciansharp.Execute(ct_image)
                # 保存处理后的CT图像
                new_ct_filename = f"{self.ct_path}volume-{i + 262}.nii"
                sitk.WriteImage(ct_image_sharp, new_ct_filename)
                # 读取标签图像（标签保持不变）
                label_image = sitk.ReadImage(label)
                # 保存标签图像
                new_label_filename = f"{self.label_path}segmentation-{i + 262}.nii"
                sitk.WriteImage(label_image, new_label_filename)
                # 打印进度信息
                print(f"Processing volume-{i}... done")
            except Exception as e:
                print(f"Error processing {ct}: {e}")
        print("All CT files have been laplace sharpened.")


if __name__ == '__main__':
    args = config.args
    # 构建输入路径与输出路径
    ct_path = os.path.join(args.original_data, 'ct/')
    label_path = os.path.join(args.original_data, 'label/')
    # 检查CT文件和标签文件是否存在
    for i in range(131):
        ct_filename = f"{ct_path}volume-{i}.nii"
        label_filename = f"{label_path}segmentation-{i}.nii"
        if not os.path.exists(ct_filename):
            print(f"Warning: {ct_filename} not found.")
        if not os.path.exists(label_filename):
            print(f"Warning: {label_filename} not found.")
    processor = Expand(ct_path, label_path)
    # 直方图均衡化处理，保存为131-261
    processor.histogram_equalization()
    # 拉普拉斯锐化处理，保存为262-392
    processor.laplace_sharpen()