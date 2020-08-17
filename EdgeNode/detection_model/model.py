from pandas import read_csv
import numpy as np
from numpy import dstack


def load_file(file_path):
    data_frame = read_csv(file_path, header=None, delim_whitespace=True)
    return data_frame.values


if __name__ == "__main__":
    loaded = list()
    loaded.append(load_file('UCI HAR Dataset/train/Inertial Signals/total_acc_x_train.txt'))
    loaded.append(load_file('UCI HAR Dataset/train/Inertial Signals/total_acc_y_train.txt'))
    loaded.append(load_file('UCI HAR Dataset/train/Inertial Signals/total_acc_z_train.txt'))
    loaded.append(load_file('UCI HAR Dataset/train/Inertial Signals/body_acc_x_train.txt'))
    loaded.append(load_file('UCI HAR Dataset/train/Inertial Signals/body_acc_y_train.txt'))
    loaded.append(load_file('UCI HAR Dataset/train/Inertial Signals/body_acc_z_train.txt'))
    loaded.append(load_file('UCI HAR Dataset/train/Inertial Signals/body_gyro_x_train.txt'))
    loaded.append(load_file('UCI HAR Dataset/train/Inertial Signals/body_gyro_y_train.txt'))
    loaded.append(load_file('UCI HAR Dataset/train/Inertial Signals/body_gyro_z_train.txt'))

    loaded = dstack(loaded)
    print(loaded.shape)


