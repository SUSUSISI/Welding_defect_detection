from flask import Flask, jsonify, render_template, redirect
from flask_restplus import Resource, Api
from flask import request
from flask_pymongo import PyMongo
from flask_socketio import send, SocketIO, emit
from flask_socketio import join_room, leave_room
import csv


app = Flask(__name__)
# api = Api(app) # api 사용시, swagger.
app.config["MONGO_URI"] = "mongodb://localhost:27017/welding_defect_dection"
mongo = PyMongo(app)
socketio = SocketIO(app)
ROOMS = [] # 필요한지 모르겠지만 일단 Room 해두자.


# 노드는 무조건 Room에 입장한다.
# 그리고 끊임없이 Room안에서 소켓을 통해 서버로 데이터를 전송한다.
# 서버는 DB에 노드가 등록되어 있을 경우에만 데이터를 받아 웹으로 전송한다.
# connect은 서버의 ip주소 : 'http://localhost:5000'이걸로 연결하고
# client는 create를 호출할때 자신의 port번호를 알려줘야한다.
# Node의 room이름은 room + port 번호로 정한다.
@socketio.on('create')
def on_create(data):
    """Create a game lobby"""

    port = data['port']
    room_num = 'room' + str(port)
    join_room(room_num)
    ROOMS.append(room_num)
    # 내 생각에는 join_room이라는 message를 room_num의 room에 보낸다.
    send('join_room', room=room_num)

# 웹 테스트 용
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


@app.route("/register", methods=['POST'])
def register():
    if request.method == 'POST':
        node_name = request.args.get('node_name')
        port_num = request.args.get('port_num')
        interval = request.args.get('interval') # 이건 고민 좀 해보자
        description = request.args.get('description') # 일단 있어서 추가.

        if mongo.db.node_data.find({'port_num', port_num}).count() == 0:
            return "port가 존재하지 않습니다. port번호를 확인해주세요."

        # node_id가 필요한지 한번 더 확인해보고
        # 형우랑 필요한거 정리하기.
        node_id = "node_" + str(port_num)

        data = {"node_id": node_id,
                "node_name": node_name,
                "node_port": port_num,
                "state": "stopped",
                "interval": interval,
                "description": description,
                "process": [{
                    "process_id": "process_dummy"}]}

        print(mongo.db.welding_data.insert_one(data))
        # 등록이 완료되면 node_id를 가진 room으로 message를 보낸다.
        # client는 register를 사전에 등록하여 듣고 있어야 한다.
        # 듣고나면 client는 곧바로 데이터 전송을 시작한다.
        # message, interval, room_num를 data로 보낸다.
        socketio.emit('register', {'message': 'node register sucess', "interval": interval, 'room_num': node_id}, room=node_id)
        return "node register success"

# node는 등록전 사전에 room에 접속해있다.
# node는 room안에서 지속적으로 서버로 데이터를 보낸다.
# server에서는 node_id == romm_id
# node는 data를 다음과 같은 형태로 보낸다.
# {"current": 111.1, "voltage": 111.1, "wire_feed": 1111.1}
@socketio.on('transmit_data')
def transmit_data(data):
    node_id = data['node_id']
    print(node_id)
    # cursor = mongo.db.welding_data.find({})
    # flag = False
    # for item in cursor:
    #     if item['node_id'] == node_id:
    #         flag = True
    #         break
    # if flag:
    #     # 노드 등록 확인 완료.
    #     # 등록 되어 있으면 전송할때 받아서 다시 웹으로 넘겨줘!!!!!!
    #     emit("transmit_data_to_web", {"node_id": node_id,
    #                                   "data": {"current": data['current'], "voltage": data['voltage'], "wire_feed": data['wire_feed']}})
    #     print("")


# Connect
# 처음 connect될 때,
# 노드의 request.sid, request.remote_addr, 노드가 가지고 있을 포트번호.
# 연결되면 서버에서 노드한테 메세지를 보내고,
# 노드는 다시 서버한테 본인이 가지고 있는 포트번호를 보내.
# 포트번호 : 노드의 sid 연결
@socketio.on("connect")
def connect():
    print("connected ", request.sid, request.remote_addr)
    emit("connect_message", {"message": "server connected"}, room=request.sid)

# Connect CallBack
# connect되고나면 노드는 connect_callBack함수로
# node_sid와 port_num를 db에 저장한다.
@socketio.on("connect_callBack")
def callBack(data):
    port_num = data["port_num"]
    mongo.db.node_data.update({'$push': {'node_sid': request.sid, 'port_num': port_num}})


@socketio.on("callBack")
def callBack(data):
    print("hello")


    # f = open("/Users/wanni/PycharmProjects/Welding_defect_detection/test.csv", 'wb')
    # f.write(data["data"])
    # f.close()



@app.route("/process_state", methods=['GET', 'POST'])
def process_state():
    if request.method == 'GET':
        process_id = request.args.get('process_id')
        process_state = request.args.get('process_state')


@app.route("/allId", methods=['GET'])
def process_ids():
    if request.method == 'GET':
        # post body value

        cursor = mongo.db.welding_data.find({})
        print(cursor)
        ids = []
        for item in cursor:
            ids.append(item['id'])
        return jsonify(ids)


@app.route("/process", methods=['GET', 'POST'])
def process():
    print(request.environ.get('REMOTE_PORT'))
    if request.method == 'GET':
        process_id = request.args.get('process_id')

        if mongo.db.welding_data.find({"id": process_id}).count() == 0:
            return '해당 id를 찾을 수 없습니다.'

        data = mongo.db.welding_data.find_one_or_404({"id": process_id})
        process_data = {'id': data['id'], 'data': data['data']}
        return jsonify(process_data)
    else:
        body = request.json
        print(body)

        process_id = request.args.get('process_id')
        if mongo.db.welding_data.find({"id": process_id}).count() == 0:
            return '해당 id를 찾을 수 없습니다.'

        for item in body['data']:
            mongo.db.welding_data.update({'id': process_id}, {'$push': {'data': item}})
            print("item", item)


# Room에 무조건 Join해 있다가 DB에
@socketio.on('join')
def on_join(data):
    # username = data['username']
    print("connected ", request.sid, request.remote_addr)
    # room = data[request.sid]
    join_room(request.sid)
    send(request.sid + ' has entered the room.', room=request.sid)


@socketio.on('leave')
def on_leave(data):
    username = data['username']
    room = data['room']
    leave_room(room)
    send(username + ' has left the room.', room=room)


# Web Page Route
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


# @app.route("/templates/MOCK_DATA.json")
# def sensor_manage():
#   return 'MOCK_DATA.json'


# 자기 아이피로 하면됨.
if __name__ == '__main__':
    socketio.run(app, host='127.0.0.1', debug=True)
    # app.run(debug=True)

# from flask import Flask, render_template

# app = Flask(__name__)





# if __name__ == '__main__':
#     app.run(debug=True)
