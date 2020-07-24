from pymodbus.client.sync import ModbusTcpClient
import threading
import time
from datetime import datetime

class EdgeNode:
    plc_address = '172.30.1.31'
    plc_port = 5020
    server_address = ''
    send_time = 1
    read_time = 0.1
    client = None
    dataSet = None
    current_data = None

    init_current = 8.0
    init_voltage = 0.0
    init_wire_feed = 0.0

    __read_plc_thread = None
    __send_server_thread = None
    __wait_request_thread = None

    def __init__(self):
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
        data = self.client.read_holding_registers(0,3)
        if data.isError():
            print("data read error!!")
            return [when, None, None, None]
        else:
            return [when, data.registers[0], data.registers[1], data.registers[2]]

    def run(self):





a = EdgeNode()
print(a.plc_address)
a.plc_address = "111"
print(a.plc_address)
