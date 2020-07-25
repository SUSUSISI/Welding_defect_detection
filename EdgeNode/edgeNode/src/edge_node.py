from pymodbus.client.sync import ModbusTcpClient
import threading
import time
import threads
from datetime import datetime


class EdgeNodeData:
    data_set = None
    PID = 1
    FLAG_WELDING = False
    current_data = None


class EdgeNode:

    def __init__(self):
        self.data = EdgeNodeData
        self.__read_plc_thread = threads.ReadPlcThread(self.data)
        self.__send_server_thread = None
        self.__wait_request_thread = None

        self.base_time = time.time()

    def sleep(self, sec):
        distance = (time.time() - self.base_time) // sec
        while True:
            after = (time.time() - self.base_time) // sec
            if after == distance + 1:
                break
            else:
                time.sleep(sec/100)

    def connect_plc(self):
        self.client = ModbusTcpClient(self.plc_address, port=self.plc_port)
        self.client.connect()

    def disconnect_plc(self):
        self.client.close()
        self.client = None

    def __read_plc_thread_func(self):
        self.connect_plc()
        while True:
            data = self.read_plc()


    def read_plc(self):
        self.sleep(self.read_time)
        when = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        data = self.client.read_holding_registers(0, 3)
        if data.isError():
            print("data read error!!")
            return [when, None, None, None]
        else:
            return [when, data.registers[0], data.registers[1], data.registers[2]]

    def run(self):
        self.__read_plc_thread = threading.Thread(target=a, )


def a():
    return 1

