# Standard modules
import dbus
import subprocess
import os
import logging
import time
try:
    from gi.repository import GObject
except ImportError:
    import gobject as GObject

# Bluezero modules
from bluezero import adapter
from bluezero import advertisement
from bluezero import localGATT
from bluezero import GATT, constants
from config import DEV_ATTR_CHRC, DEV_IDS_CHRC, SVC_UUID
import struct

# constants


logging.basicConfig(filename='transmitter.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)

logging.info('Starting transmitter...')


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
                                          ['read', 'notify'])

    def ReadValue(self, options):
        try:
            logging.info("A device is reading ID profile.")
            bs = readBytes('/home/pi/id')
            array = getByteArrayFromBytes(bs)
            logging.info("Returning %s", bs)
            return dbus.Array(array)
        except Exception as e:
            logging.error(e)
            return dbus.Array([])


class DeviceAttrChrc(localGATT.Characteristic):
    def __init__(self, service):
        localGATT.Characteristic.__init__(self,
                                          2,
                                          DEV_ATTR_CHRC,
                                          service,
                                          [dbus.Byte("1".encode('utf-8'))],
                                          False,
                                          ['read', 'notify'])

    def ReadValue(self, options):
        logging.info("A device is reading attribute profile")
        array = getByteArrayFromString("batt=20%")
        return dbus.Array(array)

    def StartNotify(self):
        if self.props[constants.GATT_CHRC_IFACE]['Notifying']:
            logging.info('Already notifying, nothing to do')
            return
        logging.info('Notifying on')
        self.props[constants.GATT_CHRC_IFACE]['Notifying'] = True
        self._update_temp_value()

    def StopNotify(self):
        if not self.props[constants.GATT_CHRC_IFACE]['Notifying']:
            logging.info('Not notifying, nothing to do')
            return

        logging.info('Notifying off')
        self.props[constants.GATT_CHRC_IFACE]['Notifying'] = False
        self._update_temp_value()

    def _update_temp_value(self):
        if not self.props[constants.GATT_CHRC_IFACE]['Notifying']:
            return

        logging.info('Starting timer event')
        GObject.timeout_add(2000, self.temperature_cb)

    def temperature_cb(self):
        reading = [5]
        logging.info('Getting new temperature',
              reading,
              self.props[constants.GATT_CHRC_IFACE]['Notifying'])
        self.props[constants.GATT_CHRC_IFACE]['Value'] = reading

        self.PropertiesChanged(constants.GATT_CHRC_IFACE,
                               {'Value': self.ReadValue({})},
                               [])
        logging.info('Array value: ', reading)
        return self.props[constants.GATT_CHRC_IFACE]['Notifying']


class ble:
    def __init__(self):
        self.bus = dbus.SystemBus()
        self.app = localGATT.Application()
        self.srv = localGATT.Service(1, SVC_UUID, True)

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

        advert.service_UUIDs = [SVC_UUID]
        # eddystone_data = tools.url_to_advert(WEB_BLINKT, 0x10, TX_POWER)
        # advert.service_data = {EDDYSTONE: eddystone_data}
        if not self.dongle.powered:
            self.dongle.powered = True
        ad_manager = advertisement.AdvertisingManager(self.dongle.address)
        ad_manager.register_advertisement(advert, {})

    def start_bt(self):
        self.idsCharc.StartNotify()
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
    logging.info('enabling bluetooth')
    try:
        os.system('sudo systemctl start bluetooth.service && sudo hciconfig hci0 up && sudo hciconfig hci0 piscan && sudo hciconfig hci0 leadv')
    except Exception as e:
        logging.info(e)

time.sleep(10)
enable_ble()
dongles = adapter.list_adapters()
dongle = adapter.Adapter(dongles[0])
logging.info('address: ' + dongle.address)
logging.info('name: ' + dongle.name)
logging.info('alias: ' + dongle.alias)
logging.info('powered: %s', dongle.powered)
logging.info('pairable: %s', dongle.pairable)
logging.info('pairable timeout: %s', dongle.pairabletimeout)
logging.info('discoverable: %s', dongle.discoverable)
pi_cpu_monitor = ble()
pi_cpu_monitor.start_bt()
