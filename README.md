# APRS Weather

Reads the temperature from a DS1820 1-Wire sensor and sends the reading to APRS.

## Configuration

### DS1820

To enable the DS1820 on a Raspberry Pi. Add the following line in the
`/boot/config.txt` file, then reboot.

```
dtoverlay=w1-gpio
```

Once your system has been rebooted, go to /sys/bus/w1/devices (`cd sys/bus/w1/devices`) and list the files. You should find a directory
named `28-XXXXXXXXXX`. The `XXXXXXXXXX` correspond to the address of your device.

### Configuring aprs_wx

Create a file `aprs_wx.conf` into `/etc`. You can use the file
`aprs_ws.conf-sample` as an inspiration.

```
[APRS]
call: HAMRADIO_CALL_SIGN
passcode: 98765
sleep: 900
latitude: 38.4599
longitude: -120.2405
w1_temp: /sys/bus/w1/devices/28-3c01f095702b/w1_slave
```

Add your call sign, passcode. You can use google maps to find out your
latitude and longitude. You also need to configure the full path for
your one-wire temperature sensor.
