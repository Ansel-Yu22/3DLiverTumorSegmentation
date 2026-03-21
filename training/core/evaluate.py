import torch
import numpy as np


class LossAverage(object):
    def __init__(self):
        # 初始化时重置属性
        self.reset()

    def reset(self):
        # 重置计算属性
        self.val = 0
        self.avg = 0
        self.sum = 0
        self.count = 0

    def update(self, val, n):
        # 更新损失值和样本数
        self.val = val
        self.sum += val * n
        self.count += n
        self.avg = round(self.sum / self.count, 4)

class DiceAverage(object):
    def __init__(self, class_num):
        self.class_num = class_num
        # 初始化时重置属性
        self.reset()

    def reset(self):
        # 重置计算属性
        self.value = np.asarray([0]*self.class_num, dtype='float64')
        self.avg = np.asarray([0]*self.class_num, dtype='float64')
        self.sum = np.asarray([0]*self.class_num, dtype='float64')
        self.count = 0

    def update(self, logits, targets):
        # 更新 Dice 系数值
        self.value = DiceAverage.get_dices(logits, targets)
        self.sum += self.value
        self.count += 1
        self.avg = np.around(self.sum / self.count, 4)

    def get_dices(logits, targets):
        # 存储每个类别的 Dice 系数
        dices = []
        # 遍历所有类别
        for class_index in range(targets.size()[1]):
            # 计算交集：logits 和 targets 对应类别的像素值相乘并求和
            inter = torch.sum(logits[:, class_index, :, :, :] * targets[:, class_index, :, :, :])
            # 计算并集：logits 和 targets 对应类别的像素值相加并求和
            union = torch.sum(logits[:, class_index, :, :, :]) + torch.sum(targets[:, class_index, :, :, :])
            # 计算 Dice 系数
            dice = (2. * inter) / (union + 0.0001)
            # 将当前类别的 Dice 系数添加到列表中
            dices.append(dice.item())
        # 返回所有类别的 Dice 系数
        return np.asarray(dices)

class MetricsCalculator(object):
    def __init__(self, class_num):
        self.class_num = class_num
        self.reset()

    def reset(self):
        self.dice_sum = np.asarray([0] * self.class_num, dtype='float64')
        self.iou_sum = np.asarray([0] * self.class_num, dtype='float64')
        self.sensitivity_sum = np.asarray([0] * self.class_num, dtype='float64')
        self.precision_sum = np.asarray([0] * self.class_num, dtype='float64')
        self.count = 0

    def update(self, logits, targets):
        dice, iou, sensitivity, precision = self.get_metrics(logits, targets)
        self.dice_sum += dice
        self.iou_sum += iou
        self.sensitivity_sum += sensitivity
        self.precision_sum += precision
        self.count += 1

    def get_averages(self):
        dice_avg = np.around(self.dice_sum / self.count, 4)
        iou_avg = np.around(self.iou_sum / self.count, 4)
        sensitivity_avg = np.around(self.sensitivity_sum / self.count, 4)
        precision_avg = np.around(self.precision_sum / self.count, 4)
        return dice_avg, iou_avg, sensitivity_avg, precision_avg

    def get_metrics(self, logits, targets):
        dices = []
        ious = []
        sensitivities = []
        precisions = []
        for class_index in range(targets.size()[1]):
            inter = torch.sum(logits[:, class_index, :, :, :] * targets[:, class_index, :, :, :])
            union = torch.sum(logits[:, class_index, :, :, :]) + torch.sum(targets[:, class_index, :, :, :])
            dice = (2. * inter) / (union + 0.0001)
            iou = inter / (union - inter + 0.0001)
            tp = inter
            fp = torch.sum(logits[:, class_index, :, :, :]) - inter
            fn = torch.sum(targets[:, class_index, :, :, :]) - inter
            sensitivity = tp / (tp + fn + 0.0001)
            precision = tp / (tp + fp + 0.0001)
            dices.append(dice.item())
            ious.append(iou.item())
            sensitivities.append(sensitivity.item())
            precisions.append(precision.item())
        return np.asarray(dices), np.asarray(ious), np.asarray(sensitivities), np.asarray(precisions)