from bluetooth import *

server_socket=BluetoothSocket( RFCOMM )

server_socket.bind(("",PORT_ANY))
server_socket.listen(1)

advertise_service(server_socket, "helloService",
                     service_classes=[SERIAL_PORT_CLASS],
                     profiles=[SERIAL_PORT_PROFILE])

while True:
    try:
        client_socket, address = server_socket.accept()
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
    except KeyboardInterrupt:
        break
    except Exception as e:
        print(e)

server_socket.close()
