import config
from Model.Model import UNet
from Util.log import Train_Log
from Util.loss import TverskyLoss
from Dataset.dataset_train import Train_Dataset, Val_Dataset
import os
import time
import torch
import Util.evaluate as el
from torch import nn
from tqdm import tqdm
from collections import OrderedDict
from torch.utils.data import DataLoader


def train(model, train_loader, loss, n_label, optimizer, ds_weight):
    print("========== Epoch:{} ========== LR:{}".format(epoch, optimizer.state_dict()['param_groups'][0]['lr']))
    # 设置模型为训练模式
    model.train()
    # 初始化训练集的平均损失和 Dice 系数
    train_loss = el.LossAverage()
    train_dice = el.DiceAverage(n_label)
    # 遍历训练集
    for idx, (data, target) in tqdm(enumerate(train_loader), total=len(train_loader)):
        # 确保数据类型正确
        data, target = data.float(), target.long()
        # 将目标标签转换为 one-hot 编码
        target = to_one_hot_3d(target, n_label)
        # 将数据和目标转移到指定设备（CPU/GPU）
        data, target = data.to(device), target.to(device)
        # 在每次训练前将梯度清零
        optimizer.zero_grad()
        # 模型预测
        output = model(data)
        # 计算每一层输出的损失（使用深监督）
        loss0 = loss(output[0], target)
        loss1 = loss(output[1], target)
        loss2 = loss(output[2], target)
        loss3 = loss(output[3], target)
        loss4 = loss(output[4], target)
        # 总损失，采用深监督的加权损失
        loss_all = loss4 + ds_weight * (loss0 + loss1 + loss2 + loss3)
        # 反向传播计算梯度
        loss_all.backward()
        # 更新模型权重
        optimizer.step()
        # 更新训练损失和 Dice 系数
        train_loss.update(loss4.item(), data.size(0))
        train_dice.update(output[4], target)
    # 返回训练日志，包含平均损失和 Dice 系数
    val_log = OrderedDict({'Train_Loss': train_loss.avg, 'Train_dice_liver': train_dice.avg[1]})
    # 如果有3个标签（包括肿瘤），则加入肿瘤的 Dice 系数
    if n_label == 3: val_log.update({'Train_dice_tumor': train_dice.avg[2]})
    return val_log

def val(model, val_loader, loss, n_label):
    # 设置模型为评估模式，禁用 Dropout 和 BatchNorm 等
    model.eval()
    # 初始化验证集的平均损失和 Dice 系数
    val_loss = el.LossAverage()
    val_dice = el.DiceAverage(n_label)
    # 在验证时不计算梯度
    with torch.no_grad():
        # 遍历验证集
        for idx, (data, target) in tqdm(enumerate(val_loader), total=len(val_loader)):
            # 确保数据类型正确
            data, target = data.float(), target.long()
            # 将目标标签转换为 one-hot 编码
            target = to_one_hot_3d(target, n_label)
            # 将数据和目标转移到指定设备（CPU/GPU）
            data, target = data.to(device), target.to(device)
            # 模型预测
            output = model(data)
            # 使用指定的损失函数计算损失
            loss_all = loss(output, target)
            # 更新验证损失和 Dice 系数
            val_loss.update(loss_all.item(), data.size(0))
            val_dice.update(output, target)
    # 返回验证结果，包含验证损失和肝脏的 Dice 系数
    val_log = OrderedDict({'Val_Loss': val_loss.avg, 'Val_dice_liver': val_dice.avg[1]})
    # 如果有3个标签（包括肿瘤），则加入肿瘤的 Dice 系数
    if n_label == 3: val_log.update({'Val_dice_tumor': val_dice.avg[2]})
    return val_log

def to_one_hot_3d(tensor, n_label):
    # 获取输入tensor的维度
    n, s, h, w = tensor.size()
    # 使用scatter_方法将tensor中的标签转换为one-hot编码
    one_hot = torch.zeros(n, n_label, s, h, w).scatter_(1, tensor.view(n, 1, s, h, w), 1)
    # 返回转换后的one-hot编码
    return one_hot


if __name__ == '__main__':
    start_time = time.time()
    args = config.args
    # 定义模型保存的路径
    save_path = args.model_save
    if not os.path.exists(save_path):
        os.mkdir(save_path)
    # 根据配置选择 CPU 或 GPU
    device = torch.device('cpu' if args.cpu else 'cuda')
    # 数据加载：定义训练和验证数据加载器
    train_loader = DataLoader(dataset=Train_Dataset(args),
                              batch_size=args.batch_size,
                              num_workers=args.n_thread,
                              shuffle=True)
    val_loader = DataLoader(dataset=Val_Dataset(args),
                            batch_size=1,
                            num_workers=args.n_thread,
                            shuffle=False)
    # 模型初始化
    model = UNet(in_channel=1, out_channel=args.n_label, drop_rate=args.drop_rate, training=True).to(device)
    # 如果是多GPU，使用DataParallel包装模型
    if torch.cuda.device_count() >= 3 and not args.cpu:
        model = nn.DataParallel(model, device_ids=[0, 1, 2]).to(device)
    elif torch.cuda.device_count() > 1 and not args.cpu:
        model = nn.DataParallel(model, device_ids=[0, 1]).to(device)
    # 使用 Kaiming 对模型进行权重初始化
    for net in model.modules():
        if isinstance(net, nn.Conv3d) or isinstance(net, nn.ConvTranspose3d):
            nn.init.kaiming_normal_(net.weight.data)
            nn.init.constant_(net.bias.data, 0)
    # 使用 Adam 优化器
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    # 打印模型结构及总参数量
    print(model)
    print(f'Total number of parameters: {sum(p.numel() for p in model.parameters())}')
    # 定义损失函数
    loss = TverskyLoss(args.alpha, args.beta)
    # 初始化训练日志记录器
    log = Train_Log(args.log_save, "train_log")
    # 初始化最佳模型的 epoch 和性能
    best = [0, 0]
    # 提前停止计数器
    trigger = 0
    # 深监督衰减系数的初始值
    ds_weight = args.ds_weight
    # 创建 ReduceLROnPlateau 调度器，初始化学习率衰减策略
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, 'min',
                                                           patience=args.lr_dp, factor=args.lr_dc)
    # 训练循环
    for epoch in range(1, args.epoch + 1):
        # 训练模型
        train_log = train(model, train_loader, loss, args.n_label, optimizer, ds_weight)
        # 验证模型
        val_log = val(model, val_loader, loss, args.n_label)
        # 更新训练和验证日志
        log.update(epoch, train_log, val_log)
        # 保存最新的模型检查点
        state = {'net': model.state_dict(),
                 'optimizer': optimizer.state_dict(),
                 'epoch': epoch}
        # 保存最新模型
        torch.save(state, os.path.join(save_path, 'latest_model.pth'))
        # 增加提前停止的计数器
        trigger += 1
        # 如果验证集上的肿瘤 Dice 系数提高，则保存最佳模型
        if val_log['Val_dice_tumor'] > best[1]:
            print('Saving best Model')
            torch.save(state, os.path.join(save_path, 'best_model.pth'))
            best[0] = epoch
            best[1] = val_log['Val_dice_tumor']
            trigger = 0
        print('Best Performance At Epoch: {} | {}'.format(best[0], best[1]))
        # 深监督衰减
        if epoch % args.ds_dp == 0:
            ds_weight *= args.ds_dc
        # 提前停止逻辑
        if args.early_stop is not None:
            if trigger >= args.early_stop:
                print("=> Early Stopping")
                break
        # 更新学习率
        scheduler.step(val_log['Val_Loss'])
        # 释放缓存内存
        torch.cuda.empty_cache()
    # 计算并输出总时间
    end_time = time.time()
    total_time = end_time - start_time
    print(f"\033[33mTotal Training Time: {round(total_time // 3600, 1)} hours "
          f"{round((total_time % 3600) // 60, 1)} minutes {round(total_time % 60, 1)} seconds\033[0m")