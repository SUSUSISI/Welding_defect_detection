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

    def sync(self):
        distance = (time.time() - self.base_time) // self.clock_time
        while True:
            after = (time.time() - self.base_time) // self.clock_time
            if after == distance + 1:
                break
            else:
                time.sleep(self.clock_time / 100)

    def init_before_run(self):
        self.FLAG_KILL = False
        self.FLAG_PAUSE = False

    def pause(self):
        self.FLAG_PAUSE = True

    def resume(self):
        self.FLAG_PAUSE = False

    def kill(self):
        self.FLAG_KILL = True


class SendCurrentStatusThread(CustomThread):
    def __init__(self, server):
        super().__init__()
        self.server = server
        self.clock_time = 1

    def run(self):
        self.init_before_run()
        while not self.FLAG_KILL:
            self.sync()
            self.server.send_current_status()
            print(datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'))
            while self.FLAG_PAUSE:
                time.sleep(0.1)


class Server(CustomThread):
    sio = socketio.Client()

    def __init__(self, data):
        super().__init__()
        self.data = data

    def kill(self):
        super().kill()
        self.sio.disconnect()

    def run(self):
        self.init_before_run()

        while not self.FLAG_KILL:
            self.sync()
            try:
                # self.sio.connect('http://' + self.data.server_address +
                #                  ":" + self.data.server_port)
                self.sio.connect('http://localhost:5020')
                self.data.set_FLAG_SERVER_CONNECTION(True)
                self.data.write_log("서버와 연결되었습니다.")

            except sioe.SocketIOError:
                self.data.write_log("서버와 연결이 되지 않습니다.")

            while self.FLAG_PAUSE:
                time.sleep(0.1)

    def send_current_status(self):
        print("send current status ")

    def send_data_set(self, file_path):
        print("send data set")

    @sio.event
    def connect_error(self):
        print("Server Connection Error")

        # 그냥 빨간불 파란불만 건드리기 + log

    @sio.event
    def connect(self):
        print("Server Connected")
        # 그냥 빨간불 파란불만 건드리기

    @sio.event
    def disconnect(self):
        print("DisConnected")
        # 그냥 빨간불 파란불만 건드리기


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
    return file_path


class SendDataSetThread(CustomThread):
    def __init__(self, data):
        super().__init__()
        self.data = data
        self.clock_time = 1

    def send_to_server(self):
        file_path = self.save_data_set()
        self.data.server.send_data_set(file_path)

    def save_data_set(self):
        file_path = save_data(self.data.done_data_set, self.data.path)
        self.data.done_data_set = None
        self.data.write_log("DATA SET 저장 (" + file_path + ")")
        return file_path

    def run(self):
        self.init_before_run()
        while not self.FLAG_KILL:
            self.sync()
            if self.data.done_data_set is not None:
                self.send_to_server()

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
            self.data.write_log("PLC 연결 성공")
            
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
                self.data.write_log("Data Read Error")
                return when, [None, None, None]
            else:
                cur = read_data.registers[0]/100
                vol = read_data.registers[1]/100
                wir = read_data.registers[2]/100
                print(cur, ", ", vol, ", ", wir)
                return when, [read_data.registers[0]/100, read_data.registers[1]/100, read_data.registers[2]/100]
        except pme.ConnectionException:
            self.data.write_log("PLC Connection Error")
            self.data.set_FLAG_PLC_CONNECTION(False)
            return when, [None, None, None]

    def add_data_to_data_set(self):
        self.data.data_set.append_data(self.data.current_time, self.data.current_data)

    def check_current_data(self):
        if self.data.current_data[0] is None:
            return None
        elif self.data.current_data[0] >= self.init_current and self.data.current_data[1] >= self.init_voltage and \
                self.data.current_data[2] >= self.init_wire_feed:
            return True
        else:
            return False

    def run(self):
        self.init_before_run()
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
                    self.data.FLAG_WELDING = False
                    self.data.PID += 1
                    self.data.done_data_set = self.data.data_set
                    self.data.data_set = None

            else:
                if is_welding_data is True:
                    self.data.data_set = fd.GTAW.GTAW_data()
                    self.data.data_set.process_id = self.data.PID
                    self.data.FLAG_WELDING = True

            while self.FLAG_PAUSE:
                time.sleep(0.1)
        self.disconnect_plc()
