from bluetooth import *
from time import sleep
import re, uuid

devices = set()
devices_to_update = set()

dev_mac = ':'.join(re.findall('..', '%012x' % uuid.getnode())).upper()
print(dev_mac)


def enable_ble():
    print('enabling bluetooth')
    try:
        os.system('sudo systemctl start bluetooth.service && sudo hciconfig hci0 up')
    except Exception as e:
        print(e)


def job():
    print("\n\nPerforming inquiry...")
    new_devices = set()
    global devices_to_update

    services = find_service(name="helloService")
    print(services)

    for i in range(len(services)):
        match = services[i]
        if match["name"] == "helloService":
            port = match["port"]
            name = match["name"]
            host = match["host"]
            print(name, port, host)
            new_devices.add(host)

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

    if devices_modified: # need to notify to all devices
        devices_to_update = devices_to_update.union(devices)

    if len(devices_to_update) > 0:
        update_message = "%sEOD" % devices
        print("Update message = %s" % update_message)
        for addr in devices_to_update.copy():
            try:
                print("Connecting to %s to send updated list" % addr)
                client_socket = BluetoothSocket(RFCOMM)
                client_socket.connect((addr, 1))

                client_socket.send(update_message)
                print("Sent to %s" % addr)
                client_socket.close()
                devices_to_update.remove(addr)
            except Exception as e:
                print(e)
    else:
        print("No updates to send")


enable_ble()

while True:
    job()
    sleep(5)
