import welding_machine as wm
from matplotlib import pyplot as plt
import random as rd
import FaDAm as fd

m = wm.WeldingMachine("test", 0.8)
path = "data/test_data.txt"


def save_welding_data(num=100):
    data_list = []
    for i in range(num):
        duration = rd.randint(600, 3600)
        data = m.generate_welding_data(duration)
        data.process_id = i
        data_list.append(data)
        print(i+1, " 번째 생성")

    fd.GTAW.save_GTAW_welding_data_list(data_list, path)


if __name__ == "__main__":
    # save_welding_data(10)
    a = fd.GTAW.read_GTAW_welding_data_list(path)
    print(len(a))


def show_normal(duration=600):
    data = m.generate_normal_data(duration).data
    plt.figure('normal data')
    plt.clf()
    plt.plot(data)
    plt.legend(['Current', 'Voltage', "Wire_feed"])
    plt.xlabel('Time (0.1 sec)')
    plt.title('normal data')
    plt.show()


def show_porosity(duration=600):
    data = m.generate_porosity_data(duration).data
    plt.figure('porosity error data')
    plt.clf()
    plt.plot(data)
    plt.legend(['Current', 'Voltage', "Wire_feed"])
    plt.xlabel('Time (0.1 sec)')
    plt.title('porosity error data')
    plt.show()


def show_undercut(duration=600):
    data = m.generate_undercut_data(duration).data
    plt.figure('undercut error data')
    plt.clf()
    plt.plot(data)
    plt.legend(['Current', 'Voltage', "Wire_feed"])
    plt.xlabel('Time (0.1 sec)')
    plt.title('undercut error data')
    plt.show()


def show_undercurrent(duration=600):
    data = m.generate_undercurrent_data(duration).data
    plt.figure('undercurrent error data')
    plt.clf()
    plt.plot(data)
    plt.legend(['Current', 'Voltage', "Wire_feed"])
    plt.xlabel('Time (0.1 sec)')
    plt.title('under current error data')
    plt.show()


def show_mechanical(duration=600):
    data = m.generate_mechanical_data(duration).data
    plt.figure('mechanical error data')
    plt.clf()
    plt.plot(data)
    plt.legend(['Current', 'Voltage', "Wire_feed"])
    plt.xlabel('Time (0.1 sec)')
    plt.title('mechanical error data')
    plt.show()








