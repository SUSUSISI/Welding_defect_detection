import welding_machine as wm
from matplotlib import pyplot as plt
import random as rd
import FaDAm as fd
from numpy import mean
from numpy import std
import numpy as np
import pandas as pd
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.layers import Flatten
from tensorflow.keras.layers import Dropout
from tensorflow.keras.layers import LSTM
from keras.utils import to_categorical
m = wm.WeldingMachine("test", 1)

x_path = "data/x_data.csv"

base_path = "data/"

current_file_name = '_current_data.csv'
voltage_file_name = '_voltage_data.csv'
wire_feed_file_name = '_wire_feed_data.csv'
y_file_name = "_y_data.csv"

n_time_steps = 128  # 0.1초 data * 100 = 10초
n_features = 3  # current, voltage, wire_feed


def show_data(data):
    plt.figure('Welding data')
    plt.clf()
    plt.plot(data)
    plt.legend(['Current', 'Voltage', "Wire_feed"])
    plt.xlabel('Time (0.1 sec)')
    plt.title('Welding data')
    plt.show()


def cut_padding(data, defect_init, defect_end):
    length = data.shape[0]
    data = np.array(data[50:length-50])
    defect_init -= 50
    defect_end -= 50

    return data, defect_init, defect_end


def generate_data(num=500, duration=60):
    x_reshaped_data = []
    y_data = []
    for i in range(num):
        data, defect_init, defect_end = m.generate_welding_data(duration)
        label = data.label
        data = data.data
        data, defect_init, defect_end = cut_padding(data, defect_init, defect_end)   # cut padding
        # show_data(data)
        # print(defect_init, ", ", defect_end)
        re_data = reshape_data(data)
        x_reshaped_data = x_reshaped_data + re_data
        y_data = y_data + get_y_data(re_data, label, defect_init, defect_end)

    print("0 : ", y_data.count(1))
    print("1 : ", y_data.count(2))
    print("2 : ", y_data.count(3))
    print("3 : ", y_data.count(4))
    print("4 : ", y_data.count(5))
    # print("5 : ", y_data.count(5))
    # print("6 : ", y_data.count(6))

    x_reshaped_data = np.array(x_reshaped_data)
    y_data = np.array(y_data)
    y_data = y_data - 1  # cut padding

    return x_reshaped_data, y_data


def predict_welding_data_set(path):
    data_frame = fd.GTAW.read_GTAW_welding_data(path)
    data = data_frame.data
    length = data.shape[0]
    data = np.array(data[50:length - 50])
    # 1. data 에 결함이 있는지 확인
    # 2. data 에 결함이 있다고 확인이 된 부분이 어떤결함인지 확인

    x_reshaped_data = reshape_data(data)


def find_defect(data, model):
    # predict_list = model.pridect(data)
    predict_list = load_file()

def save_x_data(x_data):
    data_frame = fd.GTAW.GTAW_data()
    data_frame.data = x_data
    fd.GTAW.save_welding_data(data_frame, x_path)


def read_x_data():
    data_frame = fd.GTAW.read_GTAW_welding_data(x_path)
    return data_frame.data


def save_y_data(y_data, path):
    pd.DataFrame(y_data).to_csv(path, index=False, header=False, sep=' ')


def save_LSTM_data(x_reshaped_data, y_data, prefix=''):
    x_data_list = np.dsplit(x_reshaped_data, 3)
    pd.DataFrame(x_data_list[0].reshape((-1, 128))).to_csv(base_path+prefix+current_file_name, index=False, header=False, sep=' ')
    pd.DataFrame(x_data_list[1].reshape((-1, 128))).to_csv(base_path+prefix+voltage_file_name, index=False, header=False, sep=' ')
    pd.DataFrame(x_data_list[2].reshape((-1, 128))).to_csv(base_path+prefix+wire_feed_file_name, index=False, header=False, sep=' ')
    save_y_data(y_data, base_path+prefix+y_file_name)


def load_LSTM_data(prefix=''):
    x_LSTM_data = list()
    x_LSTM_data.append(load_file(base_path+prefix+current_file_name))
    x_LSTM_data.append(load_file(base_path+prefix+voltage_file_name))
    x_LSTM_data.append(load_file(base_path+prefix+wire_feed_file_name))
    x_LSTM_data = np.dstack(x_LSTM_data)

    y_data = load_file(base_path+prefix+y_file_name)

    return x_LSTM_data, y_data


def load_file(file_path):
    data_frame = pd.read_csv(file_path, header=None, delim_whitespace=True)
    return data_frame.values


# fit and evaluate a model
def evaluate_model(train_x, train_y, test_x, test_y):
    verbose, epochs, batch_size = 0, 15, 64
    n_timesteps, n_features, n_outputs = train_x.shape[1], train_x.shape[2], train_y.shape[1]
    model = Sequential()
    model.add(LSTM(100, input_shape=(n_timesteps, n_features)))
    model.add(Dropout(0.5))
    model.add(Dense(100, activation='relu'))
    model.add(Dense(n_outputs, activation='softmax'))
    model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])
    # fit network
    model.fit(train_x, train_y, epochs=epochs, batch_size=batch_size, verbose=verbose)

    # evaluate model
    _, accuracy = model.evaluate(test_x, test_y, batch_size=batch_size, verbose=verbose)
    return accuracy


def make_model(train_x, train_y):
    verbose, epochs, batch_size = 0, 15, 64
    n_timesteps, n_features, n_outputs = train_x.shape[1], train_x.shape[2], train_y.shape[1]
    model = Sequential()
    model.add(LSTM(100, input_shape=(n_timesteps, n_features)))
    model.add(Dropout(0.5))
    model.add(Dense(100, activation='relu'))
    model.add(Dense(n_outputs, activation='softmax'))
    model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])
    # fit network
    model.fit(train_x, train_y, epochs=epochs, batch_size=batch_size, verbose=verbose)
    return model


# summarize scores
def summarize_results(scores):
    print(scores)
    m, s = mean(scores), std(scores)
    print('Accuracy: %.3f%% (+/-%.3f)' % (m, s))


# run an experiment
def run_experiment(repeats=10):
    # load data
    train_x, train_y = load_LSTM_data('train')
    test_x, test_y = load_LSTM_data('test')

    train_y = to_categorical(train_y)
    test_y = to_categorical(test_y)

    # repeat experiment
    scores = list()
    for r in range(repeats):
        score = evaluate_model(train_x, train_y, test_x, test_y)
        score = score * 100.0
        print('>#%d: %.3f' % (r + 1, score))
        scores.append(score)
    # summarize results
    summarize_results(scores)








# def read_data():
#     x_data = []
#

# begin = 0
# normal = 1
# porosity = 2
# undercut = 3
# undercurrent = 4
# mechanical = 5
# end = 6



def get_y_data(x_data, label, defect_init, defect_end):
    y_data = [1 for i in range(len(x_data))]
        
    if label != "normal":
        defect_label = -1
        if label == 'porosity':
            defect_label = 2
        elif label == 'undercut':
            defect_label = 3
        elif label == 'undercurrent':
            defect_label = 4
        elif label == 'machanical':
            defect_label = 5

        jump = int(n_time_steps/2)
        start_pos = int(defect_init / jump)
        end_pos = int(defect_end / jump)

        if end_pos == start_pos:
            if start_pos != 0:
                start_pos = start_pos - 1
            if end_pos < len(x_data):
                end_pos = end_pos + 1

        for i in range(start_pos, end_pos):
            if 0 <= i < len(y_data):
                y_data[i] = defect_label

    # cut padding
    # y_data[0] = 0
    # y_data[-1] = 6

    return y_data


def reshape_data(data):
    current_pos = 0
    length = data.shape[0]
    new_data = []
    while current_pos + n_time_steps <= length:
        new_data.append(data[current_pos:current_pos+n_time_steps])
        current_pos += int(n_time_steps / 2)
    new_data.append(data[length-n_time_steps:length])
    return new_data

