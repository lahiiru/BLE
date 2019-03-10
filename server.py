from bluetooth import *

server_socket=BluetoothSocket( RFCOMM )

server_socket.bind(("",PORT_ANY))
server_socket.listen(10)

advertise_service(server_socket, "helloService",
                     service_classes=[SERIAL_PORT_CLASS],
                     profiles=[SERIAL_PORT_PROFILE])


def enable_ble():
    print('enabling bluetooth')
    try:
        os.system('sudo systemctl start bluetooth.service && sudo hciconfig hci0 up && hciconfig hci0 piscan')
    except Exception as e:
        print(e)


enable_ble()

while True:
    try:
        client_socket, address = server_socket.accept()
        print('Client accepted from ' + address[0])
        data = b''
        while True:
            buf = client_socket.recv(1024)
            data += buf
            if data[-3:] == b'EOD':
                break
            print(len(data))
        data = data[:-3]
        print("received [%s]" % data)
        client_socket.close()
        f = open('global_devices.txt', 'w')
        f.write("%s"%data.decode('utf-8'))
        f.close()
    except KeyboardInterrupt:
        break
    except Exception as e:
        print(e)

server_socket.close()
