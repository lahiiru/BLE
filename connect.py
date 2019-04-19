from bluepy import btle
from bluepy.btle import Scanner, DefaultDelegate, BTLEException

SVC_UUID = "12341000-1234-1234-1234-123456789abc"
DEV_IDS_CHR = "6E400003-B5A3-F393-E0A9-E50E24DCCA9A"
DEV_ATTR_CHRC = '6E400003-B5A3-F393-E0A9-E50E24DCCA9B'

class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    def handleDiscovery(self, dev, isNewDev, isNewData):
        if isNewDev:
            print("Discovered device", dev.addr)
        elif isNewData:
            print("Received new data from", dev.addr)


def scan():
    devices_set = set()
    scanner = Scanner().withDelegate(ScanDelegate())
    devices = scanner.scan(2.0)
    for dev in devices:
        for (adtype, desc, value) in dev.getScanData():
            if value == SVC_UUID:
                print("Device %s (%s), RSSI=%d dB" % (dev.addr, dev.addrType, dev.rssi))
                print("  %s = %s" % (desc, value))
                devices_set.add(dev.addr)
    return devices_set


def read_data(address):
    print("Connecting to", address)
    data = ''
    tries = 5
    while tries > 0:
        try:
            tries -= 1
            dev = btle.Peripheral(address)
            service = dev.getServiceByUUID(btle.UUID(SVC_UUID))
            for svc in dev.services:
                print(str(svc))
            for ch in service.getCharacteristics():
                print(str(ch))
            idsChrc = service.getCharacteristics(btle.UUID(DEV_IDS_CHR))[0]
            attrChrc = service.getCharacteristics(btle.UUID(DEV_ATTR_CHRC))[0]
            idsBytes = idsChrc.read()
            attrBytes = attrChrc.read()
            ids = bytes(idsBytes)
            attrs = bytes(attrBytes).decode('utf-8')
            print("ids, attrs", ids, attrs)
            break
        except Exception as e:
            print(e)
    return data


scan()
read_data("B8:27:EB:E8:82:9C")
