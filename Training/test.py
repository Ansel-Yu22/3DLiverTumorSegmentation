import config
from Model.Model import UNet
from Dataset.dataset_test import Test_Datasets
import os
import torch
import numpy as np
import SimpleITK as sitk
from tqdm import tqdm
from Util.log import Test_Log
from collections import OrderedDict
from torch.utils.data import DataLoader
from Util.evaluate import MetricsCalculator


def predict(model, ct_dataset, args):
    dataloader = DataLoader(dataset=ct_dataset, batch_size=1, num_workers=0, shuffle=False)
    model.eval()
    metrics_calc = MetricsCalculator(args.n_label)
    target = to_one_hot_3d(ct_dataset.label, args.n_label)
    with torch.no_grad():
        for data in tqdm(dataloader, total=len(dataloader)):
            data = data.to(device)
            output = model(data)
            output = torch.nn.functional.interpolate(output, scale_factor=(
                1 / args.z_down_scale, 1 / args.xy_down_scale, 1 / args.xy_down_scale), mode='trilinear',
                                                     align_corners=False)
            ct_dataset.update_result(output.detach().cpu())
    pred = ct_dataset.recompone_result()
    pred = torch.argmax(pred, dim=1)
    pred_ct = to_one_hot_3d(pred, args.n_label)
    metrics_calc.update(pred_ct, target)
    dice_avg, iou_avg, sensitivity_avg, precision_avg = metrics_calc.get_averages()
    result_metrics = OrderedDict({
        'Dice_liver': dice_avg[1], 'IoU_liver': iou_avg[1],
        'Sensitivity_liver': sensitivity_avg[1], 'Precision_liver': precision_avg[1]
    })
    if args.n_label == 3:
        result_metrics.update({
            'Dice_tumor': dice_avg[2], 'IoU_tumor': iou_avg[2],
            'Sensitivity_tumor': sensitivity_avg[2], 'Precision_tumor': precision_avg[2]
        })
    pred = np.asarray(pred.numpy(), dtype='uint8')
    pred = sitk.GetImageFromArray(np.squeeze(pred, axis=0))
    return result_metrics, pred

def to_one_hot_3d(tensor, n_label):
    n, s, h, w = tensor.size()
    one_hot = torch.zeros(n, n_label, s, h, w)
    one_hot = one_hot.scatter_(1, tensor.view(n, 1, s, h, w), 1)
    return one_hot


if __name__ == '__main__':
    args = config.args
    save_path = args.model_save
    device = torch.device('cpu' if args.cpu else 'cuda')
    model = UNet(in_channel=1, out_channel=args.n_label, drop_rate=args.drop_rate, training=False)
    model = torch.nn.DataParallel(model)
    model = model.to(device)
    checkpoint = torch.load(f'{args.model_save}/best_model.pth')
    model.load_state_dict(checkpoint['net'])
    test_log = Test_Log(args.log_save, "test_log")
    result_save_path = '{}/result'.format(args.log_save)
    if not os.path.exists(result_save_path):
        os.mkdir(result_save_path)
    datasets = Test_Datasets(args.test_path, args=args)
    total_dice_liver = 0
    total_iou_liver = 0
    total_sensitivity_liver = 0
    total_precision_liver = 0
    total_dice_tumor = 0
    total_iou_tumor = 0
    total_sensitivity_tumor = 0
    total_precision_tumor = 0
    num_ct = 0
    for ct_dataset, ct_name in datasets:
        test_metrics, pred_ct = predict(model, ct_dataset, args)
        test_log.update(ct_name, test_metrics)
        sitk.WriteImage(pred_ct, os.path.join(result_save_path, 'result-' + ct_name))
        total_dice_liver += test_metrics['Dice_liver']
        total_iou_liver += test_metrics['IoU_liver']
        total_sensitivity_liver += test_metrics['Sensitivity_liver']
        total_precision_liver += test_metrics['Precision_liver']
        if args.n_label == 3:
            total_dice_tumor += test_metrics['Dice_tumor']
            total_iou_tumor += test_metrics['IoU_tumor']
            total_sensitivity_tumor += test_metrics['Sensitivity_tumor']
            total_precision_tumor += test_metrics['Precision_tumor']
        num_ct += 1
    avg_dice_liver = total_dice_liver / num_ct
    avg_iou_liver = total_iou_liver / num_ct
    avg_sensitivity_liver = total_sensitivity_liver / num_ct
    avg_precision_liver = total_precision_liver / num_ct
    if args.n_label == 3:
        avg_dice_tumor = total_dice_tumor / num_ct
        avg_iou_tumor = total_iou_tumor / num_ct
        avg_sensitivity_tumor = total_sensitivity_tumor / num_ct
        avg_precision_tumor = total_precision_tumor / num_ct
    print("\n\033[0;34mAverage Metrics:\033[0m")
    print(f"Dice_liver: {avg_dice_liver:.4f}")
    print(f"IoU_liver: {avg_iou_liver:.4f}")
    print(f"Sensitivity_liver: {avg_sensitivity_liver:.4f}")
    print(f"Precision_liver: {avg_precision_liver:.4f}")
    if args.n_label == 3:
        print(f"Dice_tumor: {avg_dice_tumor:.4f}")
        print(f"IoU_tumor: {avg_iou_tumor:.4f}")
        print(f"Sensitivity_tumor: {avg_sensitivity_tumor:.4f}")
        print(f"Precision_tumor: {avg_precision_tumor:.4f}")