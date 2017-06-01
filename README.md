# raspberry-bluetooth
Python script to configure a raspberry's wifi conenction through bluetooth.

Edit /etc/systemd/system/dbus-org.bluez.service and add '-C' after 'bluetoothd'. Reboot.

hciconfig hci0 piscan
