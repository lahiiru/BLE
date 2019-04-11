# Standard modules
import dbus
import subprocess
import os
import time
try:
    from gi.repository import GObject
except ImportError:
    import gobject as GObject

# Bluezero modules
from bluezero import adapter
from bluezero import advertisement
from bluezero import localGATT
from bluezero import GATT
import struct

# constants
MY_SRVC = '12341000-1234-1234-1234-123456789abc'
DEV_IDS_CHRC = '6E400003-B5A3-F393-E0A9-E50E24DCCA9A'
DEV_ATTR_CHRC = '6E400003-B5A3-F393-E0A9-E50E24DCCA9B'

def getByteArrayFromString(string):
    return getByteArrayFromBytes(string.encode('utf-8'))

def getByteArrayFromBytes(bs):
    return [dbus.Byte(b) for b in bs]


class DeviceIDsChrc(localGATT.Characteristic):
    def __init__(self, service):
        localGATT.Characteristic.__init__(self,
                                          1,
                                          DEV_IDS_CHRC,
                                          service,
                                          [dbus.Byte("0".encode('utf-8'))],
                                          False,
                                          ['read'])

    def ReadValue(self, options):
        bs = readBytes('id')
        array = getByteArrayFromBytes(bs)
        print("A device is reading ID profile. Returning", bs)
        return dbus.Array(array)


class DeviceAttrChrc(localGATT.Characteristic):
    def __init__(self, service):
        localGATT.Characteristic.__init__(self,
                                          2,
                                          DEV_ATTR_CHRC,
                                          service,
                                          [dbus.Byte("1".encode('utf-8'))],
                                          False,
                                          ['read'])

    def ReadValue(self, options):
        print("A device is reading attribute profile")
        array = getByteArrayFromString("batt=20%")
        return dbus.Array(array)


class ble:
    def __init__(self):
        self.bus = dbus.SystemBus()
        self.app = localGATT.Application()
        self.srv = localGATT.Service(1, MY_SRVC, True)

        self.idsCharc = DeviceIDsChrc(self.srv)
        self.attrCharc = DeviceAttrChrc(self.srv)

        self.idsCharc.service = self.srv.path
        self.attrCharc.service = self.srv.path

        self.app.add_managed_object(self.srv)
        self.app.add_managed_object(self.idsCharc)
        self.app.add_managed_object(self.attrCharc)

        self.srv_mng = GATT.GattManager(adapter.list_adapters()[0])
        self.srv_mng.register_application(self.app, {})

        self.dongle = adapter.Adapter(adapter.list_adapters()[0])
        advert = advertisement.Advertisement(1, 'peripheral')

        advert.service_UUIDs = [MY_SRVC]
        # eddystone_data = tools.url_to_advert(WEB_BLINKT, 0x10, TX_POWER)
        # advert.service_data = {EDDYSTONE: eddystone_data}
        if not self.dongle.powered:
            self.dongle.powered = True
        ad_manager = advertisement.AdvertisingManager(self.dongle.address)
        ad_manager.register_advertisement(advert, {})

    def start_bt(self):
        # self.light.StartNotify()
        self.app.start()

def writeBytes(file, value = 65535):
    f = None
    try:
        f = open(file, "wb+")
        f.write(struct.pack('H', value))
    finally:
        if f is not None:
            f.close()

def readBytesAsValue(file):
    b = readBytes(file)
    return struct.unpack('H', b)

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

def enable_ble():
    print('enabling bluetooth')
    try:
        os.system('sudo systemctl start bluetooth.service && sudo hciconfig hci0 up && sudo hciconfig hci0 piscan && sudo hciconfig hci0 leadv')
    except Exception as e:
        print(e)

time.sleep(10)
enable_ble()
dongles = adapter.list_adapters()
print('dongles available: ', dongles)
dongle = adapter.Adapter(dongles[0])
print('address: ', dongle.address)
print('name: ', dongle.name)
print('alias: ', dongle.alias)
print('powered: ', dongle.powered)
print('pairable: ', dongle.pairable)
print('pairable timeout: ', dongle.pairabletimeout)
print('discoverable: ', dongle.discoverable)
subprocess.call(['sudo','hciconfig','hci0','piscan'])
pi_cpu_monitor = ble()
pi_cpu_monitor.start_bt()
