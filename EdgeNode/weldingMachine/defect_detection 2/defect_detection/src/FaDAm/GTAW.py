import csv
from datetime import datetime, timedelta
import random as rd

import numpy as np

from FaDAm.utility.Errors import *

class GTAW_data:
    def __init__(self, data=None):
        if data == None:
            self.__time = None
            self.__process_id = None
            self.__data = np.zeros([0,3], dtype=np.float32)
            self.__prediction_label = 'null'
            self.__label = 'null'
        else:
            first_row = data[0]
            self.__time = datetime.strptime(first_row[1],'%Y-%m-%d %H:%M:%S.%f')
            self.__process_id = int(first_row[2])
            self.__prediction_label = first_row[6]
            self.__label = first_row[7]
            self.__data = np.zeros([0,3], dtype=np.float32)

            for row in data:
                new_data = np.array([float(e) for e in row[3:6]])
                self.__data = np.concatenate((self.__data, np.array([new_data])))

    def append_data(self, _data):
        if len(_data) == 8:
            new_data = np.array([float(e) for e in _data[3:6]])
        elif len(_data) == 3:
            new_data = np.array([float(e) for e in _data])
        else:
            raise InputError('Length of input must be 8 or 3')

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

    @time.setter
    def time(self, _time):
        if isinstance(_time, str):
            self.__time = datetime.strptime(_time,'%Y-%m-%d %H:%M:%S.%f')
        elif isinstance(_time, datetime):
            self.__time = _time
        else:
            raise InputError('Input type must be datetime or string formated \%Y-\%m-\%d \%H:\%M:\%S.\%f')

    @process_id.setter
    def process_id(self, _process_id):
        self.__process_id = int(_process_id)

    @data.setter
    def data(self, _data):
        self.__data = data

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
        raise InputError('Input data must be list with length 8 which consist of [data_id, date, process_id, avg_curr, avg_volt, avg_wire, prediction, label]')

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

    return data

def write_GTAW_welding_data(data, path):
    file = open(path, 'w', encoding='utf-8', newline='')
    writer = csv.writer(file)
    data_index = 1

    writer.writerow(['Data No.','Date','Process ID','Avg. Current','Avg. Voltage','Avg. Wire Feed','Prediction','Label'])

    for e in data:
        time_delta = timedelta(milliseconds=100)
        time_index = 0

        curr_data = e.data

        for i in curr_data:
            row = [data_index, e.time + (time_delta * time_index), e.process_id, round(i[0], 1), round(i[1], 1), round(i[2], 1), e.prediction_label, e.label]
            writer.writerow(row)

            data_index += 1
            time_index += 1

    file.close()


def save_welding_data(data, path):
    file = open(path, 'w', encoding='utf-8', newline='')
    writer = csv.writer(file)
    data_index = 1

    writer.writerow(
        ['Data No.', 'Date', 'Process ID', 'Avg. Current', 'Avg. Voltage', 'Avg. Wire Feed', 'Prediction', 'Label'])

    time_delta = timedelta(milliseconds=100)
    time_index = 0

    curr_data = data.data

    for i in curr_data:
        row = [data_index, data.time + (time_delta * time_index), data.process_id, round(i[0], 1), round(i[1], 1),
               round(i[2], 1), data.prediction_label, data.label]
        writer.writerow(row)
        data_index += 1
        time_index += 1

    file.close()


def merge_GTAW_datasets(_paths, _target):
    data = []

    for path in _paths:
        file = open(path, 'r', encoding='utf-8')
        reader = csv.reader(file)

        first_row = next(reader)

        if len(first_row) != 8:
            raise InputError('Input data must be list with length 8 which consist of [data_id, date, process_id, avg_curr, avg_volt, avg_wire, prediction, label], file name: {}'.format(path))

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

    write_GTAW_welding_data(data, _target)


def generate_noised_data(base_lines, noise_ratio=0.05):
    noise_current = np.random.normal(-noise_ratio, noise_ratio)
    noise_voltage = np.random.normal(-noise_ratio, noise_ratio)
    noise_wire_feed = np.random.normal(-0.01, 0.01)

    current = round(base_lines[0] + base_lines[0] * noise_current, 1)
    voltage = round(base_lines[1] + base_lines[1] * (noise_voltage + noise_current), 1)
    wire_feed = round(base_lines[2] + base_lines[2] * (noise_wire_feed + noise_current), 1)

    return np.array([current, voltage, wire_feed])

def onehot_GTAW_labels(_data, _label_list):
    n_data = len(_data)
    n_label = len(_label_list)
    onehot = np.zeros((n_data, n_label))

    for i in range(n_data):
        for j in range(n_label):
            if _data[i].label == _label_list[j]:
                onehot[i,j] = 1.0
                break

    return np.array(onehot)

def convert_to_LSTM_input(_data):
    n_data = len(_data)

    max_len = 0
    for e in _data:
        if max_len < len(e.data):
            max_len = len(e.data)

    LSTM_input = np.zeros((n_data, max_len, 3))

    for i in range(len(_data)):
        for j in range(len(_data[i].data)):
            for k in range(3):
                LSTM_input[i, j, k] = _data[i].data[j][k]

    return LSTM_input

if __name__ == '__main__':
    test_data = [
        ['1125','2019-07-10 10:52:12.641639','39','3.5','37.1','1','null','null'],
        ['1126','2019-07-10 10:52:12.842069','39','6.3','64.9','1.1','null','null'],
        ['1127','2019-07-10 10:52:13.040774','39','4','71.6','1','null','null'],
        ['1128','2019-07-10 10:52:13.241955','39','6','73.2','1.1','null','null'],
        ['1129','2019-07-10 10:52:13.436313','39','4.8','73.8','10.3','null','null'],
        ['1130','2019-07-10 10:52:13.636897','39','5.8','44.8','10.3','null','null'],
        ['1131','2019-07-10 10:52:13.842932','39','5','47.3','10.2','null','null'],
        ['1132','2019-07-10 10:52:14.036789','39','114.8','52.4','10.3','null','null'],
        ['1133','2019-07-10 10:52:14.236504','39','153.5','42.9','10.2','null','null'],
        ['1134','2019-07-10 10:52:14.436493','39','198.3','30','0.1','null','null'],
        ['1135','2019-07-10 10:52:14.629026','39','5.8','59.2','0','null','null'],
        ['1136','2019-07-10 10:52:14.827493','39','4.8','37','0.1','null','null'],
        ['1137','2019-07-10 10:52:15.041471','39','6','9.9','0.1','null','null'],
        ['1138','2019-07-10 10:52:15.241847','39','3.8','4','0.1','null','null'],
        ['1139','2019-07-10 10:52:15.436919','39','6.5','2.7','0.1','null','null']
    ]

    print('Start test for GTAW_data class')

    a = GTAW_data(data=test_data)
    a.append_data([1, 2, 3])
    a.append_data([1, 3, 2])
    print(a.data)
    a.time = '2019-07-10 10:52:15.436919'
    print(type(a.time))

    data = read_GTAW_welding_data('../../data/total_data.csv')

    print(len(data))
    for e in data:
        print(e.process_id)

    print('Done.')
