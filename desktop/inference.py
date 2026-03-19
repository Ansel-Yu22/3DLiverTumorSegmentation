import numpy as np
import SimpleITK as sitk
import torch
from scipy import ndimage
from torch.utils.data import Dataset


class Test_DataSet(Dataset):
    def __init__(self, ct_path, label_path, args):
        self.n_label = args.n_label
        self.cut_size = args.tc_size
        self.cut_stride = args.tc_stride
        self.ct = sitk.ReadImage(ct_path, sitk.sitkInt16)
        self.ct_np = sitk.GetArrayFromImage(self.ct)
        self.ori_shape = self.ct_np.shape
        self.ct_np = ndimage.zoom(self.ct_np, (args.z_down_scale, args.xy_down_scale, args.xy_down_scale), order=3)
        self.resized_shape = self.ct_np.shape
        self.ct_np[self.ct_np > args.upper] = args.upper
        self.ct_np[self.ct_np < args.lower] = args.lower
        self.ct_np = (self.ct_np + 100) / 400
        self.ct_np = self.ct_np.astype(np.float32)
        self.ct_np = self.padding_ct(self.ct_np, self.cut_size, self.cut_stride)
        self.padding_shape = self.ct_np.shape
        self.ct_np = self.extract_ordered_overlap(self.ct_np, self.cut_size, self.cut_stride)
        self.label = None
        if label_path:
            self.seg = sitk.ReadImage(label_path, sitk.sitkInt8)
            self.label_np = sitk.GetArrayFromImage(self.seg)
            if self.n_label == 2:
                self.label_np[self.label_np > 0] = 1
            self.label = torch.from_numpy(np.expand_dims(self.label_np, axis=0)).long()
        self.result = None

    def __getitem__(self, index):
        data = torch.from_numpy(self.ct_np[index])
        data = torch.FloatTensor(data).unsqueeze(0)
        return data

    def __len__(self):
        return len(self.ct_np)

    def update_result(self, tensor):
        if self.result is not None:
            self.result = torch.cat((self.result, tensor), dim=0)
        else:
            self.result = tensor

    def recompone_result(self):
        patch_s = self.result.shape[2]
        N_patches_ct = (self.padding_shape[0] - patch_s) // self.cut_stride + 1
        assert (self.result.shape[0] == N_patches_ct)
        full_prob = torch.zeros((self.n_label, self.padding_shape[0], self.ori_shape[1], self.ori_shape[2]))
        full_sum = torch.zeros((self.n_label, self.padding_shape[0], self.ori_shape[1], self.ori_shape[2]))
        for s in range(N_patches_ct):
            full_prob[:, s * self.cut_stride:s * self.cut_stride + patch_s] += self.result[s]
            full_sum[:, s * self.cut_stride:s * self.cut_stride + patch_s] += 1
        assert (torch.min(full_sum) >= 1.0)
        final_avg = full_prob / full_sum
        assert (torch.max(final_avg) <= 1.0)
        assert (torch.min(final_avg) >= 0.0)
        ct = final_avg[:, :self.ori_shape[0], :self.ori_shape[1], :self.ori_shape[2]]
        return ct.unsqueeze(0)

    def padding_ct(self, ct, size, stride):
        assert (len(ct.shape) == 3)
        ct_s, ct_h, ct_w = ct.shape
        leftover_s = (ct_s - size) % stride
        if (leftover_s != 0):
            s = ct_s + (stride - leftover_s)
        else:
            s = ct_s
        tmp_full_imgs = np.zeros((s, ct_h, ct_w), dtype=np.float32)
        tmp_full_imgs[:ct_s] = ct
        return tmp_full_imgs

    def extract_ordered_overlap(self, ct, size, stride):
        ct_s, ct_h, ct_w = ct.shape
        assert (ct_s - size) % stride == 0
        N_patches_ct = (ct_s - size) // stride + 1
        patches = np.empty((N_patches_ct, size, ct_h, ct_w), dtype=np.float32)
        for s in range(N_patches_ct):
            patch = ct[s * stride: s * stride + size]
            patches[s] = patch
        return patches

class MetricsCalculator(object):
    def __init__(self, class_num):
        self.class_num = class_num
        self.reset()

    def reset(self):
        self.dice_sum = np.asarray([0] * self.class_num, dtype='float64')
        self.iou_sum = np.asarray([0] * self.class_num, dtype='float64')
        self.count = 0

    def update(self, logits, targets):
        dice, iou = self.get_metrics(logits, targets)
        self.dice_sum += dice
        self.iou_sum += iou
        self.count += 1

    def get_averages(self):
        dice_avg = np.around(self.dice_sum / self.count, 4)
        iou_avg = np.around(self.iou_sum / self.count, 4)
        return dice_avg, iou_avg

    def get_metrics(self, logits, targets):
        dices = []
        ious = []
        for class_index in range(targets.size()[1]):
            inter = torch.sum(logits[:, class_index, :, :, :] * targets[:, class_index, :, :, :])
            union = torch.sum(logits[:, class_index, :, :, :]) + torch.sum(targets[:, class_index, :, :, :])
            dice = (2. * inter) / (union + 0.0001)
            iou = inter / (union - inter + 0.0001)
            dices.append(dice.item())
            ious.append(iou.item())
        return np.asarray(dices), np.asarray(ious)
