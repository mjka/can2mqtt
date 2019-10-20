#!/usr/bin/python3
# -*- coding: utf-8 -*-
 
import sys
import traceback
import paho.mqtt.client as mqtt
import datetime
import dateutil.parser
import time
import json
import can
import struct
import canutil




CONF = canutil.Config("/etc/can2mqtt/config")
DB   = canutil.Config("/etc/can2mqtt/db")
EV = {}
signal = {}

def load_db():
    global EV
    EV.clear
    for k,v in DB.mData.items():
        if v[0] == 'EV':
            for topic in v[2]:
                EV[topic] = k

load_db()


# https://docs.python.org/3.6/library/struct.html
#        'device/bett/temp': (0x300, 'ff', ('_', 'device/bett/humidity',)),
#        'device/licht1/pir': (0x301, '?', ('_',)),
#        'device/bett/counter': (0x3FF, 'L', ('_',)),
#        }



can.rc['interface'] = 'socketcan_native'
can.rc['channel'] = 'can0'
can.rc['bitrate'] = 125000

bus = can.interface.Bus()


def send_event(topic, value):
    if topic not in EV:
        return
    aid = EV[topic]
    dbmsg = DB.mData[aid]
    values = [signal[t] if t in signal else 0 for t in dbmsg[2]]
    #print("VALUES = %s" %values.__repr__())
    data = struct.pack(dbmsg[1], *values)

    msg = can.Message(arbitration_id=aid, data=data, extended_id=False)

    try:
        bus.send(msg)
        #print("Message sent on {}".format(bus.channel_info))
    except can.CanError:
        print("Message NOT sent")






def parse_msg(message):
    if message.upper().strip() in ('ON', 'YES', 'TRUE', 'ACTIVE', 'ONLINE' ):
        return 1
    elif message.upper().strip() in ('OFF', 'NO', 'PASSIVE', 'FALSE', 'OFFLINE'):
        return 0
    try:
        val = int(message)
        return val
    except:
        pass
    try:
        val = float(message)
        return val
    except:
        pass
    try:
        val = dateutil.parser.parse(message)
        return val
    except:
        pass
    try:
        val = json.loads(message)
        return val
    except:
        pass
    if CONF.mData['VERBOSE'] >= 1:
        print("CANNOT PARSE %s" % message)
    return None

def handle(value, topic):
    if value is None:
        pass
    #elif type(value) is str:
    #    print('IGNORE STRING: %s = %s' % (topic, value))
    #elif type(value) is datetime.datetime:
    #    print('IGNORE DATETIME: %s = %s' % (topic, value))
    elif type(value) is dict:
        for key, v in value.items():
            if type(v) is str:
                v = parse_msg(v)
            handle(v, topic+'/'+key)
    else:
        #
        #json_body = [
        #    {
        #        "measurement": topic,
        #        "time": receiveTime,
        #        "fields": {
        #            "value": value
        #        }
        #    }
        #]
        #
        #dbclient.write_points(json_body)
        if CONF.mData['VERBOSE'] >= 3:
            print('SIGNAL: '+ topic + " = " + str(value))
        global signal
        signal[topic] = value
        send_event(topic, value)


 
def on_message(client, userdata, message):
    try:
        #print("message: %s = %s" % (message.topic, message.payload))
        msg = str(message.payload.decode("utf-8"))
        #p = parse_msg(message.payload)
        p = parse_msg(msg)
        handle(p, message.topic)
        #print("message received: ", msg)
    except Exception as e:
        print ("ERROR in ON_MESSAGE:")
        #print (sys.exc_info()[0])
        #print (sys.exc_info()[1])
        #print (e)
        #print (e.__traceback__)
        #print (e.__repr__())
        print(traceback.format_exception(None, e, e.__traceback__))
        #print (sys.exc_info()[2].__repr__())
        #for err in sys.exc_info():
        #    print(err.__repr__())

def on_socket_close(client, userdata, rc):
    #client.subscribe('#')
    print("on_socket_close client=%s userdata=%s sock=%s" % (client, userdata, rc))

def on_disconnect(client, userdata, rc):
    #client.subscribe('#')
    print("DISCONNECT client=%s userdata=%s rc=%s" % (client, userdata, rc))

def on_connect(client, userdata, flags, rc):
    client.subscribe('#')
    print("client=%s userdata=%s flags=%s rc=%s" % (client, userdata, flags, rc))
    #print("Connected to MQTT Broker: " + BROKER_ADDRESS)
 
#BROKER_ADDRESS = "ha.fritz.box"
client = mqtt.Client()
client.username_pw_set(CONF.mData['MQTT']['USER'], CONF.mData['MQTT']['PASS'])
client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect
client.on_socket_close = on_socket_close
client.connect(CONF.mData['MQTT']['HOST'], keepalive=10)
client.loop_start()
#client.loop_forever()
while 1:
    #client.loop(1)
    time.sleep(1)
    #print("LOOP")
    CONF.Read()
    if DB.Read():
        load_db()

