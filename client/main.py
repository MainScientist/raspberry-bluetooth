from bluetooth import *
import sys
import json

if sys.version < '3':
    input = raw_input

# search for the SampleServer service
uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"
service_matches = find_service(uuid = uuid)

if len(service_matches) == 0:
    print("couldn't find the SampleServer service =(")
    sys.exit(0)

first_match = service_matches[0]
port = first_match["port"]
name = first_match["name"]
host = first_match["host"]

print("connecting to \"%s\" on %s" % (name, host))

# Create the client socket
sock=BluetoothSocket(RFCOMM)
sock.connect((host, port))

print("connected.  type stuff")
while True:
    data = input()
    if len(data) == 0: break
    sock.send(json.dumps({"command": data}).encode("utf-8"))
    response = sock.recv(1024)
    print(response)

sock.close()
