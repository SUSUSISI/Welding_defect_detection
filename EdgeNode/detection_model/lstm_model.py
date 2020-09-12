import welding_machine as wm
from matplotlib import pyplot as plt
import seaborn as sb
import random as rd
import FaDAm as fd
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from joblib import dump, load


from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Dense
from tensorflow.keras.layers import Dropout
from tensorflow.keras.layers import LSTM
from tensorflow.keras.utils import to_categorical


x_path = "data/x_data.csv"

find_data_path = "data/defect_find/"
classification_data_path = 'data/defect_classification/'
scaler_path = "data/std_scaler.bin"

current_file_name = '_current_data.csv'
voltage_file_name = '_voltage_data.csv'
wire_feed_file_name = '_wire_feed_data.csv'
y_file_name = "_y_data.csv"

n_time_steps = 128  # 0.1초 data * 100 = 10초
n_features = 3  # current, voltage, wire_feed
padding = 50  # 앞 뒤로 5초 데이터 버림.
is_defect_accuracy = 0.5


def test_accuracy_find(num=100, duration=None):
    m = wm.WeldingMachine('test', 0.8)
    find_model = load_model(find_data_path + 'model')
    classification_model = load_model(classification_data_path + 'model')
    find_error_count = 0
    classification_num = 0
    classification_error_count = 0

    for i in range(num):
        if duration is None:
            duration = rd.randint(600, 3600)
        x_data, _, _ = m.generate_welding_data(duration)
        y_data = x_data.label
        data = x_data.data
        pre_worked_data = pre_work_data(data)
        predict_list, defect_list = find_defect(pre_worked_data, find_model)
        expected = 0
        if y_data != 'normal':
            expected = 1

        if len(defect_list) != expected:
            print("Expected_count : ", expected)
            print("predicted_count : ", len(defect_list))
            # fd.GTAW.save_welding_data(x_data, find_data_path+"error_case/"+str(i)+".csv")
            fd.GTAW.save_welding_data(x_data, "data/test_error/find/" + str(i) + ".csv")
            find_error_count += 1

        if len(defect_list) == 1 and expected == 1:
            kind = 0
            classification_num += 1
            if y_data == 'porosity':
                kind = 1
            elif y_data == 'undercut':
                kind = 2
            elif y_data == 'undercurrent':
                kind = 3
            elif y_data == 'machanical':
                kind = 4
            percentage = classify_defect(pre_worked_data[defect_list[0][0]:defect_list[0][1] + 1],
                                         classification_model)
            predicted = percentage.argmax()
            if kind != predicted:
                print("Expected_kind : ", kind)
                print("Predicted_kind : ", predicted)
                # fd.GTAW.save_welding_data(x_data, classification_data_path + "error_case/" + str(i) + ".csv")
                fd.GTAW.save_welding_data(x_data, "data/test_error/class/" + str(i) + ".csv")
                classification_error_count += 1

    print("Total : ", num)
    print("Find_Error : ", find_error_count)
    print("Find_Accuracy : ", (1 - find_error_count/num)*100)
    print("Classification_Num : ", classification_num)
    print("Classification_Error : ", classification_error_count)
    print("Classification_Accuracy : ", (1 - classification_error_count/classification_num)*100)


def load_scaler():
    return load(scaler_path)


def save_scaler(scaler):
    dump(scaler, scaler_path, compress=True)

def generate_x_data():
    tm = wm.WeldingMachine("test", 0.8)
    duration = rd.randint(600, 3600)
    x_data, _, _ = tm.generate_welding_data(duration)
    print(x_data.label)
    fd.GTAW.save_welding_data(x_data, x_path)


def show_data(path, name="Welding data"):
    plt.figure(name)
    data = fd.GTAW.read_GTAW_welding_data(path)
    x_data = data.data
    plt.clf()
    plt.plot(x_data)
    plt.legend(['Current', 'Voltage', "Wire_feed"])
    plt.xlabel('Time (0.1 sec)')
    plt.title(name)
    plt.show()


def show_data_a(x_data, name="Welding data"):
    plt.figure(name)
    plt.clf()
    plt.plot(x_data)
    plt.legend(['Current', 'Voltage', "Wire_feed"])
    plt.xlabel('Time (0.1 sec)')
    plt.title(name)
    plt.show()


def show_predict_data(x_data, defect_position_list=[]):
    plt.figure('Welding data')
    plt.clf()
    plt.plot(x_data)
    plt.legend(['Current', 'Voltage', "Wire_feed"])
    plt.xlabel('Time (0.1 sec)')

    y_pos = 150
    for i in defect_position_list:
        x, y = [i[0], i[1]], [y_pos, y_pos]
        plt.plot(x, y, marker='o')

    plt.title('Welding data')
    plt.show()


def cut_padding(data, defect_init, defect_end):
    length = data.shape[0]
    data = np.array(data[padding:length - padding])
    defect_init -= padding
    defect_end -= padding

    return data, defect_init, defect_end


def generate_data(num=500, duration=60, is_find=False):
    x_reshaped_data = []
    y_data = []
    m = wm.WeldingMachine("test", 1)
    sc = load_scaler()

    for i in range(num):
        data, defect_init, defect_end = m.generate_welding_data(duration)
        label = data.label
        data = data.data
        data, defect_init, defect_end = cut_padding(data, defect_init, defect_end)  # cut padding
        data = sc.transform(data)
        re_data = reshape_data(data)
        x_reshaped_data = x_reshaped_data + re_data

        y_data = y_data + get_y_data(re_data, label, defect_init, defect_end, is_find)

    x_reshaped_data = np.array(x_reshaped_data)
    y_data = np.array(y_data)

    return x_reshaped_data, y_data


def generate_scaler(num=10):
    tm = wm.WeldingMachine('test', 0.2)
    x_data = []

    for i in range(num):
        duration = rd.randint(600, 3600)
        data = tm.generate_welding_data(duration)[0]
        data = data.data
        length = data.shape[0]
        data = data[padding:length - padding]  # cut padding
        x_data = x_data + data.tolist()

    x_data = np.array(x_data)
    sc = StandardScaler()
    sc = sc.fit(x_data)
    save_scaler(sc)

    return sc


def convert_original_defect_position(defect_list):
    block = int(n_time_steps / 2)
    defect_position = []

    for i in defect_list:
        temp = [0, 0]
        temp[0] = block * i[0] + 50
        temp[1] = block * i[1] + block + 49
        defect_position.append(temp)

    return defect_position


def pre_work_data(data):
    scaler = load_scaler()
    length = data.shape[0]
    cut_data = np.array(data[padding:length - padding])
    scaler_data = scaler.transform(cut_data)
    re_data = reshape_data(scaler_data)

    return np.array(re_data)


def show_data_distribution(path=x_path):
    data_frame = fd.GTAW.read_GTAW_welding_data(path)
    data = data_frame.data
    length = data.shape[0]
    cut_data = np.array(data[padding:length - padding])
    tp_data = np.transpose(cut_data)

    cmap = plt.get_cmap("tab10")

    show_data_a(cut_data, "Welding Data")

    plt.figure("Current Distribution")
    plt.clf()
    sb.kdeplot(tp_data[0], color=cmap(0))
    plt.legend(['Current'])
    # plt.ylim(-10, 10)
    plt.xlabel('current')
    plt.title("Current Distribution")
    plt.show()

    plt.figure("Voltage Distribution")
    plt.clf()
    sb.kdeplot(tp_data[1], color=cmap(1))
    plt.legend(['Voltage'])
    # plt.ylim(-10, 10)
    plt.xlabel('voltage')
    plt.title("Voltage Distribution")
    plt.show()

    plt.figure("Wire Feed Distribution")
    plt.clf()
    sb.kdeplot(tp_data[2], color=cmap(2))
    plt.legend(['Wire Feed'])
    # plt.ylim(-10, 10)
    plt.xlabel('wire feed')
    plt.title("Wire Feed Distribution")
    plt.show()



def compare_scaled_data(path=x_path):
    data_frame = fd.GTAW.read_GTAW_welding_data(path)
    data = data_frame.data
    scaler = load_scaler()
    length = data.shape[0]
    cut_data = np.array(data[padding:length - padding])
    show_data_a(cut_data, "Original Data")
    scaler_data = scaler.transform(cut_data)
    split_data = np.split(scaler_data, 3, axis=1)

    cmap = plt.get_cmap("tab10")

    plt.figure("Scale Data ( Current )")
    plt.clf()
    plt.plot(split_data[0])
    plt.legend(['Current'])
    plt.ylim(-10, 10)
    plt.xlabel('Time (0.1 sec)')
    plt.title("Scale Data ( Current )")
    plt.show()

    plt.figure("Scale Data ( Voltage )")
    plt.clf()
    plt.plot(split_data[1], color=cmap(1))
    plt.ylim(-10, 10)
    plt.legend(['Voltage'])
    plt.xlabel('Time (0.1 sec)')
    plt.title("Scale Data ( Voltage )")
    plt.show()

    plt.figure("Scale Data ( Wire Feed )")
    plt.clf()
    plt.plot(split_data[2], color=cmap(2))
    plt.ylim(-10, 10)
    plt.legend(['Wire Feed'])
    plt.xlabel('Time (0.1 sec)')
    plt.title("Scale Data ( Wire Feed )")
    plt.show()


def predict_welding_data_set(path=x_path):
    find_model = load_model(find_data_path + 'model')

    data_frame = fd.GTAW.read_GTAW_welding_data(path)
    data = data_frame.data
    pre_worked_data = pre_work_data(data)

    predict_list, defect_list = find_defect(pre_worked_data, find_model, is_defect_accuracy)
    defect_position = convert_original_defect_position(defect_list)
    show_predict_data(data, defect_position)

    result = []

    if len(defect_list) != 0:
        classification_model = load_model(classification_data_path + 'model')
        for i in range(len(defect_list)):
            percentage = classify_defect(pre_worked_data[defect_list[i][0]:defect_list[i][1]+1], classification_model)
            result.append({'kind': percentage.argmax(),
                           'section': [defect_position[i][0], defect_position[i][1]],
                           'percentage': percentage})

    return result
    # 1. data 에 결함이 있는지 확인
    # 2. data 에 결함이 있다고 확인이 된 부분이 어떤결함인지 확인


def classify_defect(data, model):
    predict_list = model.predict(data)
    return np.mean(predict_list, axis=0)


def find_defect(data, model, accuracy=is_defect_accuracy):
    defect_list = []
    predict_list = model.predict(data)

    defect = [None, None]

    for i in range(predict_list.shape[0]):
        if predict_list[i][1] >= accuracy:
            if defect[0] is None:
                defect[0] = i
        else:
            if defect[0] is not None:
                defect[1] = i - 1
                defect_list.append(defect)
                defect = [None, None]

    if defect[0] is not None:
        defect[1] = predict_list.shape[0]-1
        defect_list.append(defect)

    return predict_list, defect_list


def save_x_data(x_data):
    data_frame = fd.GTAW.GTAW_data()
    data_frame.data = x_data
    fd.GTAW.save_welding_data(data_frame, x_path)


def read_x_data():
    data_frame = fd.GTAW.read_GTAW_welding_data(x_path)
    return data_frame.data


def save_y_data(y_data, path):
    pd.DataFrame(y_data).to_csv(path, index=False, header=False, sep=' ')


def save_LSTM_data(x_reshaped_data, y_data, base_path, prefix=''):
    x_data_list = np.dsplit(x_reshaped_data, 3)
    pd.DataFrame(x_data_list[0].reshape((-1, 128))).to_csv(base_path + prefix + current_file_name, index=False,
                                                           header=False, sep=' ')
    pd.DataFrame(x_data_list[1].reshape((-1, 128))).to_csv(base_path + prefix + voltage_file_name, index=False,
                                                           header=False, sep=' ')
    pd.DataFrame(x_data_list[2].reshape((-1, 128))).to_csv(base_path + prefix + wire_feed_file_name, index=False,
                                                           header=False, sep=' ')
    save_y_data(y_data, base_path + prefix + y_file_name)


def load_LSTM_data(base_path, prefix=''):
    x_LSTM_data = list()
    x_LSTM_data.append(load_file(base_path + prefix + current_file_name))
    x_LSTM_data.append(load_file(base_path + prefix + voltage_file_name))
    x_LSTM_data.append(load_file(base_path + prefix + wire_feed_file_name))
    x_LSTM_data = np.dstack(x_LSTM_data)

    y_data = load_file(base_path + prefix + y_file_name)

    return x_LSTM_data, y_data


def load_file(file_path):
    data_frame = pd.read_csv(file_path, header=None, delim_whitespace=True)
    return data_frame.values


# fit and evaluate a model
def build_model(train_x, train_y, test_x, test_y):
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
    print('accuracy : %.3f' % (accuracy * 100.0))

    return model


def generate_model(data_path):
    train_x, train_y = load_LSTM_data(data_path, 'train')
    test_x, test_y = load_LSTM_data(data_path, 'test')

    train_y = to_categorical(train_y)
    test_y = to_categorical(test_y)
    model = build_model(train_x, train_y, test_x, test_y)
    model.save(data_path + 'model')
    return model


# normal = 0
# porosity = 1
# undercut = 2
# undercurrent = 3
# mechanical = 4


def get_y_data(x_data, label, defect_init, defect_end, flag=False):
    y_data = [0 for i in range(len(x_data))]
    defect_label = 0
    if flag:
        defect_label = 1
    else:
        if label == 'porosity':
            defect_label = 1
        elif label == 'undercut':
            defect_label = 2
        elif label == 'undercurrent':
            defect_label = 3
        elif label == 'machanical':
            defect_label = 4

    jump = int(n_time_steps / 2)
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

    return y_data


def reshape_data(data):
    current_pos = 0
    length = data.shape[0]
    new_data = []
    while current_pos + n_time_steps <= length:
        new_data.append(data[current_pos:current_pos + n_time_steps])
        current_pos += int(n_time_steps / 2)
    new_data.append(data[length - n_time_steps:length])
    return new_data
