import welding_machine as wm
from matplotlib import pyplot as plt


m = wm.WeldingMachine("test", 0.1)


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
