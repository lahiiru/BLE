from time import sleep
from bluezero import central

SERVICE_UUID = '12341000-1234-1234-1234-123456789abc'
CHARAC_UUD = '6E400003-B5A3-F393-E0A9-E50E24DCCA9A'
DEVICE_ADDR = 'B8:27:EB:E9:56:52'
ADAPTER_ADDR = 'B8:27:EB:86:40:31'

class MyPeripheralDevice:
    def __init__(self, device_addr, adapter_addr=None):
        self.remote_device = central.Central(adapter_addr=adapter_addr,
                                             device_addr=device_addr)
        self._remote_charac = self.remote_device.add_characteristic(SERVICE_UUID,
                                                                    CHARAC_UUD)

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

    def subscribe(self, user_callback):
        self._remote_charac.add_characteristic_cb(user_callback)
        self._remote_charac.start_notify()

    def run_async(self):
        self.remote_device.run()


if __name__ == '__main__':
    my_dev = MyPeripheralDevice(adapter_addr=ADAPTER_ADDR,
                                device_addr=DEVICE_ADDR)
    my_dev.connect()
    my_dev.subscribe(print)
    my_dev.run_async()
