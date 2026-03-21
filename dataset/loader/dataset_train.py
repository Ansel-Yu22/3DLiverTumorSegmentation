import dataset.loader.transform as tf
import os
import torch
import numpy as np
import SimpleITK as sitk
from torch.utils.data import Dataset


class Train_Dataset(Dataset):
    def __init__(self, args):
        self.args = args
        # 鍔犺浇璁粌鏁版嵁璺緞鍒楄〃骞跺瓨鍌?
        self.filename_list = self.load_file_name_list(os.path.join(self.args.final_data, 'train_path.txt'))
        # 瀹氫箟鏁版嵁澧炲己鎿嶄綔
        self.transform = tf.Compose([
            # 闅忔満娣卞害瑁佸壀
            tf.RandomCrop(self.args.rc_size),
            # 闅忔満宸﹀彸缈昏浆
            tf.RandomFlipLR(self.args.prob),
            # 闅忔満涓婁笅缈昏浆
            tf.RandomFlipUD(self.args.prob),
            # 闅忔満90搴︽棆杞?
            tf.RandomRotation90(self.args.prob),
            # 闅忔満骞崇Щ
            tf.RandomTranslation(self.args.prob),
            # 闅忔満楂樻柉鍣０
            tf.RandomNoise(self.args.prob)
        ])

    def __getitem__(self, index):
        # 璇诲彇CT鍥惧儚鍜屽垎鍓插浘鍍忓苟鎹负NumPy鏁扮粍
        ct = sitk.ReadImage(self.filename_list[index][0], sitk.sitkInt16)
        ct_array = sitk.GetArrayFromImage(ct)
        seg = sitk.ReadImage(self.filename_list[index][1], sitk.sitkUInt8)
        seg_array = sitk.GetArrayFromImage(seg)
        # 灏咰T鍥惧儚鐨勭伆搴﹀€煎綊涓€鍖?
        ct_array = (ct_array + 100) / 400
        ct_array = ct_array.astype(np.float32)
        # 灏哊umPy鏁扮粍杞崲涓篜yTorch寮犻噺锛屽苟涓洪€氶亾娣诲姞涓€涓淮搴?
        ct_array = torch.FloatTensor(ct_array).unsqueeze(0)
        seg_array = torch.FloatTensor(seg_array).unsqueeze(0)
        # 濡傛灉瀹氫箟浜嗘暟鎹寮哄彉鎹紝鍒欒繘琛屽彉鎹?
        if self.transform:
            ct_array, seg_array = self.transform(ct_array, seg_array)
        # 杩斿洖澶勭悊鍚庣殑CT鍥惧儚鍜屽垎鍓插浘鍍?
        return ct_array, seg_array.squeeze(0)

    def __len__(self):
        # 杩斿洖鏁版嵁闆嗙殑澶у皬锛堝嵆鏂囦欢鍒楄〃鐨勯暱搴︼級
        return len(self.filename_list)

    def load_file_name_list(self, file_path):
        # 浠庢枃浠朵腑璇诲彇鎵€鏈夊浘鍍忚矾寰勶紝骞舵寜绌虹櫧瀛楃鍒嗗壊
        with open(file_path, 'r') as file_to_read:
            # 浣跨敤鍒楄〃鎺ㄥ灏嗘瘡涓€琛屾寜绌虹櫧瀛楃鍒嗗壊鍚庢坊鍔犲埌鍒楄〃涓?
            file_name_list = [line.strip().split() for line in file_to_read if line.strip()]
        # 杩斿洖鏂囦欢璺緞鍒楄〃
        return file_name_list

class Val_Dataset(Dataset):
    def __init__(self, args):
        self.args = args
        # 鍔犺浇璁粌鏁版嵁璺緞鍒楄〃骞跺瓨鍌?
        self.filename_list = self.load_file_name_list(os.path.join(self.args.final_data, 'val_path.txt'))
        # 瀹氫箟鏁版嵁澧炲己鍙樻崲鎿嶄綔
        self.transforms = tf.Compose([
            # 涓績瑁佸壀锛宐ase鏄鍓殑鏈€灏忓昂瀵革紝max_size鏄渶澶у昂瀵?
            tf.CenterCrop(base=16, max_size=self.args.cc_size)
        ])

    def __getitem__(self, index):
        # 璇诲彇CT鍥惧儚鍜屽垎鍓插浘鍍忓苟杞崲涓篘umPy鏁扮粍
        ct = sitk.ReadImage(self.filename_list[index][0], sitk.sitkInt16)
        ct_array = sitk.GetArrayFromImage(ct)
        seg = sitk.ReadImage(self.filename_list[index][1], sitk.sitkUInt8)
        seg_array = sitk.GetArrayFromImage(seg)
        # 灏咰T鍥惧儚鐨勭伆搴﹀€煎綊涓€鍖?
        ct_array = (ct_array + 100) / 400
        ct_array = ct_array.astype(np.float32)
        # 灏哊umPy鏁扮粍杞崲涓篜yTorch寮犻噺锛屽苟涓洪€氶亾娣诲姞涓€涓淮搴?
        ct_array = torch.FloatTensor(ct_array).unsqueeze(0)
        seg_array = torch.FloatTensor(seg_array).unsqueeze(0)
        # 濡傛灉瀹氫箟浜嗘暟鎹寮哄彉鎹紝鍒欒繘琛屽彉鎹?
        if self.transforms:
            ct_array, seg_array = self.transforms(ct_array, seg_array)
        # 杩斿洖澶勭悊鍚庣殑CT鍥惧儚鍜屽垎鍓插浘鍍?
        return ct_array, seg_array.squeeze(0)

    def __len__(self):
        # 杩斿洖鏁版嵁闆嗙殑澶у皬锛堝嵆鏂囦欢鍒楄〃鐨勯暱搴︼級
        return len(self.filename_list)

    def load_file_name_list(self, file_path):
        # 浠庢枃浠朵腑璇诲彇鎵€鏈夊浘鍍忚矾寰勶紝骞舵寜绌虹櫧瀛楃鍒嗗壊
        with open(file_path, 'r') as file_to_read:
            # 浣跨敤鍒楄〃鎺ㄥ灏嗘瘡涓€琛屾寜绌虹櫧瀛楃鍒嗗壊鍚庢坊鍔犲埌鍒楄〃涓?
            file_name_list = [line.strip().split() for line in file_to_read if line.strip()]
        # 杩斿洖鏂囦欢璺緞鍒楄〃
        return file_name_list

