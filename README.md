# iDRAC-solar-controller
My old server automation startup/shutdown script

This script uses the data recieved from InfluxDB to control the power onn and off functionaity of a Dell R710 using the iDRAC interface commands.

The data in InfluxDB is provided by an ESP32 connected to a Renogy Solar controller running a slight variation upon this repository code [ESP32ArduinoRenogy](https://github.com/wrybread/ESP32ArduinoRenogy)

