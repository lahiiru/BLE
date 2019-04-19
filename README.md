1. Clone the repo and do an apt update  
`sudo apt-get update`  
`sudo apt-get install git -y`   
`git clone https://github.com/lahiiru/BLE.git`  

1. Install dependancies  
`sudo apt-get install python3-pip bluetooth bluez-tools bluez-test-scripts bluez-hcidump python-bluez -y`  

1. Enable experimental bluetooth features by adding *--experimental* flag to following file as below.  
`sudo nano /lib/systemd/system/bluetooth.service`  
   > ExecStart=/usr/lib/bluetooth/bluetoothd --experimental
   
   *Ctrl+O then Crtl+X to save and exit from the nano editor*

1. Apply changes  
`sudo systemctl daemon-reload`  
`sudo service bluetooth restart`

1. Check bluetooth status  
`service bluetooth status` 
``` 
● bluetooth.service - Bluetooth service
   Loaded: loaded (/lib/systemd/system/bluetooth.service; enabled; vendor preset: enabled)
   Active: active (running) since Sat 2019-04-13 16:12:00 UTC; 6s ago
     Docs: man:bluetoothd(8)
 Main PID: 17773 (bluetoothd)
   Status: "Running"
   CGroup: /system.slice/bluetooth.service
           └─17773 /usr/lib/bluetooth/bluetoothd --experimental

systemd[1]: Starting Bluetooth service...
bluetoothd[17773]: Bluetooth daemon 5.43
systemd[1]: Started Bluetooth service.
bluetoothd[17773]: Starting SDP server
bluetoothd[17773]: Bluetooth management interface 1.14 initialized
bluetoothd[17773]: Failed to obtain handles for "Service Changed" characteristic
bluetoothd[17773]: Endpoint registered: sender=:1.32 path=/A2DP/SBC/Source/1
bluetoothd[17773]: Endpoint registered: sender=:1.32 path=/A2DP/SBC/Sink/1
```

6. Clone python-bluezero and copy configurations    
`git clone https://github.com/ukBaz/python-bluezero.git`    
`sudo cp python-bluezero/examples/ukBaz.bluezero.conf /etc/dbus-1/system.d/. && sudo systemctl daemon-reload && sudo service bluetooth restart`   

1. Python-pip dependenices   
`sudo pip3 install bluezero`   
`sudo pip3 install uptime`   
`sudo pip3 install pybluez`  
`sudo pip3 install bluepy`   

1. Schedule running `transmitter.py` at start. Add follwing line to `crontab`  
`crontab -e`   
   > @reboot sleep 20 && sudo python3 /home/pi/BLE/transmitter.py   
   @reboot sleep 25 && sudo python3 /home/pi/BLE/beacon_udp.py
1. Run [BeaconManager.exe](https://github.com/lahiiru/BLE/blob/master/WindowsFormsApp1/bin/Debug/BeaconManager.exe) in a Windows PC and IP of the this PC will be `SERVER_ADD`.  
1. Change the `SERVER_ADD` in `config.py` script and reboot.
