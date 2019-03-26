from bluepy import btle

SVC_UUID = "12341000-1234-1234-1234-123456789abc"
CHR_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9A"


class MyDelegate(btle.DefaultDelegate):
    def __init__(self):
        btle.DefaultDelegate.__init__(self)

    def handleNotification(self, cHandle, data):
        print("A notification was received: %s" %data)


p = btle.Peripheral("B8:27:EB:E9:56:52")
p.setDelegate( MyDelegate() )

# Setup to turn notifications on, e.g.
svc = p.getServiceByUUID( SVC_UUID )
ch = svc.getCharacteristics()[0]
print(ch.valHandle)

p.writeCharacteristic(ch.valHandle+1, b"\x02\x00")

while True:
    if p.waitForNotifications(1.0):
        # handleNotification() was called
        continue

    print("Waiting...")
    # Perhaps do something else here