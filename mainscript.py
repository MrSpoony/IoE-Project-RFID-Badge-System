import paho.mqtt.client as mqtt
from influxdb import InfluxDBClient
import json
import datetime
import plotly.graph_objects as go

INFLUXDB_IP_ADDRESS = "10.0.103.38"
INFLUXDB_PORT = 8086
INFLUXDB_HTTP = "http://"
INFLUXDB_USER = "admin"
INFLUXDB_PASSWORD = "diesisteinmoeglichstlangesadminpasswort"
INFLUXDB_DATABASE = "ioeproject"
INFLUXDB_CLIENT = InfluxDBClient(INFLUXDB_IP_ADDRESS, INFLUXDB_PORT, INFLUXDB_USER, INFLUXDB_PASSWORD, INFLUXDB_DATABASE)

def makeUserList(): 
    allUsers = {}
    databaseData = INFLUXDB_CLIENT.query(f'SELECT * FROM userlog').raw
    allEntries = databaseData['series'][0]['values']
    for i in allEntries:
        if not (i[1] in allUsers):
            allUsers[i[2]] = i[1]
    return allUsers
userList = makeUserList()

def on_connect(client, userdata, flags, rc):
    client.subscribe("userlist")

def on_message(client, userdata, msg):
    msg_decoded = msg.payload.decode("utf-8")
    msg_json = json.loads(msg_decoded)
    currentUUID = msg_json["uuid"]
    timestamp = datetime.datetime.utcnow()
    currentUser = ""
    if currentUUID in userList:
        currentUser = userList[currentUUID]
    else:
        newUser = input("You are new here please enter your name: ")
        userList.update({currentUUID : newUser})
        currentUser = userList[currentUUID]
    print("\n\n")
    body = [
        {
            "measurement" : "userlog", 
            "time" : timestamp, 
            "fields" : {
                "user" : currentUser, 
                "uuid" : str(currentUUID)
            }
        }
    ]
    # print("\n\n\n\n\n\n\n")
    INFLUXDB_CLIENT.write_points(body)
    databaseData = INFLUXDB_CLIENT.query(f'SELECT * FROM userlog').raw
    allEntries = databaseData['series'][0]['values']
    currentUserEntries = []
    count = 0
    for i in allEntries:
        if i[1] == currentUser:
            currentUserEntries.append(i)
            count+=1
    print(currentUser)
    if count % 2 == 0:
        if len(currentUserEntries) >= 2:
            startTime = datetime.datetime.strptime(currentUserEntries[-1][0], '%Y-%m-%dT%H:%M:%S.%fZ')
            finalTime = datetime.datetime.strptime(currentUserEntries[-2][0], '%Y-%m-%dT%H:%M:%S.%fZ')
            timeBadged = startTime - finalTime
            # startTime = datetime.datetime.time(startTime)
            # finalTime = datetime.datetime.time(finalTime)
            # timeBadged = datetime.datetime.combine(datetime.date.today(),startTime) - datetime.datetime.combine(datetime.date.today(), finalTime)
            timeBadged = round(timeBadged.total_seconds())
        print("Logout")
        print(f"You were logged in for {timeBadged} seconds.")
        client.publish("logout", currentUser)
        client.publish("time", timeBadged)

        # piecesOfPlot = list(range(len(currentUserEntries)))
        # fig = go.Figure()

        # for i in range(1, len(currentUserEntries), 2):
        #     tempBadged = round(((datetime.datetime.strptime(currentUserEntries[i][0], '%Y-%m-%dT%H:%M:%S.%fZ').timestamp() - datetime.datetime.strptime(currentUserEntries[i-1][0], '%Y-%m-%dT%H:%M:%S.%fZ').timestamp()) - datetime.datetime.now().timestamp()))
        #     fig.add_trace(go.Bar(x=piecesOfPlot, y = [tempBadged,0]))
        # fig.update_layout(barmode='relative', title_text=currentUser)
        # fig.show()
    else:
        print("Login")
        client.publish("login", currentUser)

MQTT_IP_ADRESS = "10.0.103.38"
MQTT_USER = "ioeuser"
MQTT_PASSWORD = "LinuxBesteBetriebssystem"
MQTT_CLIENT = mqtt.Client("MQTT_PYTHON")
MQTT_CLIENT.on_connect = on_connect
MQTT_CLIENT.on_message = on_message
MQTT_CLIENT.username_pw_set(username = MQTT_USER, password = MQTT_PASSWORD)
MQTT_CLIENT.connect(MQTT_IP_ADRESS, 1883, 60)
MQTT_CLIENT.loop_forever()