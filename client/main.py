from bluetooth import *
import sys
import json

if sys.version < '3':
    input = raw_input

# search for the SampleServer service
uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"

attempts = 0

while attempts < 4:
    service_matches = find_service(uuid=uuid, address=None)

    if len(service_matches) > 0:
        break
    attempts += 1
    print("Could not find server. Trying again... ({})".format(attempts))

first_match = service_matches[0]
port = first_match["port"]
name = first_match["name"]
host = first_match["host"]

print("connecting to \"%s\" on %s" % (name, host))

# Create the client socket
sock=BluetoothSocket(RFCOMM)
sock.connect((host, port))

print("connected.")
while True:
    action, *args = input("> ").split(" ")
    if len(action) == 0 or action == "exit": break
    sock.send(json.dumps({"action": action, "args": args}).encode("utf-8"))
    if action == "shut_down": break
    msg = sock.recv(1024*10).decode("utf-8")
    print(msg)
    response = json.loads(msg)
    if "error" in response:
        print(response["error"])
    else:
        if action == "list":
            for e in response["value"]:
                print(e)
        elif action == "test":
            print(response["value"])
        elif action == "connect":
            print(response["value"])
        elif action == "ifconfig":
            print(response["value"])
        elif action == "exec":
            print(response["value"])
        elif action == "update":
            print(response["value"])
            break

sock.close()
