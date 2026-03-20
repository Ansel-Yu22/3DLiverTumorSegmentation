import torch
import random


class RandomCrop:
    def __init__(self, crop_slice):
        """
        初始化 RandomCrop 类，指定裁剪的深度范围。
        crop_slice: 裁剪的深度（crop_slice）大小。
        """
        self.crop_slice = crop_slice

    def _get_range(self, slice):
        """
        计算随机裁剪的起始和结束位置。
        slice: 图像的深度。
        返回裁剪的起始位置和结束位置。
        """
        if slice <= self.crop_slice:
            return 0, slice
        start = random.randint(0, slice - self.crop_slice)
        end = start + self.crop_slice
        return start, end

    def __call__(self, ct, label):
        """
        随机裁剪图像和标签。
        ct: 输入图像。
        label: 输入标签。
        返回裁剪后的图像和标签。
        """
        # 获取随机裁剪的起始和结束位置
        start, end = self._get_range(ct.size(1))
        # 利用切片创建裁剪后的图像和标签
        ct = ct[:, start:end, :, :]
        label = label[:, start:end, :, :]
        return ct, label

class RandomFlipLR:
    def __init__(self, prob):
        """
        初始化 RandomFlipLR 类，指定左右翻转的概率。
        """
        self.prob = prob

    def __call__(self, ct, label):
        """
        对图像和标签以给定概率进行左右翻转。
        """
        if random.random() < self.prob:
            ct = ct.flip(dims=[3])
            label = label.flip(dims=[3])
        return ct, label

class RandomFlipUD:
    def __init__(self, prob):
        """
        初始化 RandomFlipUD 类，指定上下翻转的概率。
        """
        self.prob = prob

    def __call__(self, ct, label):
        """
        对图像和标签以给定概率进行上下翻转。
        """
        if random.random() < self.prob:
            ct = ct.flip(dims=[2])
            label = label.flip(dims=[2])
        return ct, label

class RandomRotation90:
    def __init__(self, prob, axes=(2, 3)):
        """
        初始化随机90度旋转类。
        axes: 指定旋转的维度（默认沿高度和宽度旋转）。
        """
        self.prob = prob
        self.axes = axes

    def __call__(self, ct, label):
        """
        对ct和label以一定概率进行随机90度倍数旋转。
        """
        if random.random() < self.prob:
            # 随机选择1到3次旋转
            k = random.randint(1, 3)
            ct = torch.rot90(ct, k=k, dims=self.axes)
            label = torch.rot90(label, k=k, dims=self.axes)
        return ct, label

class RandomTranslation:
    def __init__(self, prob, max_translation=0.1):
        """
        初始化随机平移类。
        max_translation: 最大平移比例。
        """
        self.prob = prob
        self.max_translation = max_translation

    def __call__(self, ct, label):
        """
        对ct和label以一定概率进行随机平移操作。
        """
        if random.random() < self.prob:
            # 生成随机平移值并转换为整数像素值
            translation = (
                int(random.uniform(-self.max_translation, self.max_translation) * ct.size(2)),
                int(random.uniform(-self.max_translation, self.max_translation) * ct.size(3))
            )
            # 对图像和标签进行平移操作，保持图像尺寸不变
            ct = torch.roll(ct, shifts=(translation[0], translation[1]), dims=(2, 3))
            label = torch.roll(label, shifts=(translation[0], translation[1]), dims=(2, 3))
        return ct, label

class RandomNoise:
    def __init__(self, prob, mean=0.0, std=0.05):
        """
        初始化随机噪声注入。
        mean: 噪声均值。
        std: 噪声标准差。
        """
        self.prob = prob
        self.mean = mean
        self.std = std

    def __call__(self, ct, label):
        """
        对ct添加高斯噪声，label保持不变。
        """
        if random.random() < self.prob:
            noise = torch.randn_like(ct) * self.std + self.mean
            ct = ct + noise
            ct = torch.clamp(ct, 0, 1)
        return ct, label

class CenterCrop:
    def __init__(self, base, max_size):
        """
        初始化 CenterCrop 类，指定基础大小和最大裁剪尺寸。
        base: 基础大小，通常为16，用于保证裁剪后的图像尺寸可以被 base 整除。
        max_size: 最大裁剪尺寸，用于控制显存，确保图像裁剪不会超过最大尺寸。
        """
        self.base = base
        self.max_size = max_size
        # 保证 max_size 可以被 base 整除
        self.max_size -= self.max_size % self.base

    def __call__(self, ct, label):
        """
        从图像中心裁剪指定大小的区域。
        ct: 输入图像。
        label: 输入标签。
        返回裁剪后的图像和标签。
        """
        # 检查图像的切片数是否小于 base，若小于则不执行裁剪
        if ct.size(1) < self.base:
            return None
        # 计算可以裁剪的最大切片数（向下取整）
        slice_num = ct.size(1) - ct.size(1) % self.base
        slice_num = min(self.max_size, slice_num)
        # 计算裁剪的左右位置
        left = (ct.size(1) - slice_num) // 2
        right = left + slice_num
        # 从图像和标签中裁剪
        crop_ct = ct[:, left:right, :, :]
        crop_label = label[:, left:right, :, :]
        return crop_ct, crop_label

class Compose:
    def __init__(self, transform):
        """
        初始化 Compose 类，组合多个变换操作。
        transform: 变换操作列表。
        """
        self.transform = transform

    def __call__(self, ct, label):
        """
        对图像和标签应用一系列变换。
        ct: 输入图像。
        label: 输入标签。
        返回经过所有变换后的图像和标签。
        """
        for t in self.transform:
            ct, label = t(ct, label)
        return ct, label