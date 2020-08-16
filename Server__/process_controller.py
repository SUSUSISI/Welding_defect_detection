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


from flask import Flask, jsonify, render_template
from flask import request
from flask_socketio import send, SocketIO, emit
import pandas as pd
from flask_pymongo import PyMongo

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/welding_defect_dection"
app.config['SESSION_TYPE'] = 'filesystem'
socketio = SocketIO(app)
mongo = PyMongo(app)

welding_db = mongo.db.welding_data
node_db = mongo.db.node_data

# key: Node_ip, value: Node_sid
connected_nodeList = {}

#   웹 테이블 테스트
@app.route("/temp", methods=['POST'])
def temp():
    data1 = {
        "id": 0,
        "first_name": "Mariele",
        "last_name": "Mintram",
        "email": "mmintram0@cbsnews.com",
        "gender": "Female",
        "date": "2018-03-18",
        "ip_address": "110.1.138.115",
        "money": "50252.57"}

    data2 = {
        "id": 1,
        "first_name": "Creight",
        "last_name": "Coucher",
        "email": "ccoucher1@google.it",
        "gender": "Male",
        "date": "2017-11-18",
        "ip_address": "7.146.154.113",
        "money": "56909.08"}

    data3 = {
        "id": 2,
        "first_name": "Alie",
        "last_name": "Bidewel",
        "email": "abidewel2@illinois.edu",
        "gender": "Female",
        "date": "2017-11-14",
        "ip_address": "207.101.136.222",
        "money": "85243.91"
    }

    return {'data': [{
        "id": 0,
        "first_name": "Mariele",
        "last_name": "Mintram",
        "email": "mmintram0@cbsnews.com",
        "gender": "Female",
        "date": "2018-03-18",
        "ip_address": "110.1.138.115",
        "money": "50252.57"}]}

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
        node_id = request.args.get('node_id')
        description = request.args.get('description')
        speed = 1
        # web_ip = request.remote_addr
        node_ip = request.args.get('node_ip')

        # 무조건 등록.
        data = {'node_id': node_id, 'node_ip': node_ip,
                'speed': speed, 'description': description,
                'processes': []}
        welding_db.insert_one(data)

        # 등록 후 체크해서 확인
        if node_ip in connected_nodeList.keys():
            emit('data_request', {"request": True, 'speed': data['speed']}, room=connected_nodeList['node_ip'])

        return "node register success"

#   노드 삭제할 때, 호출
@app.route("/delete_node", methods=['POST'])
def delete_node():
    node_ip = request.args.get('node_ip')
    welding_db.delete_many({'node_ip': node_ip})

#   Connect Web
#   웹이 필요한 데이터 보내줘야
@socketio.on("connect", namespace='/web')
def connect():
    print("connected with web", request.sid, request.remote_addr)

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
    connected_nodeList[node_ip] = node_sid
    check_registered_node_and_emit(node_ip, node_sid)

#   Disconnect Node
#   노드와 연결해제되면 connectNodeList에서 제거.
#   웹에 커넥션이 해제됨을 알려줘야함.
@socketio.on("disconnect", namespace='/node')
def disconnect():
    print("disconnect Node", request.sid, request.remote_addr)
    node_ip = request.remote_addr
    connected_nodeList.pop(node_ip)
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
        emit('data_request', {"request": False, 'speed': 1}, room=sid)
    else:
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
@socketio.on('transmit_data')  # ---> 이거 확인해봐야함.
def transmit_data(data):
    node_ip = request.remote_addr
    if welding_db.find_one({'node_ip': request.node_ip}):
        weldingDataFrame = pd.read_csv(data["data"])
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

#   Node에서 보내준 실시간 데이터
#   real_time_data 네임스페이스로 전송
#   broadcast는 모든 client에 보내서 namespace로 한정.
#   event 이름 까먹음
@socketio.on('what??')
def temp_data(data):
    real_time_data = data['data']
    emit('send_data_to_web', {'data': real_time_data}, namespace='/real_time_data')

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


if __name__ == '__main__':
    socketio.run(app, host='192.168.0.104', debug=True)
