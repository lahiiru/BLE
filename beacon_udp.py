import socket
from time import sleep
from uptime import uptime
import os
import re, uuid
from bluetooth import *

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
f = open('global_devices.txt', 'r')
devices = set()
global_devices = set()
devices_to_update = set()


def enable_ble():
    print('enabling bluetooth')
    try:
        os.system('sudo systemctl start bluetooth.service && sudo hciconfig hci0 up')
    except Exception as e:
        print(e)


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
            connected = True
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


def process_scatter_link():
    print("\n\nPerforming inquiry...")
    new_devices = set()
    global devices_to_update

    services = find_service(name="helloService")
    print(services)

    for i in range(len(services)):
        match = services[i]
        if match["name"] == "helloService":
            port = match["port"]
            name = match["name"]
            host = match["host"]
            print(name, port, host)
            new_devices.add(host)

    devices_diff_set = devices.symmetric_difference(new_devices)
    print("Diff set = %s"%devices_diff_set)
    devices_modified = False

    if len(devices_diff_set) > 0:
        for addr in devices_diff_set:
            if addr in new_devices:
                devices.add(addr)
                devices_to_update.add(addr)
                devices_modified = True
            else:
                print("Removing device %s" % addr)
                devices.remove(addr)
                if addr in devices_to_update:
                    devices_to_update.remove(addr)
                devices_modified = True

    if devices_modified: # need to notify to all devices
        devices_to_update = devices_to_update.union(devices)

    if len(devices_to_update) > 0:
        update_message = "%sEOD" % devices
        print("Update message = %s" % update_message)
        for addr in devices_to_update.copy():
            try:
                print("Connecting to %s to send updated list" % addr)
                client_socket = BluetoothSocket(RFCOMM)
                client_socket.connect((addr, 1))

                client_socket.send(update_message)
                print("Sent to %s" % addr)
                client_socket.close()
                devices_to_update.remove(addr)
            except Exception as e:
                print(e)
    else:
        print("No updates to send")

def get_all_devices():
    data = f.read()
    return data

def process_management_link():
    print('Connecting to management app...')
    connect()  # ensure the connectivity
    frame = 'OK`{}`{}`{}`{}`{}'.format(
        node_id,
        get_uptime_minutes(),
        get_battery(),
        get_bluetooth_mac(),
        get_all_devices()
    )
    send(frame)


def get_bluetooth_mac():
    return ':'.join(re.findall('..', '%012x' % uuid.getnode())).upper()


sleep(10)  # wait device to initialize wireless modules
enable_ble()
sleep(2)

i = 0
while True:  # repeatedly send status/ping messages
    if i % 2 == 0:
        process_management_link()
    process_scatter_link()
    sleep(10)  # should be > 60 sec wait in production
    i += 1
