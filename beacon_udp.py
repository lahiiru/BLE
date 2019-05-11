from uptime import uptime
from time import sleep, time
from bluezero import central
import re, uuid
from bluetooth import *
import struct
from bluepy.btle import Scanner, DefaultDelegate
import json
import socket
from bluezero import adapter
from config import DEV_ATTR_CHRC, DEV_IDS_CHRC, SVC_UUID, SERVER_ADD, TIME_TO_PING
import os, logging

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

logging.basicConfig(filename='node.log', filemode='w', format='%(lineno)d %(funcName)s %(filename)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)

logging.info('Starting beacon node script...')

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # udp client to send data to management app
sock.settimeout(5)  # if server doesn't respond withing 5 sec, ignore
server_address = (SERVER_ADD, 9091)
node_id = "not-set"
devices = set()
global_devices = set()
devices_to_update = set()
devices_info = dict()
last_ping = time()

last_dev_info = ''


def enable_ble():
    logging.info('enabling bluetooth')
    try:
        os.system('sudo systemctl restart bluetooth.service && sudo hciconfig hci0 up')
    except Exception as e:
        logging.error(e)


def readBytes(file):
    f = None
    b = b''
    try:
        f = open(file, "rb+")
        b = f.read()
    finally:
        if f is not None:
            f.close()
    return b


logging.info(os.getpid())
# sleep(10)  # wait device to initialize wireless modules
# enable_ble()
sleep(2)
dongles = adapter.list_adapters()
logging.info('dongles available: %s', dongles)
dongle = adapter.Adapter(dongles[0])
SELF = dongle.address
logging.info('address: %s', SELF)

try:
    bs = readBytes('/home/pi/id')
    node_id = str(struct.unpack('H', bs)[0])
except Exception as e:
    logging.error(e)

node_id = "not-set"

logging.info('node id: %s', node_id)


def writeBytes(file, value = 65535):
    f = None
    try:
        f = open(file, "wb+")
        f.write(struct.pack('H', value))
    except Exception as e:
        logging.error(e)
    finally:
        if f is not None:
            f.close()


class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    def handleDiscovery(self, dev, isNewDev, isNewData):
        if isNewDev:
            logging.info("Discovered device %s", dev.addr)
        elif isNewData:
            logging.info("Received new data from %s", dev.addr, dev.getScanData())


scanner = Scanner().withDelegate(ScanDelegate())


def scan():
    devices_set = set()
    all_dev = scanner.scan(10.0, True)
    for dev in all_dev:
        for (adtype, desc, value) in dev.getScanData():
            if value == SVC_UUID:
                logging.info("Device %s (%s), RSSI=%d dB" % (dev.addr, dev.addrType, dev.rssi))
                obj = devices_info.get(dev.addr)
                if obj is None:
                    devices_info[dev.addr] = {}
                devices_info.get(dev.addr)["rssi"] = dev.rssi
                logging.info("  %s = %s" % (desc, value))
                devices_set.add(dev.addr)
    return devices_set


class MyPeripheralDevice:
    def __init__(self, device_addr, adapter_addr=SELF):
        self.remote_device = central.Central(adapter_addr=adapter_addr,
                                             device_addr=device_addr)
        try:
            self._id_char = self.remote_device.add_characteristic(SVC_UUID, DEV_IDS_CHRC)
            self._attr_char = self.remote_device.add_characteristic(SVC_UUID, DEV_ATTR_CHRC)
        except Exception as e:
            logging.error(e)

    def connect(self):
        if not self.remote_device.connected:
            self.remote_device.connect()
        else:
            logging.info('Already connected.')
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

    def subscribe(self, user_callback):
        self._id_char.add_characteristic_cb(user_callback)
        self._id_char.start_notify()

    def run_async(self):
        self.remote_device.run()

def callback(a, b, *args):
    logging.info('callback %s %s', a, b)

def read_data(address):
    logging.info("Reading data from %s", address)
    data = ''
    tries = 5
    while tries > 0:
        my_dev = None
        try:
            tries -= 1
            my_dev = MyPeripheralDevice(address)

            my_dev.connect()
            ids = my_dev.id
            attrs = my_dev.attr
            if len(attrs) == 2:
                ids, attrs = attrs, ids
            logging.info('%s %s', ids, attrs)

            '''
            my_dev.subscribe(callback)
            logging.info('entering to event loop')
            my_dev.run_async()
            logging.info('exiting from event loop')
            '''
            logging.info("ids %s", bytes(ids))
            logging.info("attrs %s", attrs)
            devices_info.get(address)["id"] = struct.unpack('H', bytes(ids))
            devices_info.get(address)["attr"] = bytes(attrs).decode()
            logging.info(json.dumps(devices_info))
            break
        except Exception as e:
            logging.exception(e, exc_info=True)
            if my_dev is not None:
                my_dev.disconnect()

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
            logging.info('Connecting management app on {}:{}'.format(*server_address))
            sock.connect(server_address)
            connected = True
        except Exception as e:
            logging.error(e)
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
        logging.error(e)
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
    logging.info('HED %s, DAT %s', hed, dat)
    if hed == "ID":  # asked to set ID
        logging.info("Asked to change ID to %s", dat)
        node_id = dat
        writeBytes('/home/pi/id', int(dat))


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
    global devices_to_update
    logging.info("\n\nPerforming inquiry...")
    new_devices = scan()
    devices_to_update = devices_to_update.union(new_devices)
    logging.info('Discovered all device list %s', devices_to_update)
    for addr in devices_to_update.copy():
        try:
            read_data(addr)
        except Exception as e:
            logging.error(e)


def process_management_link():
    global last_dev_info, last_ping, TIME_TO_PING
    new_dev_info = json.dumps(devices_info)
    if time() > TIME_TO_PING + last_ping or last_dev_info != new_dev_info:
        last_dev_info = new_dev_info
        frame = 'OK`{}`{}`{}`{}`{}'.format(
            node_id,
            get_uptime_minutes(),
            get_battery(),
            SELF,
            new_dev_info
        )
        logging.info('Connecting to management app...')
        connect()  # ensure the connectivity
        send(frame)
        last_ping = time()
        logging.info("Sent update: %s", frame)
    else:
        logging.info("No update to send")


def get_bluetooth_mac():
    return ':'.join(re.findall('..', '%012x' % uuid.getnode())).upper()


while True:  # repeatedly send status/ping messages
    try:
        process_management_link()
        process_scatter_link()
        sleep(2)  # should be > 60 sec wait in production
    except Exception as e:
        logging.error(e, exc_info=True)
        sleep(10)
