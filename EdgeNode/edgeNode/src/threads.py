from threading import Thread
from pymodbus.client.sync import ModbusTcpClient
import pymodbus.exceptions as pme
import time
import FaDAm as fd
from datetime import datetime

import socketio
import socketio.exceptions as sioe
import os
import errno


class CustomThread(Thread):
    clock_time = 0.1
    FLAG_PAUSE = False
    FLAG_KILL = False

    def __init__(self):
        Thread.__init__(self)
        self.base_time = time.time()

    def deep_sync(self, clock):
        distance = (time.time() - self.base_time) // clock
        while True:
            after = (time.time() - self.base_time) // clock
            if after == distance + 1:
                break
            else:
                time.sleep(clock / 100)

    def sync(self):
        self.deep_sync(self.clock_time)

    def pause(self):
        self.FLAG_PAUSE = True

    def resume(self):
        self.FLAG_PAUSE = False

    def kill(self):
        self.FLAG_KILL = True


class SendCurrentStatusThread(CustomThread):

    def __init__(self, send_current_stats_func):
        super().__init__()
        self.func = send_current_stats_func
        self.clock_time = 1

    def set_clock_time(self, speed):
        print("Clock Time Change : ", speed)
        self.clock_time = speed

    def run(self):
        while not self.FLAG_KILL:
            self.sync()
            print("FUNC")
            self.func()
            while self.FLAG_PAUSE:
                time.sleep(0.1)


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
    return data.process_id, file_path


class SendDataSetThread(CustomThread):
    def __init__(self, edge_node):
        super().__init__()
        self.edge_node = edge_node

    def send_data_set(self):
        pid, file_path = save_data(self.edge_node.done_data_set, self.edge_node.path)
        self.edge_node.log_plc("파일이 저장되었습니다 (" + file_path +")")
        self.edge_node.done_data_set = None
        self.edge_node.send_data_set(pid, file_path)

    def run(self):
        while not self.FLAG_KILL:
            time.sleep(0.5)
            if self.edge_node.done_data_set is not None:
                self.send_data_set()

            while self.FLAG_PAUSE:
                time.sleep(0.1)


class ReadPlcThread(CustomThread):

    init_current = 8.0
    init_voltage = 0.0
    init_wire_feed = 0.0

    def __init__(self, data):
        super().__init__()
        self.data = data
        self.clock_time = 0.1

    def connect_plc(self):
        self.data.plc_client = ModbusTcpClient(self.data.plc_address, port=self.data.plc_port)
        if self.data.plc_client.connect():
            self.data.set_FLAG_PLC_CONNECTION(True)
            self.data.log_plc("PLC 연결 성공")
            
    def disconnect_plc(self):
        self.data.plc_client.close()
        self.data.plc_client = None

    def read_plc(self):
        self.sync()
        when = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        try:
            read_data = self.data.plc_client.read_holding_registers(0, 3)
            self.data.set_FLAG_PLC_CONNECTION(True)
            if read_data.isError():
                self.data.log_plc("Data Read Error")
                return when, [None, None, None]
            else:
                cur = read_data.registers[0]/100
                vol = read_data.registers[1]/100
                wir = read_data.registers[2]/100

                return when, [cur, vol, wir]
        except pme.ConnectionException:
            self.data.log_plc("PLC Connection Error")
            self.data.set_FLAG_PLC_CONNECTION(False)
            return when, [None, None, None]

    def add_data_to_data_set(self):
        self.data.data_set.append_data(self.data.current_data, self.data.current_time)

    def check_current_data(self):
        if self.data.current_data[0] is None:
            return None
        elif self.data.current_data[0] >= self.init_current and self.data.current_data[1] >= self.init_voltage and \
                self.data.current_data[2] >= self.init_wire_feed:
            return True
        else:
            return False

    def run(self):
        self.connect_plc()

        while not self.FLAG_KILL:
            self.data.current_time, self.data.current_data = self.read_plc()
            # print("*************************************")
            # print("time : ", self.data.current_data[0])
            # print("curr : ", self.data.current_data[1])
            # print("volt : ", self.data.current_data[2])
            # print("wire : ", self.data.current_data[3])

            is_welding_data = self.check_current_data()

            if self.data.FLAG_WELDING:
                if is_welding_data is not False:
                    self.add_data_to_data_set()
                else:
                    self.data.log_plc("용접이 끝났습니다.")
                    self.data.set_FLAG_WELDING(False)
                    self.data.PID += 1
                    self.data.done_data_set = self.data.data_set
                    self.data.data_set = None

            else:
                if is_welding_data is True:
                    self.data.data_set = fd.GTAW.GTAW_data()
                    self.data.data_set.process_id = self.data.PID
                    self.data.log_plc("용접이 시작되었습니다.")
                    self.data.set_FLAG_WELDING(True)

            while self.FLAG_PAUSE:
                time.sleep(0.1)
        self.disconnect_plc()
