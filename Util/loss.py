import torch


class TverskyLoss(torch.nn.Module):
    """
    Tversky 损失函数，常用于类别不平衡的分割任务。
    参数：
        alpha: 假阳性的权重。
        beta: 假阴性的权重。
    输入：
        pred: 模型的预测输出，各类别的概率值。
        target: 目标标签，one-hot 编码格式，与 pred 形状一致。
    返回：
        Tversky 损失值。
    """
    def __init__(self, alpha, beta):
        super(TverskyLoss, self).__init__()
        self.alpha = alpha
        self.beta = beta

    def forward(self, pred, target):
        dice = 0
        # 遍历每个类别
        for i in range(pred.size(1)):
            # 计算每个类别的 Tversky
            dice += (pred[:, i] * target[:, i]).sum(dim=1).sum(dim=1).sum(dim=1) / (
                    (pred[:, i] * target[:, i]).sum(dim=1).sum(dim=1).sum(dim=1) +
                    self.alpha * (pred[:, i] * (1 - target[:, i])).sum(dim=1).sum(dim=1).sum(dim=1) +
                    self.beta * ((1 - pred[:, i]) * target[:, i]).sum(dim=1).sum(dim=1).sum(dim=1) +
                    0.0001)
        dice = dice / pred.size(1)
        # 返回损失值
        return torch.clamp((1 - dice).mean(), 0, 2)