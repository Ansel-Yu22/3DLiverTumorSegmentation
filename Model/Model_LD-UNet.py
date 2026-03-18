import torch
import torch.nn as nn
import torch.nn.functional as fun


def generate_laplacian_pyramid(inputs, num_levels=5):
    """
    生成拉普拉斯金字塔
    参数：
    - inputs: 输入张量，形状为(B, C, D, H, W)，即批大小、通道数、深度、高度、宽度。
    - num_levels: 金字塔层数。
    返回：
    - laplacian_pyramid: 拉普拉斯金字塔列表。
    """
    # 初始化高斯金字塔，将输入作为第一层
    gaussian_pyramid = [inputs]
    for i in range(num_levels - 1):
        # 使用平均池化进行下采样
        smoothed = fun.avg_pool3d(gaussian_pyramid[-1], kernel_size=2, stride=2)
        gaussian_pyramid.append(smoothed)
    # 初始化空的拉普拉斯金字塔列表
    laplacian_pyramid = []
    for i in range(num_levels - 1):
        # 对低分辨率图像进行上采样
        upsampled = fun.interpolate(gaussian_pyramid[i + 1], scale_factor=2, mode='trilinear', align_corners=False)
        # 计算差值（细节层）
        diff = gaussian_pyramid[i] - upsampled
        laplacian_pyramid.append(diff)
    # 将最低分辨率的高斯层直接加入拉普拉斯金字塔
    laplacian_pyramid.append(gaussian_pyramid[-1])
    return laplacian_pyramid


class UNet(nn.Module):
    def __init__(self, in_channel, out_channel, drop_rate, training):
        """
        初始化集成了拉普拉斯金字塔的UNet模型。
        in_channel: 输入通道数
        out_channel: 输出通道数
        drop_rate: 丢弃率
        training: 是否在训练模式（启用丢弃）
        """
        super().__init__()
        self.drop_rate = drop_rate
        self.training = training

        # ---------------------- 编码器部分 ---------------------- #
        # 定义编码器阶段1，与拉普拉斯金字塔的L_0层连接
        self.encoder_stage1 = nn.Sequential(
            nn.Conv3d(in_channel + in_channel, 32, kernel_size=3, stride=1, padding=1),
            nn.InstanceNorm3d(32),
            nn.PReLU(32),

            nn.Conv3d(32, 32, kernel_size=3, stride=1, padding=1),
            nn.InstanceNorm3d(32),
            nn.PReLU(32),

            nn.Conv3d(32, 32, kernel_size=3, stride=1, padding=1),
            nn.InstanceNorm3d(32),
            nn.PReLU(32),
        )

        # 定义编码器阶段2，与拉普拉斯金字塔的L_1层连接
        self.encoder_stage2 = nn.Sequential(
            nn.Conv3d(64 + in_channel, 64, kernel_size=3, stride=1, padding=1),
            nn.InstanceNorm3d(64),
            nn.PReLU(64),

            nn.Conv3d(64, 64, kernel_size=3, stride=1, padding=1),
            nn.InstanceNorm3d(64),
            nn.PReLU(64),

            nn.Conv3d(64, 64, kernel_size=3, stride=1, padding=1),
            nn.InstanceNorm3d(64),
            nn.PReLU(64),
        )

        # 定义编码器阶段3，与拉普拉斯金字塔的L_2层连接
        self.encoder_stage3 = nn.Sequential(
            nn.Conv3d(128 + in_channel, 128, kernel_size=3, stride=1, padding=2, dilation=2),
            nn.InstanceNorm3d(128),
            nn.PReLU(128),

            nn.Conv3d(128, 128, kernel_size=3, stride=1, padding=2, dilation=2),
            nn.InstanceNorm3d(128),
            nn.PReLU(128),

            nn.Conv3d(128, 128, kernel_size=3, stride=1, padding=2, dilation=2),
            nn.InstanceNorm3d(128),
            nn.PReLU(128),
        )

        # 定义编码器阶段4，与拉普拉斯金字塔的L_3层连接
        self.encoder_stage4 = nn.Sequential(
            nn.Conv3d(256 + in_channel, 256, kernel_size=3, stride=1, padding=3, dilation=3),
            nn.InstanceNorm3d(256),
            nn.PReLU(256),

            nn.Conv3d(256, 256, kernel_size=3, stride=1, padding=3, dilation=3),
            nn.InstanceNorm3d(256),
            nn.PReLU(256),

            nn.Conv3d(256, 256, kernel_size=3, stride=1, padding=3, dilation=3),
            nn.InstanceNorm3d(256),
            nn.PReLU(256),
        )

        # 定义编码器阶段5，与拉普拉斯金字塔的L_4层连接
        self.encoder_stage5 = nn.Sequential(
            nn.Conv3d(512 + in_channel, 512, kernel_size=3, stride=1, padding=4, dilation=4),
            nn.InstanceNorm3d(512),
            nn.PReLU(512),

            nn.Conv3d(512, 512, kernel_size=3, stride=1, padding=4, dilation=4),
            nn.InstanceNorm3d(512),
            nn.PReLU(512),
        )

        # ---------------------- 解码器部分 ---------------------- #
        # 定义解码器阶段1，处理编码器阶段5的输出
        self.decoder_stage1 = nn.Sequential(
            nn.Conv3d(512, 512, kernel_size=3, stride=1, padding=4, dilation=4),
            nn.InstanceNorm3d(512),
            nn.PReLU(512),

            nn.Conv3d(512, 512, kernel_size=3, stride=1, padding=4, dilation=4),
            nn.InstanceNorm3d(512),
            nn.PReLU(512),
        )

        # 定义解码器阶段2，融合上采样和编码器阶段4的特征
        self.decoder_stage2 = nn.Sequential(
            nn.Conv3d(256 + 256, 256, kernel_size=3, stride=1, padding=1),
            nn.InstanceNorm3d(256),
            nn.PReLU(256),

            nn.Conv3d(256, 256, kernel_size=3, stride=1, padding=1),
            nn.InstanceNorm3d(256),
            nn.PReLU(256),

            nn.Conv3d(256, 256, kernel_size=3, stride=1, padding=1),
            nn.InstanceNorm3d(256),
            nn.PReLU(256),
        )

        # 定义解码器阶段3，融合上采样和编码器阶段3的特征
        self.decoder_stage3 = nn.Sequential(
            nn.Conv3d(128 + 128, 128, kernel_size=3, stride=1, padding=1),
            nn.InstanceNorm3d(128),
            nn.PReLU(128),

            nn.Conv3d(128, 128, kernel_size=3, stride=1, padding=1),
            nn.InstanceNorm3d(128),
            nn.PReLU(128),

            nn.Conv3d(128, 128, kernel_size=3, stride=1, padding=1),
            nn.InstanceNorm3d(128),
            nn.PReLU(128),
        )

        # 定义解码器阶段4，融合上采样和编码器阶段2的特征
        self.decoder_stage4 = nn.Sequential(
            nn.Conv3d(64 + 64, 64, kernel_size=3, stride=1, padding=1),
            nn.InstanceNorm3d(64),
            nn.PReLU(64),

            nn.Conv3d(64, 64, kernel_size=3, stride=1, padding=1),
            nn.InstanceNorm3d(64),
            nn.PReLU(64),

            nn.Conv3d(64, 64, kernel_size=3, stride=1, padding=1),
            nn.InstanceNorm3d(64),
            nn.PReLU(64),
        )

        # 定义解码器阶段5，融合上采样和编码器阶段1的特征
        self.decoder_stage5 = nn.Sequential(
            nn.Conv3d(32 + 32, 32, kernel_size=3, stride=1, padding=1),
            nn.InstanceNorm3d(32),
            nn.PReLU(32),

            nn.Conv3d(32, 32, kernel_size=3, stride=1, padding=1),
            nn.InstanceNorm3d(32),
            nn.PReLU(32),

            nn.Conv3d(32, 32, kernel_size=3, stride=1, padding=1),
            nn.InstanceNorm3d(32),
            nn.PReLU(32),
        )

        # ---------------------- 下采样操作 ---------------------- #
        # 定义下采样层1，从32通道到64通道
        self.down_conv1 = nn.Sequential(
            nn.Conv3d(32, 64, kernel_size=2, stride=2),
            nn.InstanceNorm3d(64),
            nn.PReLU(64)
        )

        # 定义下采样层2，从64通道到128通道
        self.down_conv2 = nn.Sequential(
            nn.Conv3d(64, 128, kernel_size=2, stride=2),
            nn.InstanceNorm3d(128),
            nn.PReLU(128)
        )

        # 定义下采样层3，从128通道到256通道
        self.down_conv3 = nn.Sequential(
            nn.Conv3d(128, 256, kernel_size=2, stride=2),
            nn.InstanceNorm3d(256),
            nn.PReLU(256)
        )

        # 定义下采样层4，从256通道到512通道
        self.down_conv4 = nn.Sequential(
            nn.Conv3d(256, 512, kernel_size=2, stride=2),
            nn.InstanceNorm3d(512),
            nn.PReLU(512)
        )

        # ---------------------- 上采样操作 ---------------------- #
        # 定义上采样层1，从512通道到256通道
        self.up_conv1 = nn.Sequential(
            nn.ConvTranspose3d(512, 256, kernel_size=2, stride=2),
            nn.InstanceNorm3d(256),
            nn.PReLU(256)
        )

        # 定义上采样层2，从256通道到128通道
        self.up_conv2 = nn.Sequential(
            nn.ConvTranspose3d(256, 128, kernel_size=2, stride=2),
            nn.InstanceNorm3d(128),
            nn.PReLU(128)
        )

        # 定义上采样层3，从128通道到64通道
        self.up_conv3 = nn.Sequential(
            nn.ConvTranspose3d(128, 64, kernel_size=2, stride=2),
            nn.InstanceNorm3d(64),
            nn.PReLU(64)
        )

        # 定义上采样层4，从64通道到32通道
        self.up_conv4 = nn.Sequential(
            nn.ConvTranspose3d(64, 32, kernel_size=2, stride=2),
            nn.InstanceNorm3d(32),
            nn.PReLU(32)
        )

        # ---------------------- 多尺度映射层 ---------------------- #
        # 定义多尺度映射层1，从512通道映射到输出通道
        self.map1 = nn.Sequential(
            nn.Conv3d(512, out_channel, kernel_size=1, stride=1),
            nn.Upsample(scale_factor=16, mode='trilinear', align_corners=False),
            nn.Softmax(dim=1)
        )

        # 定义多尺度映射层2，从256通道映射到输出通道
        self.map2 = nn.Sequential(
            nn.Conv3d(256, out_channel, kernel_size=1, stride=1),
            nn.Upsample(scale_factor=8, mode='trilinear', align_corners=False),
            nn.Softmax(dim=1)
        )

        # 定义多尺度映射层3，从128通道映射到输出通道
        self.map3 = nn.Sequential(
            nn.Conv3d(128, out_channel, kernel_size=1, stride=1),
            nn.Upsample(scale_factor=4, mode='trilinear', align_corners=False),
            nn.Softmax(dim=1)
        )

        # 定义多尺度映射层4，从64通道映射到输出通道
        self.map4 = nn.Sequential(
            nn.Conv3d(64, out_channel, kernel_size=1, stride=1),
            nn.Upsample(scale_factor=2, mode='trilinear', align_corners=False),
            nn.Softmax(dim=1)
        )

        # 定义多尺度映射层5，从32通道映射到输出通道
        self.map5 = nn.Sequential(
            nn.Conv3d(32, out_channel, kernel_size=1, stride=1),
            nn.Upsample(scale_factor=1, mode='trilinear', align_corners=False),
            nn.Softmax(dim=1)
        )

    # 定义前向传播方法
    def forward(self, inputs):
        """
        集成了拉普拉斯金字塔的前向传播。
        inputs: 形状为[batch, in_channel, depth, height, width]的3D图像数据
        在训练模式下返回多个尺度的输出，在推理模式下返回最终输出。
        """
        # 生成包含5层的拉普拉斯金字塔
        laplacian_pyramid = generate_laplacian_pyramid(inputs, num_levels=5)
        L_0, L_1, L_2, L_3, L_4 = laplacian_pyramid

        # ------------- 编码器前向传播 ------------- #
        # 将输入与L_0沿通道维度拼接
        inputs_with_L0 = torch.cat([inputs, L_0], dim=1)
        long_range1 = self.encoder_stage1(inputs_with_L0)
        # 下采样到下一阶段
        short_range1 = self.down_conv1(long_range1)

        # 将短距离特征与L_1沿通道维度拼接
        short_range1_with_L1 = torch.cat([short_range1, L_1], dim=1)
        long_range2 = self.encoder_stage2(short_range1_with_L1)
        long_range2 = fun.dropout(long_range2, self.drop_rate, self.training)
        # 下采样到下一阶段
        short_range2 = self.down_conv2(long_range2)

        # 将短距离特征与L_2沿通道维度拼接
        short_range2_with_L2 = torch.cat([short_range2, L_2], dim=1)
        long_range3 = self.encoder_stage3(short_range2_with_L2)
        long_range3 = fun.dropout(long_range3, self.drop_rate, self.training)
        # 下采样到下一阶段
        short_range3 = self.down_conv3(long_range3)

        # 将短距离特征与L_3沿通道维度拼接
        short_range3_with_L3 = torch.cat([short_range3, L_3], dim=1)
        long_range4 = self.encoder_stage4(short_range3_with_L3)
        long_range4 = fun.dropout(long_range4, self.drop_rate, self.training)
        # 下采样到下一阶段
        short_range4 = self.down_conv4(long_range4)

        # 将短距离特征与L_4沿通道维度拼接
        short_range4_with_L4 = torch.cat([short_range4, L_4], dim=1)
        long_range5 = self.encoder_stage5(short_range4_with_L4)
        long_range5 = fun.dropout(long_range5, self.drop_rate, self.training)

        # ------------- 解码器前向传播 ------------- #
        # 通过解码器阶段1处理编码器输出
        outputs = self.decoder_stage1(long_range5)
        outputs = fun.dropout(outputs, self.drop_rate, self.training)
        output1 = self.map1(outputs)
        # 上采样到下一阶段
        short_range6 = self.up_conv1(outputs)

        # 将上采样结果与编码器阶段4的特征拼接
        outputs = self.decoder_stage2(torch.cat([short_range6, long_range4], dim=1))
        outputs = fun.dropout(outputs, self.drop_rate, self.training)
        output2 = self.map2(outputs)
        # 上采样到下一阶段
        short_range7 = self.up_conv2(outputs)

        # 将上采样结果与编码器阶段3的特征拼接
        outputs = self.decoder_stage3(torch.cat([short_range7, long_range3], dim=1))
        outputs = fun.dropout(outputs, self.drop_rate, self.training)
        output3 = self.map3(outputs)
        # 上采样到下一阶段
        short_range8 = self.up_conv3(outputs)

        # 将上采样结果与编码器阶段2的特征拼接
        outputs = self.decoder_stage4(torch.cat([short_range8, long_range2], dim=1))
        outputs = fun.dropout(outputs, self.drop_rate, self.training)
        output4 = self.map4(outputs)
        # 上采样到下一阶段
        short_range9 = self.up_conv4(outputs)

        # 将上采样结果与编码器阶段1的特征拼接
        outputs = self.decoder_stage5(torch.cat([short_range9, long_range1], dim=1))
        output5 = self.map5(outputs)

        # 根据训练模式返回相应的输出
        if self.training:
            # 训练模式下返回所有多尺度输出
            return output1, output2, output3, output4, output5
        else:
            # 推理模式下仅返回最终输出
            return output5