from bluepy.btle import Scanner, DefaultDelegate, BTLEException
from bluepy import btle

MY_SRVC = '12341000-1234-1234-1234-123456789abb'


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
            #if value == SVC_UUID:
            print("Device %s (%s), RSSI=%d dB" % (dev.addr, dev.addrType, dev.rssi))
            print("  %s = %s" % (desc, value))
            devices_set.add(dev.addr)
            d = btle.Peripheral(dev.addr)
            print(value)
            service = d.getServiceByUUID(btle.UUID(MY_SRVC))
            for svc in d.services:
                print(str(svc))
            for ch in service.getCharacteristics():
                print(str(ch))
    return devices_set

scan()