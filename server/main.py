from bluetooth import *
from wifi import Cell, Scheme
import json
import socket
import subprocess
import os
import sys


class Server:

    def __init__(self):
        self.socket=BluetoothSocket( RFCOMM )
        self.socket.bind(("", PORT_ANY))
        self.socket.listen(1)
        self.uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"
        self.cells = {}
        self.schemes = list(Scheme.all())
        self.shut_down = False
        self.client = None
        self.exit = False

    def serve(self):
        print("Running server")
        port = self.socket.getsockname()[1]
        advertise_service(self.socket, "BluetoothWifiConfig",
                          service_id=self.uuid,
                          service_classes=[self.uuid, SERIAL_PORT_CLASS],
                          profiles=[SERIAL_PORT_PROFILE]
                         )
        self.scan()
        while not self.shut_down:
            self.accept()

    def scan(self):
        self.cells = list(Cell.all('wlan0'))

    def accept(self):
        self.client, client_info = server_sock.accept()
        print("Accepted connection from ", client_info)
        try:
            self.client_loop()
        except IOError:
            pass
        finally:
            print("Client disconnected")
            self.client.close()

    def client_loop(self):
        command = self.receive()
        self.exit = False
        while not self.exit:
            try:
                self.process_command(command["action"], command["args"])
            except Exception as e:
                self.send({"error": str(e)})

    def receive(self):
        # TODO: MORE COMPLEX AND ENCRYPTION
        data = self.socket.recv(1024)
        return json.loads(data.decode("utf-8"))

    def process_command(self, action, args):
        if action == "list":
            self.scan()
            value = ["--saved--"]
            for s in self.schemes:
                value.append(s.name)
            value.append("--scanned--")
            for c in self.cells:
                value.append(c.ssid)
            send({"value": value})
        elif action == "connect":
            cell = self.cells[args[0]]
            scheme = Scheme.for_cell('wlan0', args[1], cell, args[1])
            try:
                scheme.activate()
                scheme.save()
                send({"value": "Successfully connected and saved network."})
            except AssertionError:
                # Schema already saved
                send({"value": "Successfully connected to network."})
            except:
                send({"value": "Something went wrong. Please try again."})
        elif action == "test":
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                address = s.getsockname()[0]
                send({"value": "OK"})
            except IOError:
                send({"value": "You are not connected to the internet."})
            finally:
                s.close()
        elif action == "update":
            out = subprocess.check_output(["git", "pull", "origin", "master"])
            send({"value": out.decode("utf-8")})

            self.exit = True
            self.shut_down = True
            self.restart = True
        elif action == "ifconfig":
            out = subprocess.check_output(["ifconfig", "wlan0"])
            send({"value": out.decode("utf-8")})
        elif action == "exec":
            out = subprocess.check_output(args)
            send({"value": out.decode("utf-8")})
        elif action == "exit":
            self.exit = True
        elif action == "shut_down":
            self.exit = True
            self.shut_down = True

    def send(self, d):
        msg = json.dumps(d).encode("utf-8")
        self.socket.send(msg)

    def close(self):
        self.socket.close()
        if self.restart:
            print("Restarting server...")
            os.execv(sys.executable, ['python3'] + sys.argv)
        print("Server closed")


def main():
    s = Server()
    s.serve()
    s.close()


main()
