from pymodbus.server.sync import StartTcpServer
from pymodbus.datastore.context import *


def run_server(address=None, port=None):
    plc_address = '172.30.1.20'
    plc_port = 5020

    if address is not None:
        plc_address = address
    if port is not None:
        plc_port = port


    store = ModbusSlaveContext(
        di=ModbusSequentialDataBlock(0, [17] * 100),
        co=ModbusSequentialDataBlock(0, [17] * 100),
        hr=ModbusSequentialDataBlock(0, [17] * 100),
        ir=ModbusSequentialDataBlock(0, [17] * 100))

    print("PLC Server ON : ", plc_address, " / ", plc_port)
    context = ModbusServerContext(slaves=store, single=True)
    StartTcpServer(context, address=(plc_address, plc_port))


if __name__ == '__main__':
    run_server('192.168.1.104', 5020)
