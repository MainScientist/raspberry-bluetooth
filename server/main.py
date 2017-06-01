from bluetooth import *
from wifi import Cell, Scheme
import json
import socket
import subprocess
import os
import sys


def send(d):
    client_sock.send(json.dumps(d).encode("utf-8"))


def scan():
    ret = {}
    cells = list(Cell.all("wlan0"))
    value = []
    print(cells)
    for c in cells:
        ret[c.ssid.strip().replace(" ", "")] = c
    return ret


print("Running server...")
server_sock=BluetoothSocket( RFCOMM )
server_sock.bind(("", PORT_ANY))
server_sock.listen(1)

port = server_sock.getsockname()[1]

uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"

advertise_service(server_sock, "BluetoothWifiConfig",
                  service_id=uuid,
                  service_classes=[uuid, SERIAL_PORT_CLASS],
                  profiles=[SERIAL_PORT_PROFILE],
#                  protocols = [ OBEX_UUID ]
                 )


CELLS = scan()
conditions = {"shut_down": False, "restart": False}
while not conditions["shut_down"]:
    print(conditions)
    print("Waiting for connection on RFCOMM channel %d" % port)
    client_sock, client_info = server_sock.accept()
    print("Accepted connection from ", client_info)
    try:
        while True:
            data = client_sock.recv(1024)
            if len(data) == 0: break
            command = json.loads(data.decode("utf-8"))
            action = command["action"]
            args = command["args"]
            if action == "list":
                cells = list(Cell.all("wlan0"))
                value = []
                for c in CELLS:
                    value.append(c)
                send({"value": value})
            elif action == "connect":
                cell = CELLS[args[0]]
                scheme = Scheme.for_cell('wlan0', 'home', cell, args[1])
                try:
                    scheme.activate()
                    scheme.save()
                    send({"value": "Successfully connected to network."})
                except AssertionError:
                    # Schema already saved
                    pass
                except:
                    send({"value": "Something went wrong. Please try again."})

            elif action == "address":
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    s.connect(("8.8.8.8", 80))
                    address = s.getsockname()[0]
                    send({"value": address})
                except IOError:
                    send({"value": "Something went wrong!"})
                finally:
                    s.close()
            elif action == "rescan":
                CELLS = scan()
                send({})
            elif action == "update":
                out = subprocess.check_output(["git", "pull", "origin", "master"])
                send({"value": out.decode("utf-8")})

                conditions["shut_down"] = True
                conditions["restart"] = True
                break
            elif action == "ifconfig":
                out = subprocess.check_output(["ifconfig"])
                send({"value": out.decode("utf-8")})
            elif action == "exit":
                break
            elif action == "shut_down":
                conditions["shut_down"] = True
                break
            print("received [%s]" % data)
    except IOError as e:
        print(e)
    finally:
        print(conditions)
        print("disconnected")
        client_sock.close()

server_sock.close()
if conditions["restart"]:
    os.execv(sys.executable, ['python3'] + sys.argv)
print("all done")
