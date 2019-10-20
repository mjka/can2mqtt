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

can.rc['interface'] = 'socketcan_native'
can.rc['channel'] = 'can0'
can.rc['bitrate'] = 125000

bus = can.interface.Bus()


def on_message(client, userdata, message):
    pass

def on_connect(client, userdata, flags, rc):
    #client.subscribe('#')
    print("Connected to MQTT Broker. client=%s userdata=%s flags=%s rc=%s" % (client, userdata, flags, rc))


def handle(msg, client):
    #print(msg)
    id = msg.arbitration_id
    if id in DB.mData:
        db = DB.mData[id]
        #print(db.__repr__())
        # TODO try...
        if db[0] in ('RX', 'rx', 'R', 'r'):                    
            data = struct.unpack(db[1], msg.data)
            for i in range(len(data)):
                topic = db[2][i]
                value = data[i]
                if type(value) is float:
                    #print ("Float")
                    value = '%.3g' % value
                print("%s = %s" % (topic, value))
                client.publish(topic, value, qos=1)
 
while 1:
    try:
        client = mqtt.Client()
        client.username_pw_set(CONF.mData['MQTT']['USER'], CONF.mData['MQTT']['PASS'])
        client.on_connect = on_connect
        client.on_message = on_message
        client.connect(CONF.mData['MQTT']['HOST'], keepalive=60)
        client.loop_start()
        
        #   0x300: ('EV', 'ff', ('device/bett/temp', 'device/bett/humidity',)),
        
        while 1:
            msg = bus.recv(1)
            if msg is not None:
                handle(msg, client)
       #client.loop(1)
        #print("LOOP")
        CONF.Read()
        DB.Read()
    except Exception as e:
        print("type error: " + str(e))
        print(traceback.format_exc())

