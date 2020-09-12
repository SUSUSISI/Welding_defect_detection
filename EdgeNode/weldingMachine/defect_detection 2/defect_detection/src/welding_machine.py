import errno
import os

import FaDAm as fd
from datetime import datetime
import random as rd
import numpy as np
import normal_data_generator
import mechanical_error_data_generator
import porosity_data_generator
import undercurrent_data_generator
import undercut_data_generator
import threading
import time
from pymodbus.client.sync import ModbusTcpClient
from matplotlib import pyplot as plt


class WeldingMachine:
    base_current = 260
    base_voltage = 30
    base_wire_feed = 8.1

    init_current = 8.0
    init_voltage = 0.0
    init_wire_feed = 0.0

    process_id = 1

    current_data = None
    next_data = None

    port_current = None
    port_voltage = None
    port_wire_feed = None

    address = '172.30.1.20'
    port = 5020
    client = None
    sleep_time = 0.1

    def __init__(self, name, error_rate, address=None, port=None):
        self.name = name
        self.error_rate = error_rate
        self.path = "data/" + self.name + "_" + datetime.now().strftime('%Y_%m_%d_%H%M%S') + "/"
        self.base_time = time.time()
        if address is not None:
            self.address = address
        if port is not None:
            self.port = port

    def set_base(self, current, voltage, wire_feed):
        self.base_current = current
        self.base_voltage = voltage
        self.base_wire_feed = wire_feed

    def set_init(self, current, voltage, wire_feed):
        self.init_current = current
        self.init_voltage = voltage
        self.init_wire_feed = wire_feed

    def warm_up(self):
        self.generate_next_data()
        self.current_data = self.next_data

    def set_port(self, port_current, port_voltage, port_wire_feed):
        self.port_current = port_current
        self.port_voltage = port_voltage
        self.port_wire_feed = port_wire_feed

    def send_data(self, data):
        send_current = int(data[0] * 100)
        send_voltage = int(data[1] * 100)
        send_wire_feed = int(data[2] * 100)

        self.sleep()
        self.client.write_registers(0, [send_current, send_voltage, send_wire_feed])
        # print("-----------------------------------------------")
        # print(datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'))
        # print("current : ", send_current)
        # print("voltage : ", send_voltage)
        # print("wire_feed : ", send_wire_feed)
        # print("-----------------------------------------------")

    def sleep(self):
        distance = (time.time() - self.base_time) // self.sleep_time
        while True:
            after = (time.time() - self.base_time) // self.sleep_time
            if after == distance + 1:
                break
            else:
                time.sleep(0.001)

    def run(self):
        self.warm_up()
        gen_thread = threading.Thread(target=self.generate_welding_data, args=())
        self.client = ModbusTcpClient(self.address, port=self.port)
        self.client.connect()

        while True:

            intermission = rd.randint(10, 100)
            for i in range(intermission):
                curr = abs(np.random.normal(0, 1)) % self.init_current
                volt = 0.0
                wire = 0.0
                self.send_data([curr, volt, wire])

            self.generate_next_data()
            # self.current_data.time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
            self.current_data.process_id = self.process_id

            # save_thread = threading.Thread(target=save_data, args=(self.current_data, self.path))
            # save_thread.start()

            log("용접시작")
            log(self.current_data.label)
            for i in self.current_data.data:
                self.send_data(i)
            log("용접 끝")
            self.current_data = self.next_data

        self.client.close()

    def set_port_name(self, port):
        self.port = port

    def generate_normal_data(self, duration):
        return normal_data_generator.generate(self.base_current, self.base_voltage, self.base_wire_feed,
                                              self.init_current, self.init_voltage, self.init_wire_feed, duration)

    def generate_mechanical_data(self, duration):
        return mechanical_error_data_generator.generate(self.base_current, self.base_voltage,
                                                        self.base_wire_feed,
                                                        self.init_current, self.init_voltage,
                                                        self.init_wire_feed,
                                                        duration)

    def generate_porosity_data(self, duration):
        return porosity_data_generator.generate(self.base_current, self.base_voltage, self.base_wire_feed,
                                                self.init_current, self.init_voltage, self.init_wire_feed,
                                                duration)

    def generate_undercut_data(self, duration):
        return undercut_data_generator.generate(self.base_current, self.base_voltage, self.base_wire_feed,
                                                self.init_current, self.init_voltage, self.init_wire_feed,
                                                duration)

    def generate_undercurrent_data(self, duration):
        return undercurrent_data_generator.generate(self.base_current, self.base_voltage, self.base_wire_feed,
                                                    self.init_current, self.init_voltage, self.init_wire_feed,
                                                    duration)

    def generate_next_data(self):
        self.next_data = self.generate_welding_data(60)

    def generate_welding_data(self, duration=None):
        if duration is None:
            duration = rd.randint(600, 3600)

        if rd.random() >= self.error_rate:
            return self.generate_normal_data(duration)
        else:
            error_case = rd.randint(1, 4)
            if error_case == 1:
                return self.generate_mechanical_data(duration)
            elif error_case == 2:
                return self.generate_porosity_data(duration)
            elif error_case == 3:
                return self.generate_undercut_data(duration)
            elif error_case == 4:
                return self.generate_undercurrent_data(duration)


def save_data(data, path):
    print(path)
    try:
        if not (os.path.isdir(path)):
            os.makedirs(path)

    except OSError as e:
        if e.errno != errno.EEXIST:
            print("Failed to create directory!!!!!")
            raise

    file_path = path + "process_" + str(data.process_id) + ".csv"
    fd.GTAW.save_welding_data(data, file_path)


def log(msg):
    print(datetime.now().strftime('[%Y-%m-%d %H:%M:%S.%f]: '), msg)


if __name__ == "__main__":
    test = WeldingMachine("one", 0.8, '192.168.1.105', 5020)
    test.run()
