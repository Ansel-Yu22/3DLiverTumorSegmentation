import pandas as pd
from collections import OrderedDict
from tensorboardX import SummaryWriter


class Train_Log():
    def __init__(self, save_path, save_name):
        """
        初始化训练日志记录器
        save_path: 保存日志文件的路径
        save_name: 保存日志文件的名称
        """
        self.log = None
        self.summary = None
        self.save_path = save_path
        self.save_name = save_name

    def update(self, epoch, train_log, val_log):
        """
        更新训练日志
        epoch: 当前的 epoch
        train_log: 本轮训练的日志
        val_log: 本轮验证的日志
        """
        item = OrderedDict({'epoch': epoch})
        # 更新字典
        item.update(train_log)
        item.update(val_log)
        # 输出当前训练和验证的日志
        print("\033[0;34mTrain:\033[0m", train_log)
        print("\033[0;34mValid:\033[0m", val_log)
        # 更新 CSV 文件和 TensorBoard 日志
        self.update_csv(item)
        self.update_tensorboard(item)

    def update_csv(self, item):
        """
        更新 CSV 文件，保存训练和验证的日志信息
        item: 当前训练和验证的日志项（字典形式）
        """
        # 将字典转换为 DataFrame（每行代表一个epoch的日志）
        tmp = pd.DataFrame(item, index=[0])
        if self.log is not None:
            self.log = pd.concat([self.log, tmp], ignore_index=True)
        else:
            self.log = tmp
        self.log.to_csv('%s/%s.csv' % (self.save_path, self.save_name), index=False)

    def update_tensorboard(self, item):
        """
        更新 TensorBoard 日志
        item: 当前训练和验证的日志项（字典形式）
        """
        if self.summary is None:
            self.summary = SummaryWriter('%s/' % self.save_path)
        epoch = item['epoch']
        for key, value in item.items():
            if key != 'epoch':
                self.summary.add_scalar(key, value, epoch)

class Test_Log():
    def __init__(self, save_path, save_name):
        self.log = None
        self.save_path = save_path
        self.save_name = save_name

    def update(self, name, log):
        item = OrderedDict({'CT': name})
        item.update(log)
        print("\033[0;34mTest:\033[0m", log)
        self.update_csv(item)

    def update_csv(self, item):
        tmp = pd.DataFrame(item, index=[0])
        if self.log is not None:
            self.log = pd.concat([self.log, tmp], ignore_index=True)
        else:
            self.log = tmp
        self.log.to_csv('%s/%s.csv' % (self.save_path, self.save_name), index=False)