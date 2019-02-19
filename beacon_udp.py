import socket
import sys
from time import sleep
from uptime import uptime
import time
import os
# sudo apt-get install python3-pip
# sudo pip3 install uptime
# grep cron -A5 /var/log/syslog
# @reboot sudo python3 /home/pi/beacon_udp.py

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(5)
server_address = ('192.168.8.102', 9091)
node_id = "not-set";

def enableBLE():
    print('enabling BLE')
    os.system('sudo hciconfig hci0 up && sudo hciconfig hci0 leadv 3')

def setBeaconInfo():
    print('configuring beacon data')
    os.system('sudo hcitool -i hci0 cmd 0x08 0x0008 13 02 01 06 03 03 aa fe 0b 16 aa fe 10 00 03 74 65 73 74 07 00 00 00 00 00 00 00 00 00 00 00 00')
    
def connect():
    connected = False
    while not connected:
        try:
            # Connect the socket to the port where the server is listening
            
            print('connecting management app on {}:{}'.format(*server_address))
            sock.connect(server_address)
            connected = True
        except Exception as e:
            print(e)
            sleep(10) # 60 sec wait

def send(message_str):        
    try:
        # send some data
        sock.sendto(message_str.encode(), server_address)

        # receive some data
        data, addr = sock.recvfrom(1024)
        handleAck(data)
    except Exception as e:
        print(e)
        sleep(10)
        connected = False

def handleAck(data):
    d = data.decode("utf-8")
    global node_id
    hed = d[:2]
    dat = d[3:]
    print(hed, dat)
    if hed == "ID":
        node_id = dat
    
def getUptimeMinutes():
    return int(uptime())

def getBattery():
    return 50;

sleep(10)
enableBLE()
sleep(2)
setBeaconInfo()
while 1:
    connect()
    frame = 'OK:{}:{}:{}'.format(node_id, getUptimeMinutes(),getBattery())
    send(frame)
    sleep(10)
