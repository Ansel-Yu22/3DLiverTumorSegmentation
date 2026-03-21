import torch
import torch.nn as nn


class UNet(nn.Module):
    def __init__(self, in_channel, out_channel):
        """
        in_channel: 输入通道数
        out_channel: 输出通道数
        """
        super().__init__()

        # ---------------------- 编码器部分 ---------------------- #
        # 定义编码器阶段1
        self.encoder_stage1 = nn.Sequential(
            nn.Conv3d(in_channel, 32, kernel_size=3, stride=1, padding=1),
            nn.InstanceNorm3d(32),
            nn.PReLU(32),

            nn.Conv3d(32, 32, kernel_size=3, stride=1, padding=1),
            nn.InstanceNorm3d(32),
            nn.PReLU(32),

            nn.Conv3d(32, 32, kernel_size=3, stride=1, padding=1),
            nn.InstanceNorm3d(32),
            nn.PReLU(32),
        )

        # 定义编码器阶段2
        self.encoder_stage2 = nn.Sequential(
            nn.Conv3d(64, 64, kernel_size=3, stride=1, padding=1),
            nn.InstanceNorm3d(64),
            nn.PReLU(64),

            nn.Conv3d(64, 64, kernel_size=3, stride=1, padding=1),
            nn.InstanceNorm3d(64),
            nn.PReLU(64),

            nn.Conv3d(64, 64, kernel_size=3, stride=1, padding=1),
            nn.InstanceNorm3d(64),
            nn.PReLU(64),
        )

        # 定义编码器阶段3
        self.encoder_stage3 = nn.Sequential(
            nn.Conv3d(128, 128, kernel_size=3, stride=1, padding=1),
            nn.InstanceNorm3d(128),
            nn.PReLU(128),

            nn.Conv3d(128, 128, kernel_size=3, stride=1, padding=1),
            nn.InstanceNorm3d(128),
            nn.PReLU(128),

            nn.Conv3d(128, 128, kernel_size=3, stride=1, padding=1),
            nn.InstanceNorm3d(128),
            nn.PReLU(128),
        )

        # 定义编码器阶段4
        self.encoder_stage4 = nn.Sequential(
            nn.Conv3d(256, 256, kernel_size=3, stride=1, padding=1),
            nn.InstanceNorm3d(256),
            nn.PReLU(256),

            nn.Conv3d(256, 256, kernel_size=3, stride=1, padding=1),
            nn.InstanceNorm3d(256),
            nn.PReLU(256),

            nn.Conv3d(256, 256, kernel_size=3, stride=1, padding=1),
            nn.InstanceNorm3d(256),
            nn.PReLU(256),
        )

        # 定义编码器阶段5
        self.encoder_stage5 = nn.Sequential(
            nn.Conv3d(512, 512, kernel_size=3, stride=1, padding=1),
            nn.InstanceNorm3d(512),
            nn.PReLU(512),

            nn.Conv3d(512, 512, kernel_size=3, stride=1, padding=1),
            nn.InstanceNorm3d(512),
            nn.PReLU(512),
        )

        # ---------------------- 解码器部分 ---------------------- #
        # 定义解码器阶段1，处理编码器阶段5的输出
        self.decoder_stage1 = nn.Sequential(
            nn.Conv3d(512, 512, kernel_size=3, stride=1, padding=1),
            nn.InstanceNorm3d(512),
            nn.PReLU(512),

            nn.Conv3d(512, 512, kernel_size=3, stride=1, padding=1),
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

        # ---------------------- 映射层 ---------------------- #
        self.map = nn.Sequential(
            nn.Conv3d(32, out_channel, kernel_size=1, stride=1),
            nn.Softmax(dim=1)
        )

    # 定义前向传播方法
    def forward(self, inputs):
        """
        inputs: 形状为[batch, in_channel, depth, height, width]的3D图像数据
        在训练模式下返回多个尺度的输出，在推理模式下返回最终输出。
        """

        # ------------- 编码器前向传播 ------------- #
        long_range1 = self.encoder_stage1(inputs)
        # 下采样到下一阶段
        short_range1 = self.down_conv1(long_range1)

        long_range2 = self.encoder_stage2(short_range1)
        # 下采样到下一阶段
        short_range2 = self.down_conv2(long_range2)

        long_range3 = self.encoder_stage3(short_range2)
        # 下采样到下一阶段
        short_range3 = self.down_conv3(long_range3)

        long_range4 = self.encoder_stage4(short_range3)
        # 下采样到下一阶段
        short_range4 = self.down_conv4(long_range4)

        long_range5 = self.encoder_stage5(short_range4)

        # ------------- 解码器前向传播 ------------- #
        # 通过解码器阶段1处理编码器输出
        outputs = self.decoder_stage1(long_range5)
        # 上采样到下一阶段
        short_range6 = self.up_conv1(outputs)

        # 将上采样结果与编码器阶段4的特征拼接
        outputs = self.decoder_stage2(torch.cat([short_range6, long_range4], dim=1))
        # 上采样到下一阶段
        short_range7 = self.up_conv2(outputs)

        # 将上采样结果与编码器阶段3的特征拼接
        outputs = self.decoder_stage3(torch.cat([short_range7, long_range3], dim=1))
        # 上采样到下一阶段
        short_range8 = self.up_conv3(outputs)

        # 将上采样结果与编码器阶段2的特征拼接
        outputs = self.decoder_stage4(torch.cat([short_range8, long_range2], dim=1))
        # 上采样到下一阶段
        short_range9 = self.up_conv4(outputs)

        # 将上采样结果与编码器阶段1的特征拼接
        outputs = self.decoder_stage5(torch.cat([short_range9, long_range1], dim=1))
        outputs = self.map(outputs)

        return outputs