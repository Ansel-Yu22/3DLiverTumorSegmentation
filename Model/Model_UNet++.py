import torch
import torch.nn as nn


class UNetPlusPlus(nn.Module):
    def __init__(self, in_channel, out_channel, drop_rate, training):
        super().__init__()
        self.drop_rate = drop_rate
        self.training = training

        self.encoder_stage1 = nn.Sequential(
            nn.Conv3d(in_channel, 16, kernel_size=3, stride=1, padding=1),
            nn.InstanceNorm3d(16),
            nn.PReLU(16),
        )
        self.encoder_stage2 = nn.Sequential(
            nn.Conv3d(32, 32, kernel_size=3, stride=1, padding=1),
            nn.InstanceNorm3d(32),
            nn.PReLU(32),
        )
        self.encoder_stage3 = nn.Sequential(
            nn.Conv3d(64, 64, kernel_size=3, stride=1, padding=1),
            nn.InstanceNorm3d(64),
            nn.PReLU(64),
        )
        self.encoder_stage4 = nn.Sequential(
            nn.Conv3d(128, 128, kernel_size=3, stride=1, padding=1),
            nn.InstanceNorm3d(128),
            nn.PReLU(128),
        )

        self.down_conv1 = nn.Sequential(
            nn.Conv3d(16, 32, kernel_size=2, stride=2),
            nn.InstanceNorm3d(32),
            nn.PReLU(32)
        )
        self.down_conv2 = nn.Sequential(
            nn.Conv3d(32, 64, kernel_size=2, stride=2),
            nn.InstanceNorm3d(64),
            nn.PReLU(64)
        )
        self.down_conv3 = nn.Sequential(
            nn.Conv3d(64, 128, kernel_size=2, stride=2),
            nn.InstanceNorm3d(128),
            nn.PReLU(128)
        )

        self.up_conv1 = nn.Sequential(
            nn.ConvTranspose3d(128, 64, kernel_size=2, stride=2),
            nn.InstanceNorm3d(64),
            nn.PReLU(64)
        )
        self.up_conv2 = nn.Sequential(
            nn.ConvTranspose3d(64, 32, kernel_size=2, stride=2),
            nn.InstanceNorm3d(32),
            nn.PReLU(32)
        )
        self.up_conv3 = nn.Sequential(
            nn.ConvTranspose3d(32, 16, kernel_size=2, stride=2),
            nn.InstanceNorm3d(16),
            nn.PReLU(16)
        )

        self.decoder_stage1 = nn.Sequential(
            nn.Conv3d(128, 128, kernel_size=3, stride=1, padding=1),
            nn.InstanceNorm3d(128),
            nn.PReLU(128),
        )
        self.decoder_stage2_0 = nn.Sequential(
            nn.Conv3d(64 + 64, 64, kernel_size=3, stride=1, padding=1),
            nn.InstanceNorm3d(64),
            nn.PReLU(64),
        )
        self.decoder_stage3_0 = nn.Sequential(
            nn.Conv3d(32 + 32, 32, kernel_size=3, stride=1, padding=1),
            nn.InstanceNorm3d(32),
            nn.PReLU(32),
        )
        self.decoder_stage4_0 = nn.Sequential(
            nn.Conv3d(16 + 16, 16, kernel_size=3, stride=1, padding=1),
            nn.InstanceNorm3d(16),
            nn.PReLU(16),
        )

        self.map = nn.Sequential(
            nn.Conv3d(16, out_channel, kernel_size=1, stride=1),
            nn.Softmax(dim=1)
        )

    def forward(self, inputs):
        long_range1 = self.encoder_stage1(inputs)
        short_range1 = self.down_conv1(long_range1)
        long_range2 = self.encoder_stage2(short_range1)
        short_range2 = self.down_conv2(long_range2)
        long_range3 = self.encoder_stage3(short_range2)
        short_range3 = self.down_conv3(long_range3)
        long_range4 = self.encoder_stage4(short_range3)
        outputs_1_0 = self.decoder_stage1(long_range4)
        up_1_0 = self.up_conv1(outputs_1_0)
        outputs_2_0 = self.decoder_stage2_0(torch.cat([up_1_0, long_range3], dim=1))
        up_2_0 = self.up_conv2(outputs_2_0)
        outputs_3_0 = self.decoder_stage3_0(torch.cat([up_2_0, long_range2], dim=1))
        up_3_0 = self.up_conv3(outputs_3_0)
        outputs_4_0 = self.decoder_stage4_0(torch.cat([up_3_0, long_range1], dim=1))
        final_output = self.map(outputs_4_0)
        return final_output