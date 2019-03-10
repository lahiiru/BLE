import socket
from time import sleep
from uptime import uptime
import os
import re, uuid

# if you are setting up from the scratch. please use follwoing commands.
# install dependencies
#   sudo apt-get install python3-pip
#   sudo pip3 install uptime
# register as startup script
#   put the script in home directory
#   crontab -e
#   @reboot sudo python3 /home/pi/beacon_udp.py

"""
    BEACON NODE SCRIPT
"""


SERVER_ADD = '192.168.8.102'  # ip address of the machine where management app runs
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # udp client to send data to management app
sock.settimeout(5)  # if server doesn't respond withing 5 sec, ignore
server_address = (SERVER_ADD, 9091)
node_id = "not-set"


def enable_ble():
    print('enabling bluetooth')
    os.system('sudo systemctl start bluetooth.service && sudo hciconfig hci0 up')


def connect():
    """
    Ensure the connectivity. This repeats tries to connect util successful
    :return:
    """
    connected = False
    while not connected:
        try:
            # Connect the socket to the port where the server is listening
            print('connecting management app on {}:{}'.format(*server_address))
            sock.connect(server_address)
        except Exception as e:
            print(e)
            sleep(10)  # should be > 60 sec wait in production


def send(message_str):
    """
    Send data to management app
    :param message_str: message to send
    :return:
    """
    try:
        # send some data
        sock.sendto(message_str.encode(), server_address)
        # receive some data
        data, addr = sock.recvfrom(1024)
        # process server response
        handle_ack(data)
    except Exception as e:
        print(e)
        sleep(10)


def handle_ack(data):
    """
    Process the responses of management app and take necessary actions
    :param data: from management app
    :return:
    """
    d = data.decode("utf-8") # ascii or utf-8
    global node_id
    hed = d[:2]  # first part of the message indicates the message type
    dat = d[3:]  # rest of them are data
    print(hed, dat)
    if hed == "ID":  # asked to set ID
        node_id = dat


def get_uptime_minutes():
    """
    Number of seconds/minutes the node is continuously running
    :return:
    """
    return int(uptime())


def get_battery():
    """
    Get the level of battery 0 - 100
    :return:
    """
    return 50


def get_bluetooth_mac():
    return ':'.join(re.findall('..', '%012x' % uuid.getnode())).upper()


sleep(10)  # wait device to initialize wireless modules
enable_ble()
sleep(2)

while True:  # repeatedly send status/ping messages
    connect()  # ensure the connectivity
    frame = 'OK:{}:{}:{}:{}'.format(node_id, get_uptime_minutes(), get_battery(), get_bluetooth_mac())
    send(frame)
    sleep(10)  # should be > 60 sec wait in production
