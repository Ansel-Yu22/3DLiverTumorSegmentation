import argparse


# 创建一个用于管理超参数的命令行参数解析器
parser = argparse.ArgumentParser(description='Hyper-parameters management')

# 数据处理
parser.add_argument('--original_data', default='/root/autodl-tmp/original_data', help='train dataset path')
parser.add_argument('--final_data', default='/root/autodl-tmp/final_data', help='final dataset path')
parser.add_argument('--n_label', type=int, default=3, help='2 for liver, 3 for liver and tumor')
parser.add_argument('--upper', type=int, default=300, help='gray value upper limit')
parser.add_argument('--lower', type=int, default=-100, help='gray value lower limit')
parser.add_argument('--xy_down_scale', type=float, default=0.5, help='x and y axis downsample scaling factor')
parser.add_argument('--z_down_scale', type=float, default=1.0, help='z axis downsample scaling factor')
parser.add_argument('--expand_slice', type=int, default=4, help='slice expansion number')
parser.add_argument('--min_slice', type=int, default=80, help='minimum slice number')
parser.add_argument('--valid_rate', type=float, default=0.2, help='validation dataset ratio')
parser.add_argument('--rc_size', type=int, default=80, help='random crop size')
parser.add_argument('--prob', type=float, default=0.5, help='probability of occurrence')
parser.add_argument('--cc_size', type=int, default=160, help='center crop size')
parser.add_argument('--tc_size', type=int, default=80, help='size of sliding window')
parser.add_argument('--tc_stride', type=int, default=20, help='stride of sliding window')

# 训练测试
parser.add_argument('--model_save', default='./model/checkpoint', help='save path of trained model')
parser.add_argument('--cpu', action='store_true', help='use cpu only')
parser.add_argument('--batch_size', type=int, default=1, help='batch size of train dataset')
parser.add_argument('--n_thread', type=int, default=16, help='number of threads for data loading')
parser.add_argument('--drop_rate', type=float, default=0.3, help='dropout ratio')
parser.add_argument('--lr', type=float, default=0.00005, help='learning rate')
parser.add_argument('--alpha', type=float, default=0.3, help='false positive weight')
parser.add_argument('--beta', type=float, default=0.7, help='false negative weight')
parser.add_argument('--log_save', default='./doc', help='save path of log')
parser.add_argument('--ds_weight', type=float, default=0.4, help='deep supervision initial coefficient')
parser.add_argument('--lr_dp', type=int, default=20, help='learning rate decay period')
parser.add_argument('--lr_dc', type=float, default=0.8, help='learning rate decay coefficient')
parser.add_argument('--epoch', type=int, default=1000, help='number of epochs to train')
parser.add_argument('--ds_dp', type=int, default=20, help='deep supervision decay period')
parser.add_argument('--ds_dc', type=float, default=0.8, help='deep supervision decay coefficient')
parser.add_argument('--early_stop', default=100, type=int, help='early stop number')
parser.add_argument('--test_path',default = '/root/autodl-tmp/original_data/test',help='test dataset path')

# 解析从命令行传递的参数并将结果存储在args中
args = parser.parse_args()
