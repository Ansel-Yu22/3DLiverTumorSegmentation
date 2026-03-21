import torch
import torch.nn as nn


class ResidualBlock(nn.Module):
    def __init__(self, in_channels, out_channels):
        """
        残差块，用于增强特征传递和缓解梯度消失问题。
        in_channels (int): 输入通道数
        out_channels (int): 输出通道数
        """
        super(ResidualBlock, self).__init__()
        # 第一个卷积层：3x3x3卷积，保持空间尺寸不变
        self.conv1 = nn.Conv3d(in_channels, out_channels, kernel_size=3, stride=1, padding=1)
        self.norm1 = nn.InstanceNorm3d(out_channels)
        self.prelu1 = nn.PReLU(out_channels)
        # 第二个卷积层：3x3x3卷积，保持空间尺寸不变
        self.conv2 = nn.Conv3d(out_channels, out_channels, kernel_size=3, stride=1, padding=1)
        self.norm2 = nn.InstanceNorm3d(out_channels)
        self.prelu2 = nn.PReLU(out_channels)
        # 如果输入和输出通道数不同，使用1x1卷积调整通道数以匹配残差连接
        if in_channels != out_channels:
            self.residual_conv = nn.Conv3d(in_channels, out_channels, kernel_size=1, stride=1, padding=0)
        else:
            self.residual_conv = None

    def forward(self, x):
        """
        前向传播：通过两个卷积层并添加残差连接。
        参数:
        x (Tensor): 输入特征图
        返回:
        Tensor: 输出特征图
        """
        # 保存输入用于残差连接
        identity = x
        out = self.conv1(x)
        out = self.norm1(out)
        out = self.prelu1(out)
        out = self.conv2(out)
        out = self.norm2(out)
        # 应用残差连接：将输入加到输出上
        if self.residual_conv is not None:
            identity = self.residual_conv(identity)
        out += identity
        out = self.prelu2(out)
        return out


class UNet(nn.Module):
    def __init__(self, in_channel, out_channel, drop_rate, training):
        """
        in_channel: 输入通道数
        out_channel: 输出通道数
        drop_rate: 丢弃率
        training: 是否在训练模式（启用丢弃）
        """
        super().__init__()
        self.drop_rate = drop_rate
        self.training = training

        # ---------------------- 编码器部分 ---------------------- #
        # 编码器阶段1：输入in_channel，输出32通道
        self.encoder_stage1 = nn.Sequential(
            ResidualBlock(in_channel, 32),
            ResidualBlock(32, 32),
        )

        # 编码器阶段2：输入64通道，输出64通道
        self.encoder_stage2 = nn.Sequential(
            ResidualBlock(64, 64),
        )

        # 编码器阶段3：输入128通道，输出128通道
        self.encoder_stage3 = nn.Sequential(
            ResidualBlock(128, 128),
        )

        # 编码器阶段4：输入256通道，输出256通道
        self.encoder_stage4 = nn.Sequential(
            ResidualBlock(256, 256),
        )

        # 编码器阶段5：输入512通道，输出512通道
        self.encoder_stage5 = nn.Sequential(
            ResidualBlock(512, 512),
        )

        # ---------------------- 解码器部分 ---------------------- #
        # 解码器阶段1：处理编码器阶段5的输出，输入512通道，输出512通道
        self.decoder_stage1 = nn.Sequential(
            ResidualBlock(512, 512),
        )

        # 解码器阶段2：融合上采样和编码器阶段4的特征，输入256+256=512通道，输出256通道
        self.decoder_stage2 = nn.Sequential(
            ResidualBlock(256 + 256, 256),
        )

        # 解码器阶段3：融合上采样和编码器阶段3的特征，输入128+128=256通道，输出128通道
        self.decoder_stage3 = nn.Sequential(
            ResidualBlock(128 + 128, 128),
        )

        # 解码器阶段4：融合上采样和编码器阶段2的特征，输入64+64=128通道，输出64通道
        self.decoder_stage4 = nn.Sequential(
            ResidualBlock(64 + 64, 64),
        )

        # 解码器阶段5：融合上采样和编码器阶段1的特征，输入32+32=64通道，输出32通道
        self.decoder_stage5 = nn.Sequential(
            ResidualBlock(32 + 32, 32),
            ResidualBlock(32, 32),
        )

        # ---------------------- 下采样操作 ---------------------- #
        # 下采样层1：从32通道到64通道，减小空间尺寸
        self.down_conv1 = nn.Sequential(
            nn.Conv3d(32, 64, kernel_size=2, stride=2),
            nn.InstanceNorm3d(64),
            nn.PReLU(64)
        )

        # 下采样层2：从64通道到128通道，减小空间尺寸
        self.down_conv2 = nn.Sequential(
            nn.Conv3d(64, 128, kernel_size=2, stride=2),
            nn.InstanceNorm3d(128),
            nn.PReLU(128)
        )

        # 下采样层3：从128通道到256通道，减小空间尺寸
        self.down_conv3 = nn.Sequential(
            nn.Conv3d(128, 256, kernel_size=2, stride=2),
            nn.InstanceNorm3d(256),
            nn.PReLU(256)
        )

        # 下采样层4：从256通道到512通道，减小空间尺寸
        self.down_conv4 = nn.Sequential(
            nn.Conv3d(256, 512, kernel_size=2, stride=2),
            nn.InstanceNorm3d(512),
            nn.PReLU(512)
        )

        # ---------------------- 上采样操作 ---------------------- #
        # 上采样层1：从512通道到256通道，增大空间尺寸
        self.up_conv1 = nn.Sequential(
            nn.ConvTranspose3d(512, 256, kernel_size=2, stride=2),
            nn.InstanceNorm3d(256),
            nn.PReLU(256)
        )

        # 上采样层2：从256通道到128通道，增大空间尺寸
        self.up_conv2 = nn.Sequential(
            nn.ConvTranspose3d(256, 128, kernel_size=2, stride=2),
            nn.InstanceNorm3d(128),
            nn.PReLU(128)
        )

        # 上采样层3：从128通道到64通道，增大空间尺寸
        self.up_conv3 = nn.Sequential(
            nn.ConvTranspose3d(128, 64, kernel_size=2, stride=2),
            nn.InstanceNorm3d(64),
            nn.PReLU(64)
        )

        # 上采样层4：从64通道到32通道，增大空间尺寸
        self.up_conv4 = nn.Sequential(
            nn.ConvTranspose3d(64, 32, kernel_size=2, stride=2),
            nn.InstanceNorm3d(32),
            nn.PReLU(32)
        )

        # ---------------------- 映射层 ---------------------- #
        # 映射层：将32通道映射到out_channel，并应用Softmax激活
        self.map = nn.Sequential(
            nn.Conv3d(32, out_channel, kernel_size=1, stride=1),
            nn.Softmax(dim=1)
        )

    def forward(self, inputs):
        """
        前向传播：通过编码器提取特征，通过解码器恢复空间尺寸并生成分割图。
        参数:
        inputs (Tensor): 输入图像，形状为[batch, in_channel, depth, height, width]
        返回:
        Tensor: 分割图，形状为[batch, out_channel, depth, height, width]
        """
        # ------------- 编码器前向传播 ------------- #
        # 编码器阶段1：输入->32通道
        long_range1 = self.encoder_stage1(inputs)
        # 下采样到下一阶段：32->64通道，空间尺寸减半
        short_range1 = self.down_conv1(long_range1)
        # 编码器阶段2：64通道
        long_range2 = self.encoder_stage2(short_range1)
        # 下采样到下一阶段：64->128通道，空间尺寸减半
        short_range2 = self.down_conv2(long_range2)
        # 编码器阶段3：128通道
        long_range3 = self.encoder_stage3(short_range2)
        # 下采样到下一阶段：128->256通道，空间尺寸减半
        short_range3 = self.down_conv3(long_range3)
        # 编码器阶段4：256通道
        long_range4 = self.encoder_stage4(short_range3)
        # 下采样到下一阶段：256->512通道，空间尺寸减半
        short_range4 = self.down_conv4(long_range4)
        # 编码器阶段5：512通道
        long_range5 = self.encoder_stage5(short_range4)

        # ------------- 解码器前向传播 ------------- #
        # 解码器阶段1：处理编码器阶段5的输出，512通道
        outputs = self.decoder_stage1(long_range5)
        # 上采样到下一阶段：512->256通道，空间尺寸翻倍
        short_range6 = self.up_conv1(outputs)
        # 解码器阶段2：融合上采样（256通道）和编码器阶段4（256通道），输入512通道->256通道
        outputs = self.decoder_stage2(torch.cat([short_range6, long_range4], dim=1))
        # 上采样到下一阶段：256->128通道，空间尺寸翻倍
        short_range7 = self.up_conv2(outputs)
        # 解码器阶段3：融合上采样（128通道）和编码器阶段3（128通道），输入256通道->128通道
        outputs = self.decoder_stage3(torch.cat([short_range7, long_range3], dim=1))
        # 上采样到下一阶段：128->64通道，空间尺寸翻倍
        short_range8 = self.up_conv3(outputs)
        # 解码器阶段4：融合上采样（64通道）和编码器阶段2（64通道），输入128通道->64通道
        outputs = self.decoder_stage4(torch.cat([short_range8, long_range2], dim=1))
        # 上采样到下一阶段：64->32通道，空间尺寸翻倍
        short_range9 = self.up_conv4(outputs)
        # 解码器阶段5：融合上采样（32通道）和编码器阶段1（32通道），输入64通道->32通道
        outputs = self.decoder_stage5(torch.cat([short_range9, long_range1], dim=1))
        # 映射到最终输出：32通道->out_channel，并应用Softmax
        outputs = self.map(outputs)

        return outputs