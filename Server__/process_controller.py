#   개발 현황
#   1. 웹에서 노드 등록하는 기능
#   2. 웹에서 노드 삭제하는 기능
#   3. 웹과 서버 사이의 socket.io 연결
#   4. 웹과 서버 사이의 socket.io 연결 해제
#   5. 노드와 서버 사이의 socket.io 연결
#   6. 노드와 서버 사이의 socket.io 연결 해재
#   7. 노드에서 csv파일 전송 시 DB에 저장하는 기능
#   8. 노드에서 실시간 데이터 전송시 웹으로 실시간으로 전송하는 기능 ( 테스트 필요 )
#   ********************************************************************************************************************
#   개발 필요
#   1.

from flask import Flask, jsonify, render_template
from flask import request
from flask_socketio import send, SocketIO, emit, join_room
import pandas as pd
from flask_pymongo import PyMongo
import time

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/welding_defect_dection"
app.config['SESSION_TYPE'] = 'filesystem'
socketio = SocketIO(app)
mongo = PyMongo(app)

welding_db = mongo.db.welding_data
node_db = mongo.db.node_data

# key: Node_ip, value: [Node_id, Node_sid]
connected_nodeList = {}
node_average_data_set_list = {}
node_average_data_set_list["172.20.10.3"] = []

#   형우가 준 데이터 테스트 용
def test_transmit_data():
    # data = pd.read_csv("./test.csv")
    node_ip = 'node_ipp'
    if welding_db.find_one({'node_ip': node_ip}):
        weldingDataFrame = pd.read_csv("./test.csv")
        # 동일 아이피 존재하지는 확인하고 나면, 만들어야지.
        welding_db.find_one_and_update({'node_ip': node_ip},
                                       {'$push': {'processes': {'label': 'temp_label',
                                                                'process_id': int(weldingDataFrame['Process ID'][0]),
                                                                'prediction': [],
                                                                'dataList': []}
                                                  }
                                        })

        for rowData in weldingDataFrame.iterrows():
            welding_db.find_one_and_update({'node_ip': node_ip, 'processes.process_id': 1},
                                           # {'$set': {'processes.$.dataList': 'youwan'}}, upsert=True)
                                           {'$push': {'processes.$.dataList': {"date": rowData[1][1],
                                                                              "current": rowData[1][3],
                                                                              "voltage": rowData[1][4],
                                                                              "wireFeed": rowData[1][5]}}},
                                           upsert=True)

#   ********************************************************************************************************************

#   description(input) : ""
#   speed(default) : 1
#   node_ip : 웹에서 입력하는 node ip
#   node_id : 웹에서 입력하는 node id
#   processes : Array
#   { node_ip : node_sid }
@app.route("/register_node", methods=['POST'])
def register_node():
    if request.method == 'POST':
        print("hello")
        node_name = request.args.get('node_name')
        description = request.args.get('description')
        speed = 1
        # web_ip = request.remote_addr
        node_ip = request.args.get('node_ip')

        # 무조건 등록.
        data = {'node_name': node_name, 'node_ip': node_ip,
                'speed': speed, 'description': description,
                'processes': []}
        welding_db.insert_one(data)
        # 등록 후 체크해서 확인
        if node_ip in connected_nodeList.keys():
            if connected_nodeList[node_ip][0] is None:
                connected_nodeList[node_ip][0] = welding_db.find_one({'node_ip': node_ip})['_id']
            emit('data_request', {"request": True, 'speed': speed}, room=connected_nodeList[node_ip][1])

        return "node register success"

#   노드 삭제할 때, 호출
@app.route("/delete_node", methods=['POST'])
def delete_node():
    node_ip = request.args.get('node_ip')
    welding_db.delete_many({'node_ip': node_ip})

@app.route('/dataSheet_dataTable', methods=['POST'])
def dataSheet_dataTable():
    if request.method == "POST":
        print("dataSheet_dataTable")

        total_data = []
        cursor = welding_db.find()
        # 전체 데이터 전부 가지고 와서 total_data
        for i in range(0, welding_db.count()):
            total_data.append(cursor.next())

        total_arranged_data = []
        # print(total_data)
        for node in total_data:
            print(node)
            for process in node['processes']:
                print(process)
                avg_current = 0.0
                avg_voltage = 0.0
                avg_wireFeed = 0.0
                expected_result = "temp_expected_result"
                real_result = "temp_real_result"
                for data in process['dataList']:
                    print(data)
                    # print(data['current'])
                    avg_current = avg_current + data['current']
                    avg_voltage = avg_voltage + data['voltage']
                    avg_wireFeed = avg_wireFeed + data['wireFeed']
                # print(strnode['_id'])

                total_arranged_data.append({
                    "data_number": process['process_id'],
                    "start_time": process['dataList'][0]['date'],
                    "end_time": process['dataList'][-1]['date'],
                    "sensor_id": str(node['_id']),
                    "avg_current": avg_current,
                    "avg_voltage": avg_voltage,
                    "avg_wire_feed": avg_wireFeed,
                    "expected_result": expected_result,
                    "real_result": real_result
                })

        print(total_arranged_data)

        return jsonify({'data': total_arranged_data})

@app.route("/dataSheet_dataTable_detail", methods=['POST'])
def dataSheet_dataTable_detail():
    if request.method == 'POST':
        print("dataSheet_dataTable_detail")
        data = request.get_json()

        print(data)



#   ********************************************************************************************************************
#   Connect Web
#   웹이 필요한 데이터 보내줘야
@socketio.on("connect", namespace='/web')
def connect():
    print("connected with web", request.sid, request.remote_addr)

    # emit("get_machine_status_data", {'data': {'current': 10.0, "voltage": 10.0, "wire_feed": 10.0}, "message": "node disconnect"})

@socketio.on("disconnect", namespace='/web')
def disconnect():
    print("disconnect Web", request.sid, request.remote_addr)

#   Connection
#   노드와 커넥션되면 connectedNodeList에 노드 정보 저장
#   Welding_DB에 노드정보 있는지 확인하고 유무에 따라 처리.
@socketio.on("connect", namespace='/node')
def connect():
    print("connected node", request.sid, request.remote_addr)
    node_sid = request.sid
    node_ip = request.remote_addr
    node_average_data_set_list[node_ip] = []
    data = welding_db.find_one({'node_ip': '172.20.10.3'})
    if data:
        node_id = data['_id']
        connected_nodeList[node_ip] = [node_id, node_sid]
    else:
        connected_nodeList[node_ip] = [None, node_sid]
    check_registered_node_and_emit(node_ip, node_sid)
    # emit("get_machine_status_data", {'data': {'current': 10.0, "voltage": 10.0, "wire_feed": 10.0}, "message": "node disconnect"}, namespace='\web')

#   Disconnect Node
#   노드와 연결해제되면 connectNodeList에서 제거.
#   웹에 커넥션이 해제됨을 알려줘야함.
@socketio.on("disconnect", namespace='/node')
def disconnect():
    print("disconnect Node", request.sid, request.remote_addr)
    node_ip = request.remote_addr
    connected_nodeList.pop(node_ip)
    print("connected_nodeList : ", connected_nodeList)
    # 여기에다가 추가하세요.

#   check_registered_node_and_emit 함수
#   welding_data( 웹에서 등록한 노드 )에 해당 ip주소가 있는지 파악.
#   *호출 시기*
#   1) 엣지노드 Connection 이 있을때
#   2) 웹에서 엣지노드 등록 할때
#   3) speed 바꿀 때
def check_registered_node_and_emit(ip, sid):
    welding_data = welding_db.find_one({'node_ip': ip})
    if welding_data is None:
        print("welding_data is None")
        emit('data_request', {"request": False, 'speed': 1}, room=sid)
    else:
        print("welding_data is Exist")
        emit('data_request', {"request": True, 'speed': welding_data['speed']}, room=sid)

#   파일 받고 DB에 저장하는 함수.

#   (pd.read_csv(data["data"]))[1] 데이터 형식. 참고 ) [0] --> order number
#   Data No.                                   1 "data_number": 0         0
#   Date              2020-08-08 19:03:27.022213 "date": "2020.02.02"     1
#   Process ID                                 3                          2
#   Avg. Current                          100.83 "avg_current": 1000,     3
#   Avg. Voltage                           17.32 "avg_voltage": 111.1     4
#   Avg. Wire Feed                          4.09 "avg_wireFeed": 1111.1   5
#   Prediction                               NaN
#   Label                                    NaN
#   Name: 0, dtype: object
#   ------------------------------------------------------------------------
#   DB TEST
#   welding_db.find_one_and_update({'node_ip': 'node_ip', 'processes.process_id': 1},
#                                   {'$set': {'processes.$.label': 'youwan'}}, upsert=True)
@socketio.on('data_set', namespace='/node')  # ---> 이거 확인해봐야함.
def transmit_data(data):
    print("File GET")
    node_ip = request.remote_addr

    if welding_db.find_one({'node_ip': node_ip}):
        weldingDataFrame = pd.Series(" ".join(data["data"].strip(' b\'').strip('\'').split('\' b\'')).split('\\n')).str.split(',', expand=True)
        print(data["data"])
        print(data['process_id'])
        # weldingDataFrame = pd.read_csv(data["data"])
        # 등록할때는 processes가 empty Array이기 때문에 여기서 채워준다.
        welding_db.find_one_and_update({'node_ip': node_ip},
                                       {'$push': {'processes': {'label': 'temp_label',
                                                                'process_id': int(weldingDataFrame['Process ID'][0]),
                                                                'prediction': [],
                                                                'dataList': []}
                                                  }
                                        })
        for rowData in weldingDataFrame.iterrows():
            welding_db.find_one_and_update({'node_ip': node_ip, 'processes.process_id': rowData[2]},
                                           {'$push': {'processes.$.dataList': {"date": rowData[1],
                                                                               "current": rowData[3],
                                                                               "voltage": rowData[4],
                                                                               "wireFeed": rowData[5]}
                                                      }
                                            }, upsert=True)

@socketio.on('join')
def on_join(data):
    print("Web Join Room")
    channel = data['channel']
    join_room(channel)
    emit("get_recent_defect_data", {'data': {"node_defect_name": "NODE_NAME_1", "node_defect_date": "2020.05.04",
                                             "node_defect_id":"NODE_DEFECT_ID",
                                             "defect_task_id":"TASK_1",
                                                          "node_defect__id": "NODE_ID_1", 'undercut': 10.0,
                                                          "porosity": 10.0, "machanical": 10.0}})

    # emit("get_recent_status_init_average_data", {'data': {"node_name": "NODE_NAME_1", "node_date": "2020.05.04",
    #                                                  "node_avg_id": "NODE_ID_1", 'avg_current': 10.0,
    #                                                  "avg_voltage": 10.0, "avg_wire_feed": 10.0}})
    # emit("get_machine_status_init_data", {'data': {"node_name": "NODE_NAME_1", "node_id": "NODE_ID_1"}}, room="WEB")
    # emit("get_machine_status_init_data", {'data': {"node_name": "NODE_NAME_2", "node_id": "NODE_ID_2"}}, room="WEB")
    # emit("get_machine_status_init_data", {'data': {"node_name": "NODE_NAME_3", "node_id": "NODE_ID_3"}}, room="WEB")

    # emit("get_machine_status_data", {'data': {"node_id": "NODE_ID_1", 'current': 10.0, "voltage": 10.0, "wire_feed": 10.0}}, room="WEB")
    # emit("get_machine_status_data", {'data': {"node_id": "NODE_ID_1", 'current': 10.0, "voltage": 10.0, "wire_feed": 10.0}}, room="WEB")

@socketio.on("get_recent_status_init_average_data_callBack")
def get_recent_status_average_data_callBack(data):
    time.sleep(2)
    print("get_recent_status_average_data_callBack")
    emit('get_recent_status_average_data', {'data': {"node_name": "NODE_NAME_1", "node_date": "2020.05.111",
                                                     "node_avg_id": "NODE_ID_1", "task_id": "TASK_ID",
                                                     'avg_current': 14.0, "avg_voltage": 14.0, "avg_wire_feed": 14.0}})

@socketio.on('callBack')
def callBack(data):
    print("callBack")
    time.sleep(2)
    emit("get_machine_status_data", {'data': {"node_id": "NODE_ID_1", 'current': 10.0, "voltage": 10.0, "wire_feed": 10.0}}, room="WEB")
    emit("get_machine_status_data", {'data': {"node_id": "NODE_ID_2", 'current': 14.0, "voltage": 14.0, "wire_feed": 14.0}}, room="WEB")
    emit("get_machine_status_data", {'data': {"node_id": "NODE_ID_3", 'current': 16.0, "voltage": 16.0, "wire_feed": 16.0}}, room="WEB")


#   Node에서 보내준 실시간 데이터
#   real_time_data 네임스페이스로 전송
#   broadcast는 모든 client에 보내서 namespace로 한정.
#   event 이름 까먹음
@socketio.on('current_status', namespace='/node')
def current_status_data(data):
    real_time_data = data['data']
    current = data['data']['current']
    voltage = data['data']['voltage']
    wire_feed = data['data']['wire_feed']

    print("real_time_data", real_time_data)
    node_average_data_set_list[request.remote_addr].append((current, voltage, wire_feed))
    emit("get_machine_status_data", {'data': {"node_ip": "NODE_IP_1", "node_id": "NODE_ID_1", 'current': current, "voltage": voltage, "wire_feed": wire_feed}}, room="WEB")

    # 밑에 코드로 위에 코드 고쳐야함.
    # emit("get_machine_status_data", {'data': {"node_id": "NODE_ID_1", 'current': 10.0, "voltage": 10.0, "wire_feed": 10.0}}, room="WEB")

@socketio.on('get_machine_status_data_callBack')
def get_machine_status_data_callBack(data):
    node_ip = data['node_ip']
    if len(node_average_data_set_list[node_ip]) > 9:
        avg = node_average_data_set_list





#   ********************************************************************************************************************
#   Web Page Route
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/datasheet')
def data_sheet():
    return render_template("datasheet.html")


@app.route("/dataextract")
def data_extract():
    return render_template('dataextract.html')


@app.route("/defectanalysis")
def defect_analysis():
    return render_template('defectanalysis.html')


@app.route("/datalabel")
def data_label():
    return render_template('datalabel.html')


@app.route("/sensormanage")
def sensor_manage():
    return render_template('sensormanage.html')

@app.route("/process_detail.html")
def process_detail():
    return render_template("process_detail.html")


if __name__ == '__main__':
    socketio.run(app, host='192.168.0.104', debug=True)
