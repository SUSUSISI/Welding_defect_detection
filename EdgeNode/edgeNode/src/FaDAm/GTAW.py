import csv
from datetime import datetime, timedelta
import random as rd

import numpy as np

from FaDAm.utility.Errors import *


class GTAW_data:
    def __init__(self, data=None):
        if data is None:
            self.__time = []
            self.__process_id = None
            self.__data = np.zeros([0, 3], dtype=np.float32)
            self.__prediction_label = 'null'
            self.__label = 'null'
        else:
            self.__time = []
            self.__process_id = None
            self.__data = np.zeros([0, 3], dtype=np.float32)
            self.__prediction_label = 'null'
            self.__label = 'null'
            # 후에 필요할 시 다시 수정할 것.
            # first_row = data[0]
            # self.__time = datetime.strptime(first_row[1],'%Y-%m-%d %H:%M:%S.%f')
            # self.__process_id = int(first_row[2])
            # self.__prediction_label = first_row[6]
            # self.__label = first_row[7]
            # self.__data = np.zeros([0, 3], dtype=np.float32)
            #
            # for row in data:
            #     new_data = np.array([float(e) for e in row[3:6]])
            #     self.__data = np.concatenate((self.__data, np.array([new_data])))

    def append_data(self, _time, _data):
        if isinstance(_time, str):
            self.__time.append(datetime.strptime(_time, '%Y-%m-%d %H:%M:%S.%f'))
        elif isinstance(_time, datetime):
            self.__time.append(_time)
        else:
            raise InputError('time must be datetime or string formated \%Y-\%m-\%d \%H:\%M:\%S.\%f')

        if len(_data) == 3:
            if _data[0] is None:
                new_data = np.array([None, None, None])
            else:
                new_data = np.array([float(e) for e in _data])
        else:
            raise InputError('data input error')

        self.__data = np.concatenate((self.__data, np.array([new_data])))

    @property
    def time(self):
        return self.__time

    @property
    def process_id(self):
        return self.__process_id

    @property
    def data(self):
        return self.__data

    @property
    def prediction_label(self):
        return self.__prediction_label

    @property
    def label(self):
        return self.__label

    # @time.setter
    # def time(self, _time):
    #     if isinstance(_time, str):
    #         self.__time = datetime.strptime(_time, '%Y-%m-%d %H:%M:%S.%f')
    #     elif isinstance(_time, datetime):
    #         self.__time = _time
    #     else:
    #         raise InputError('Input type must be datetime or string formated \%Y-\%m-\%d \%H:\%M:\%S.\%f')

    @process_id.setter
    def process_id(self, _process_id):
        self.__process_id = int(_process_id)

    # @data.setter
    # def data(self, _data):
    #     self.__data = data

    @prediction_label.setter
    def prediction_label(self, _prediction_label):
        self.__prediction_label = _prediction_label

    @label.setter
    def label(self, _label):
        self.__label = _label


def read_GTAW_welding_data(path):
    data = []

    file = open(path, 'r', encoding='utf-8')
    reader = csv.reader(file)

    first_row = next(reader)

    if len(first_row) != 8:
        raise InputError(
            'Input data must be list with length 8 which consist of [data_id, date, process_id, avg_curr, avg_volt, avg_wire, prediction, label]')

    new_data = GTAW_data()
    for row in reader:
        if new_data.process_id is not None:
            if int(row[2]) == new_data.process_id:
                new_data.append_data(row[1], [row[3], row[4], row[5]])
            else:
                data.append(new_data)
                new_data = GTAW_data()

        if new_data.process_id is None:
            new_data.process_id = row[2]
            new_data.prediction_label = row[6]
            new_data.label = row[7]
            new_data.append_data(row[1], [row[3], row[4], row[5]])

    data.append(new_data)
    file.close()

    return data


def save_GTAW_welding_data_list(data, path):
    file = open(path, 'w', encoding='utf-8', newline='')
    writer = csv.writer(file)
    data_index = 1

    writer.writerow(
        ['Data No.', 'Date', 'Process ID', 'Avg. Current', 'Avg. Voltage', 'Avg. Wire Feed', 'Prediction', 'Label'])

    for e in data:

        curr_data = e.data

        for i in curr_data:
            row = [data_index, e.time[i], e.process_id, round(i[0], 1), round(i[1], 1),
                   round(i[2], 1), e.prediction_label, e.label]
            writer.writerow(row)

            data_index += 1

    file.close()


def save_welding_data(data, path):
    file = open(path, 'w', encoding='utf-8', newline='')
    writer = csv.writer(file)
    data_index = 1

    writer.writerow(
        ['Data No.', 'Date', 'Process ID', 'Avg. Current', 'Avg. Voltage', 'Avg. Wire Feed', 'Prediction', 'Label'])

    curr_data = data.data

    for i in range(len(curr_data)):
        row = [data_index, data.time[i], data.process_id, curr_data[i][0], curr_data[i][1],
               curr_data[i][2], data.prediction_label, data.label]
        writer.writerow(row)
        data_index += 1

    file.close()


def merge_GTAW_datasets(_paths, _target):
    data = []

    for path in _paths:
        file = open(path, 'r', encoding='utf-8')
        reader = csv.reader(file)

        first_row = next(reader)

        if len(first_row) != 8:
            raise InputError(
                'Input data must be list with length 8 which consist of [data_id, date, process_id, avg_curr, avg_volt, avg_wire, prediction, label], file name: {}'.format(
                    path))

        new_data = GTAW_data()
        for row in reader:
            if new_data.process_id != None:
                if int(row[2]) == new_data.process_id:
                    new_data.append_data(row)
                else:
                    data.append(new_data)
                    new_data = GTAW_data()

            if new_data.process_id == None:
                new_data.time = row[1]
                new_data.process_id = row[2]
                new_data.prediction_label = row[6]
                new_data.label = row[7]
                new_data.append_data(row)

        data.append(new_data)
        file.close()

    save_GTAW_welding_data_list(data, _target)


# def generate_noised_data(base_lines, noise_ratio=0.05):
#     noise_current = np.random.normal(-noise_ratio, noise_ratio)
#     noise_voltage = np.random.normal(-noise_ratio, noise_ratio)
#     noise_wire_feed = np.random.normal(-0.01, 0.01)
#
#     current = round(base_lines[0] + base_lines[0] * noise_current, 1)
#     voltage = round(base_lines[1] + base_lines[1] * (noise_voltage + noise_current), 1)
#     wire_feed = round(base_lines[2] + base_lines[2] * (noise_wire_feed + noise_current), 1)
#
#     return np.array([current, voltage, wire_feed])


def onehot_GTAW_labels(_data, _label_list):
    n_data = len(_data)
    n_label = len(_label_list)
    onehot = np.zeros((n_data, n_label))

    for i in range(n_data):
        for j in range(n_label):
            if _data[i].label == _label_list[j]:
                onehot[i, j] = 1.0
                break

    return np.array(onehot)

# def convert_to_LSTM_input(_data):
#     n_data = len(_data)
#
#     max_len = 0
#     for e in _data:
#         if max_len < len(e.data):
#             max_len = len(e.data)
#
#     LSTM_input = np.zeros((n_data, max_len, 3))
#
#     for i in range(len(_data)):
#         for j in range(len(_data[i].data)):
#             for k in range(3):
#                 LSTM_input[i, j, k] = _data[i].data[j][k]
#
#     return LSTM_input
