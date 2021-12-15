# BMP180 sensor driver for Home Assistant used in Raspberry Pi
Custom component BMP180 sensor for Home Assistant.

Copy the content of this directory to your homeassistant config directory:
  - example: ./config/custom_components/dev_747_BMP180/

##Requirements:
Enable I2C communication in Raspberry via raspi-config and install dependencies for handeling I2C communication in Python
```ruby
sudo apt-get update
sudo apt-get install python3-smbus python3-dev i2c-tools
```

##Parameters:
  - i2c_address: I2C address of BMP180 (typical 0x77)
  - i2c_bus_num: I2C bus number (default raspberry = 1)
  - name: custom name of the sensor
  - mode: 0 - Ultra low power, 1 - standard, 2 - high resolution, 3 - ultra high resolution
  - monitored_conditions: temperature, pressure, altitude

Exaple configuration.yaml file:
```ruby
sensor:
  - platform: dev747_AM2320
    i2c_address: 0x77
    i2c_bus_num: 1
    name: "BMP180"
    mode: 3
    monitored_conditions:
      - temperature
      - pressure
      - altitude
    scan_interval: 2 
```
