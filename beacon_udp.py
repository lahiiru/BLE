from uptime import uptime
from time import sleep
from bluezero import central
import re, uuid
from bluetooth import *
import struct
from bluepy.btle import Scanner, DefaultDelegate
import json
import socket
from bluezero import adapter


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
devices_info = dict()
SVC_UUID = "12341000-1234-1234-1234-123456789abc"
DEV_IDS_CHR = "6E400003-B5A3-F393-E0A9-E50E24DCCA9A"
DEV_ATTR_CHRC = '6E400003-B5A3-F393-E0A9-E50E24DCCA9B'

def enable_ble():
    print('enabling bluetooth')
    try:
        os.system('sudo systemctl restart bluetooth.service && sudo hciconfig hci0 up')
    except Exception as e:
        print(e)

sleep(10)  # wait device to initialize wireless modules
enable_ble()
sleep(2)
dongles = adapter.list_adapters()
print('dongles available: ', dongles)
dongle = adapter.Adapter(dongles[0])
SELF = dongle.address
print('address: ', SELF)

def writeBytes(file, value = 65535):
    f = None
    try:
        f = open(file, "wb+")
        f.write(struct.pack('H', value))
    finally:
        if f is not None:
            f.close()

class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    def handleDiscovery(self, dev, isNewDev, isNewData):
        if isNewDev:
            print("Discovered device", dev.addr)
        elif isNewData:
            print("Received new data from", dev.addr, dev.getScanData())

scanner = Scanner().withDelegate(ScanDelegate())

def scan():
    devices_set = set()
    devices = scanner.scan(10.0, True)
    for dev in devices:
        for (adtype, desc, value) in dev.getScanData():
            if value == SVC_UUID:
                print("Device %s (%s), RSSI=%d dB" % (dev.addr, dev.addrType, dev.rssi))
                obj = devices_info.get(dev.addr)
                if obj is None:
                    devices_info[dev.addr] = {}
                devices_info.get(dev.addr)["rssi"] = dev.rssi
                print("  %s = %s" % (desc, value))
                devices_set.add(dev.addr)
    return devices_set


class MyPeripheralDevice:
    def __init__(self, device_addr, adapter_addr=SELF):
        self.remote_device = central.Central(adapter_addr=adapter_addr,
                                             device_addr=device_addr)
        self._id_char = self.remote_device.add_characteristic(SVC_UUID, DEV_IDS_CHR)
        self._attr_char = self.remote_device.add_characteristic(SVC_UUID, DEV_ATTR_CHRC)

    def connect(self):
        self.remote_device.connect()
        while not self.remote_device.services_resolved:
            sleep(0.5)
        self.remote_device.load_gatt()

    def disconnect(self):
        self.remote_device.disconnect()

    @property
    def id(self):
        return self._id_char.value

    @property
    def attr(self):
        return self._attr_char.value


def read_data(address):
    print("Connecting to", address)
    data = ''
    tries = 5
    while tries > 0:
        try:
            tries -= 1
            my_dev = MyPeripheralDevice(address)

            my_dev.connect()
            ids = my_dev.id
            attrs = my_dev.attr
            my_dev.disconnect()

            print("ids", bytes(ids))
            devices_info.get(address)["id"] = struct.unpack('H', bytes(ids))
            devices_info.get(address)["attr"] = bytes(attrs).decode()
            print(json.dumps(devices_info))
            break
        except Exception as e:
            print(e)
    return data


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
        print("Asked to change ID to "+dat)
        node_id = dat
        writeBytes('id', int(dat))


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
    global devices_to_update

    new_devices = scan()

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

    #if devices_modified: # need to notify to all devices
    devices_to_update = devices_to_update.union(devices)

    if len(devices_to_update) > 0:
        update_message = "%sEOD" % devices
        print("Update message = %s" % update_message)
        for addr in devices_to_update.copy():
            try:
                read_data(addr)
                # print("Connecting to %s to send updated list" % addr)
                # client_socket = BluetoothSocket(RFCOMM)
                # client_socket.connect((addr, 1))
                #
                # client_socket.send(update_message)
                # print("Sent to %s" % addr)
                # client_socket.close()
                devices_to_update.remove(addr)
            except Exception as e:
                print(e)
    else:
        print("No updates to send")


# def get_all_devices():
#     data = f.read()
#     if len(data) > 0:
#         s = eval(data)
#         data = '%s'%devices.union(s)
#     return data

def process_management_link():
    print('Connecting to management app...')
    connect()  # ensure the connectivity
    frame = 'OK`{}`{}`{}`{}`{}'.format(
        node_id,
        get_uptime_minutes(),
        get_battery(),
        SELF,
        json.dumps(devices_info)
    )
    send(frame)
    print("Sent data: " + frame)


def get_bluetooth_mac():
    return ':'.join(re.findall('..', '%012x' % uuid.getnode())).upper()


i = 0
while True:  # repeatedly send status/ping messages
    if i % 2 == 0:
        process_management_link()
    process_scatter_link()
    sleep(2)  # should be > 60 sec wait in production
    i += 1
