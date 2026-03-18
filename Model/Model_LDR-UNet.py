import torch
import torch.nn as nn
import torch.nn.functional as fun


def generate_laplacian_pyramid(inputs, num_levels=5):
    gaussian_pyramid = [inputs]
    for i in range(num_levels - 1):
        smoothed = fun.avg_pool3d(gaussian_pyramid[-1], kernel_size=2, stride=2)
        gaussian_pyramid.append(smoothed)
    laplacian_pyramid = []
    for i in range(num_levels - 1):
        upsampled = fun.interpolate(gaussian_pyramid[i + 1], scale_factor=2, mode='trilinear', align_corners=False)
        diff = gaussian_pyramid[i] - upsampled
        laplacian_pyramid.append(diff)
    laplacian_pyramid.append(gaussian_pyramid[-1])
    return laplacian_pyramid


class ResidualBlock(nn.Module):
    def __init__(self, in_channels, out_channels):
        super(ResidualBlock, self).__init__()
        self.conv1 = nn.Conv3d(in_channels, out_channels, kernel_size=3, stride=1, padding=1)
        self.norm1 = nn.InstanceNorm3d(out_channels)
        self.prelu1 = nn.PReLU(out_channels)
        self.conv2 = nn.Conv3d(out_channels, out_channels, kernel_size=3, stride=1, padding=1)
        self.norm2 = nn.InstanceNorm3d(out_channels)
        self.prelu2 = nn.PReLU(out_channels)
        if in_channels != out_channels:
            self.residual_conv = nn.Conv3d(in_channels, out_channels, kernel_size=1, stride=1, padding=0)
        else:
            self.residual_conv = None

    def forward(self, x):
        identity = x
        out = self.conv1(x)
        out = self.norm1(out)
        out = self.prelu1(out)
        out = self.conv2(out)
        out = self.norm2(out)
        if self.residual_conv is not None:
            identity = self.residual_conv(identity)
        out += identity
        out = self.prelu2(out)
        return out


class UNet(nn.Module):
    def __init__(self, in_channel, out_channel, drop_rate, training):
        super().__init__()
        self.drop_rate = drop_rate
        self.training = training

        # ---------------------- 编码器部分 ---------------------- #
        # 编码器阶段1：输入in_channel + in_channel (from Laplacian)，输出32通道
        self.encoder_stage1 = nn.Sequential(
            ResidualBlock(in_channel + in_channel, 32),
            ResidualBlock(32, 32),
        )
        # 编码器阶段2：输入64 (from down_conv1) + in_channel (from Laplacian)，输出64通道
        self.encoder_stage2 = nn.Sequential(
            ResidualBlock(64 + in_channel, 64),
        )
        # 编码器阶段3：输入128 (from down_conv2) + in_channel (from Laplacian)，输出128通道
        self.encoder_stage3 = nn.Sequential(
            ResidualBlock(128 + in_channel, 128),
        )
        # 编码器阶段4：输入256 (from down_conv3) + in_channel (from Laplacian)，输出256通道
        self.encoder_stage4 = nn.Sequential(
            ResidualBlock(256 + in_channel, 256),
        )
        # 编码器阶段5：输入512 (from down_conv4) + in_channel (from Laplacian)，输出512通道
        self.encoder_stage5 = nn.Sequential(
            ResidualBlock(512 + in_channel, 512),
        )

        # ---------------------- 解码器部分 ---------------------- #
        # 解码器阶段1：输入512 (from encoder_stage5)，输出512通道
        self.decoder_stage1 = nn.Sequential(
            ResidualBlock(512, 512),
        )
        # 解码器阶段2：输入256 (from up_conv1) + 256 (from encoder_stage4)，输出256通道
        self.decoder_stage2 = nn.Sequential(
            ResidualBlock(256 + 256, 256),
        )
        # 解码器阶段3：输入128 (from up_conv2) + 128 (from encoder_stage3)，输出128通道
        self.decoder_stage3 = nn.Sequential(
            ResidualBlock(128 + 128, 128),
        )
        # 解码器阶段4：输入64 (from up_conv3) + 64 (from encoder_stage2)，输出64通道
        self.decoder_stage4 = nn.Sequential(
            ResidualBlock(64 + 64, 64),
        )
        # 解码器阶段5：输入32 (from up_conv4) + 32 (from encoder_stage1)，输出32通道
        self.decoder_stage5 = nn.Sequential(
            ResidualBlock(32 + 32, 32),
            ResidualBlock(32, 32),
        )

        self.down_conv1 = nn.Sequential(
            nn.Conv3d(32, 64, kernel_size=2, stride=2),
            nn.InstanceNorm3d(64),
            nn.PReLU(64)
        )
        self.down_conv2 = nn.Sequential(
            nn.Conv3d(64, 128, kernel_size=2, stride=2),
            nn.InstanceNorm3d(128),
            nn.PReLU(128)
        )
        self.down_conv3 = nn.Sequential(
            nn.Conv3d(128, 256, kernel_size=2, stride=2),
            nn.InstanceNorm3d(256),
            nn.PReLU(256)
        )
        self.down_conv4 = nn.Sequential(
            nn.Conv3d(256, 512, kernel_size=2, stride=2),
            nn.InstanceNorm3d(512),
            nn.PReLU(512)
        )

        self.up_conv1 = nn.Sequential(
            nn.ConvTranspose3d(512, 256, kernel_size=2, stride=2),
            nn.InstanceNorm3d(256),
            nn.PReLU(256)
        )
        self.up_conv2 = nn.Sequential(
            nn.ConvTranspose3d(256, 128, kernel_size=2, stride=2),
            nn.InstanceNorm3d(128),
            nn.PReLU(128)
        )
        self.up_conv3 = nn.Sequential(
            nn.ConvTranspose3d(128, 64, kernel_size=2, stride=2),
            nn.InstanceNorm3d(64),
            nn.PReLU(64)
        )
        self.up_conv4 = nn.Sequential(
            nn.ConvTranspose3d(64, 32, kernel_size=2, stride=2),
            nn.InstanceNorm3d(32),
            nn.PReLU(32)
        )

        self.map1 = nn.Sequential(
            nn.Conv3d(512, out_channel, kernel_size=1, stride=1),
            nn.Upsample(scale_factor=16, mode='trilinear', align_corners=False),
            nn.Softmax(dim=1)
        )

        self.map2 = nn.Sequential(
            nn.Conv3d(256, out_channel, kernel_size=1, stride=1),
            nn.Upsample(scale_factor=8, mode='trilinear', align_corners=False),
            nn.Softmax(dim=1)
        )

        self.map3 = nn.Sequential(
            nn.Conv3d(128, out_channel, kernel_size=1, stride=1),
            nn.Upsample(scale_factor=4, mode='trilinear', align_corners=False),
            nn.Softmax(dim=1)
        )

        self.map4 = nn.Sequential(
            nn.Conv3d(64, out_channel, kernel_size=1, stride=1),
            nn.Upsample(scale_factor=2, mode='trilinear', align_corners=False),
            nn.Softmax(dim=1)
        )
        self.map5 = nn.Sequential(
            nn.Conv3d(32, out_channel, kernel_size=1, stride=1),
            nn.Upsample(scale_factor=1, mode='trilinear', align_corners=False),
            nn.Softmax(dim=1)
        )

    def forward(self, inputs):
        laplacian_pyramid = generate_laplacian_pyramid(inputs, num_levels=5)
        L_0, L_1, L_2, L_3, L_4 = laplacian_pyramid

        inputs_with_L0 = torch.cat([inputs, L_0], dim=1)
        long_range1 = self.encoder_stage1(inputs_with_L0)
        short_range1 = self.down_conv1(long_range1)

        short_range1_with_L1 = torch.cat([short_range1, L_1], dim=1)
        long_range2 = self.encoder_stage2(short_range1_with_L1)
        long_range2 = fun.dropout(long_range2, self.drop_rate, self.training)
        short_range2 = self.down_conv2(long_range2)

        short_range2_with_L2 = torch.cat([short_range2, L_2], dim=1)
        long_range3 = self.encoder_stage3(short_range2_with_L2)
        long_range3 = fun.dropout(long_range3, self.drop_rate, self.training)
        short_range3 = self.down_conv3(long_range3)

        short_range3_with_L3 = torch.cat([short_range3, L_3], dim=1)
        long_range4 = self.encoder_stage4(short_range3_with_L3)
        long_range4 = fun.dropout(long_range4, self.drop_rate, self.training)
        short_range4 = self.down_conv4(long_range4)

        short_range4_with_L4 = torch.cat([short_range4, L_4], dim=1)
        long_range5 = self.encoder_stage5(short_range4_with_L4)
        long_range5 = fun.dropout(long_range5, self.drop_rate, self.training)

        outputs = self.decoder_stage1(long_range5)
        outputs = fun.dropout(outputs, self.drop_rate, self.training)
        output1 = self.map1(outputs)
        short_range6 = self.up_conv1(outputs)

        outputs = self.decoder_stage2(torch.cat([short_range6, long_range4], dim=1))
        outputs = fun.dropout(outputs, self.drop_rate, self.training)
        output2 = self.map2(outputs)
        short_range7 = self.up_conv2(outputs)

        outputs = self.decoder_stage3(torch.cat([short_range7, long_range3], dim=1))
        outputs = fun.dropout(outputs, self.drop_rate, self.training)
        output3 = self.map3(outputs)
        short_range8 = self.up_conv3(outputs)

        outputs = self.decoder_stage4(torch.cat([short_range8, long_range2], dim=1))
        outputs = fun.dropout(outputs, self.drop_rate, self.training)
        output4 = self.map4(outputs)
        short_range9 = self.up_conv4(outputs)

        outputs = self.decoder_stage5(torch.cat([short_range9, long_range1], dim=1))
        output5 = self.map5(outputs)

        if self.training:
            return output1, output2, output3, output4, output5
        else:
            return output5