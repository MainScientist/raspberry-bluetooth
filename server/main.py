from bluetooth import *
from wifi import Cell, Scheme
import json
import socket


def send(d):
    client_sock.send(json.dumps(d).encode("utf-8"))


def scan():
    ret = {}
    cells = list(Cell.all("wlan0"))
    value = []
    print(cells)
    for c in cells:
        ret[c.ssid.strip()] = c
    return ret


server_sock=BluetoothSocket( RFCOMM )
server_sock.bind(("", PORT_ANY))
server_sock.listen(1)

port = server_sock.getsockname()[1]

uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"

advertise_service(server_sock, "SampleServer",
                  service_id=uuid,
                  service_classes=[uuid, SERIAL_PORT_CLASS],
                  profiles=[SERIAL_PORT_PROFILE],
#                  protocols = [ OBEX_UUID ]
                 )


CELLS = scan()
while True:
    print("Waiting for connection on RFCOMM channel %d" % port)
    client_sock, client_info = server_sock.accept()
    print("Accepted connection from ", client_info)
    try:
        while True:
            data = client_sock.recv(1024)
            if len(data) == 0: break
            command = json.loads(data.decode("utf-8"))
            if command["action"] == "list":
                cells = list(Cell.all("wlan0"))
                value = []
                for c in CELLS:
                    value.append(c)
                send({"value": value})
            elif command["action"] == "connect":
                cell = CELLS[command["args"][0]]
                scheme = Scheme.for_cell('wlan0', 'home', cell, command["args"][1])
                scheme.save()
                scheme.activate()
                send({})
            elif command["action"] == "address":
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                address = s.getsockname()[0]
                s.close()
                send({"value": address})
            elif command["action"] == "rescan":
                CELLS = scan()
                send({})
            elif command["action"] == "exit":
                break
            print("received [%s]" % data)
    except IOError:
        pass
    finally:
        print("disconnected")
        client_sock.close()

server_sock.close()
print("all done")
