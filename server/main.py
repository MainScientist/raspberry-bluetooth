from bluetooth import *
from wifi import Cell, Scheme
import json
import socket
import subprocess
import os
import sys
import git
import os


class Server:

    def __init__(self):
        self.socket=BluetoothSocket( RFCOMM )
        self.socket.bind(("", PORT_ANY))
        self.socket.listen(1)
        self.uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"
        self.cells = {}
        self.schemes = {}
        self.shut_down = False
        self.client = None
        self.exit = False
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.g = git.cmd.Git(dir_path)

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
        cs = list(Cell.all('wlan0'))
        for c in cs:
            self.cells[c.ssid.replace(" ", "").strip()] = c
        schs = list(Scheme.all())
        for s in schs:
            self.schemes[s.name] = s

    def accept(self):
        self.client, client_info = self.socket.accept()
        print("Accepted connection from ", client_info)
        try:
            self.client_loop()
        except IOError:
            pass
        finally:
            print("Client disconnected")
            self.client.close()

    def client_loop(self):
        self.exit = False
        while not self.exit:
            try:
                command = self.receive()
                self.process_command(command["action"], command["args"])
            except Exception as e:
                self.send({"error": str(e)})

    def receive(self):
        # TODO: MORE COMPLEX AND ENCRYPTION
        data = self.client.recv(1024)
        return json.loads(data.decode("utf-8"))

    def process_command(self, action, args):
        if action == "list":
            self.scan()
            value = ["--saved--"]
            for s in self.schemes:
                value.append(s)
            value.append("--scanned--")
            for c in self.cells:
                value.append(c)
            self.send({"value": value})
        elif action == "connect":
            if args[0] in self.schemes:
                scheme = self.schemes[args[0]]
            else:
                cell = self.cells[args[0]]
                scheme = Scheme.for_cell('wlan0', args[0], cell, args[1])
            try:
                scheme.save()
            except AssertionError:
                # Schema already saved
                pass
            try:
                scheme.activate()
                self.send({"value": "Successfully connected to network."})
            except Exception as e:
                self.send({"value": "{} Please try again.".format(e)})
        elif action == "test":
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                address = s.getsockname()[0]
                self.send({"value": "OK"})
            except IOError:
                self.send({"value": "You are not connected to the internet."})
            finally:
                s.close()
        elif action == "update":
            out = self.g.pull()
            self.send({"value": out.decode("utf-8")})

            self.exit = True
            self.shut_down = True
            self.restart = True
        elif action == "ifconfig":
            out = subprocess.check_output(["ifconfig", "wlan0"])
            self.send({"value": out.decode("utf-8")})
        elif action == "exec":
            out = subprocess.check_output(args)
            self.send({"value": out.decode("utf-8")})
        elif action == "exit":
            self.exit = True
        elif action == "shut_down":
            self.exit = True
            self.shut_down = True
        else:
            self.send({"error": "Command does not exist."})

    def send(self, d):
        msg = json.dumps(d).encode("utf-8")
        print(msg)
        self.client.send(msg)

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
