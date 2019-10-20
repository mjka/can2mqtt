#!/bin/bash


cp *.py canrestart /usr/local/bin/

mkdir -p /etc/can2mqtt/
if [ ! -e /etc/can2mqtt/config ] ; then 
	cp config.example /etc/can2mqtt/config
fi
if [ ! -e /etc/can2mqtt/db ] ; then 
	cp db.example /etc/can2mqtt/db
fi

cp mqtt2can.py /usr/local/bin/

cat << EOF

Edit /etc/can2mqtt/config

Dependencies:
===================================================
python3-paho-mqtt can-utils python3-dateutil python3-can python3-serial
===================================================

Add to /etc/rc.local 
===================================================
/sbin/ip link set can0 up type can bitrate 125000
nohup /usr/local/bin/canrestart &
nohup python3 /usr/local/bin/can2mqtt.py > /var/log/can2mqtt.log &
nohup python3 /usr/local/bin/mqtt2can.py > /var/log/mqtt2can.log &
===================================================
EOF



