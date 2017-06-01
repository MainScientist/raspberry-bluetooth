import bluetooth


devices = bluetooth.discover_devices()

for d in devices:
    print(bluetooth.lookup_name(d))
