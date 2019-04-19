MY_SRVC = '12341000-1234-1234-1234-123456789abc'
DEV_IDS_CHRC = '6E400003-B5A3-F393-E0A9-E50E24DCCA9A'
DEV_ATTR_CHRC = '6E400003-B5A3-F393-E0A9-E50E24DCCA9B'

R9C = 'B8:27:EB:E8:82:9C' # Kali
R31 = 'B8:27:EB:86:40:31' # RPi

from time import sleep
from bluezero import central

class MyPeripheralDevice:
    def __init__(self, device_addr, adapter_addr):
        self.remote_device = central.Central(adapter_addr=adapter_addr,
                                             device_addr=device_addr)
        self._remote_charac = self.remote_device.add_characteristic(MY_SRVC,
                                                                    DEV_IDS_CHRC)

    def connect(self):
        self.remote_device.connect()
        while not self.remote_device.services_resolved:
            sleep(0.5)
        self.remote_device.load_gatt()

    def disconnect(self):
        self.remote_device.disconnect()

    @property
    def value(self):
        return self._remote_charac.value


if __name__ == '__main__':
    my_dev = MyPeripheralDevice(R9C, R31)

    my_dev.connect()
    print(my_dev.value)
    my_dev.disconnect()
