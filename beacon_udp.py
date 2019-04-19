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
from config import DEV_ATTR_CHRC, DEV_IDS_CHRC, SVC_UUID, SERVER_ADD


# if you are setting up from the scratch. please use follwoing commands.
# install dependencies
#   sudo apt-get install python3-pip
#   sudo pip3 install uptime
# register as startup script
#   put the script in home directory
#   crontab -e
#   @reboot sudo python3 /home/pi/BLE/beacon_udp.py

"""
    BEACON NODE SCRIPT
"""


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # udp client to send data to management app
sock.settimeout(5)  # if server doesn't respond withing 5 sec, ignore
server_address = (SERVER_ADD, 9091)
node_id = "not-set"
devices = set()
global_devices = set()
devices_to_update = set()
devices_info = dict()

last_dev_info = ''


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
    all_dev = scanner.scan(10.0, True)
    for dev in all_dev:
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
        self._id_char = self.remote_device.add_characteristic(SVC_UUID, DEV_IDS_CHRC)
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
    print("Reading data from", address)
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
            print('Connecting management app on {}:{}'.format(*server_address))
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
        writeBytes('/home/pi/id', int(dat))
        print("Asked to change ID to "+dat)


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
    new_devices = scan()
    print('Discovered device list', new_devices)
    for addr in new_devices.copy():
        try:
            read_data(addr)
        except Exception as e:
            print(e)


def process_management_link():
    global last_dev_info
    new_dev_info = json.dumps(devices_info)
    if last_dev_info != new_dev_info:
        last_dev_info = new_dev_info
        frame = 'OK`{}`{}`{}`{}`{}'.format(
            node_id,
            get_uptime_minutes(),
            get_battery(),
            SELF,
            new_dev_info
        )
        print('Connecting to management app...')
        connect()  # ensure the connectivity
        send(frame)
        print("Sent update: " + frame)
    else:
        print("No update to send")


def get_bluetooth_mac():
    return ':'.join(re.findall('..', '%012x' % uuid.getnode())).upper()


while True:  # repeatedly send status/ping messages
    process_management_link()
    process_scatter_link()
    sleep(2)  # should be > 60 sec wait in production
