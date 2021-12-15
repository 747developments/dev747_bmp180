from __future__ import annotations

__version__ = '1.0.0'

import logging
import os
import time
import voluptuous as vol
import smbus
import math

from homeassistant.components.sensor import PLATFORM_SCHEMA, ENTITY_ID_FORMAT, SensorEntity
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity, async_generate_entity_id
from homeassistant.components.group import expand_entity_ids
from homeassistant.const import (
    ATTR_ATTRIBUTION,
    ATTR_BATTERY_LEVEL,
    CONF_DEVICES,
    CONF_TEMPERATURE_UNIT,
    CONF_NAME,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
    PERCENTAGE,
    CONF_SENSORS,
    CONF_MONITORED_CONDITIONS
)

DEF_SEA_LEVEL_PRESSURE = 101325.0

# Operating Modes
BMP085_ULTRALOWPOWER     = 0
BMP085_STANDARD          = 1
BMP085_HIGHRES           = 2
BMP085_ULTRAHIGHRES      = 3

# BMP180 registers
CONTROL_REG = 0xF4
DATA_REG = 0xF6

# Calibration data registers
CAL_AC1_REG = 0xAA
CAL_AC2_REG = 0xAC
CAL_AC3_REG = 0xAE
CAL_AC4_REG = 0xB0
CAL_AC5_REG = 0xB2
CAL_AC6_REG = 0xB4
CAL_B1_REG = 0xB6
CAL_B2_REG = 0xB8
CAL_MB_REG = 0xBA
CAL_MC_REG = 0xBC
CAL_MD_REG = 0xBE

# Calibration data variables
calAC1 = 0
calAC2 = 0
calAC3 = 0
calAC4 = 0
calAC5 = 0
calAC6 = 0
calB1 = 0
calB2 = 0
calMB = 0
calMC = 0
calMD = 0


DOMAIN                  = "dev_747_bmp180"
DEFAULT_NAME            = "I2C Sensor"
SENSOR_TEMP             = "temperature"
SENSOR_PRESS            = "pressure"
SENSOR_ALT              = "altitude"

_SENSOR_TYPES = {
    "temperature":  ("Temperature",     "",     "mdi:thermometer",      "°C"),
    "pressure":     ("Pressure",        "",     "mdi:gauge",            "Pa"),
    "altitude":     ("Altitude",        "",     "mdi:image-filter-hdr", "m"),
}

DEFAULT_I2C_ADDRESS     = "0x77"
DEFAULT_I2C_BUS         = 1

CONF_I2C_ADDRESS        = "i2c_address"
CONF_I2C_BUS_NUM        = "i2c_bus_num"
CONF_NAME               = "name"
CONF_MODE               = "mode"

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_I2C_ADDRESS, default=DEFAULT_I2C_ADDRESS): cv.positive_int,
    vol.Required(CONF_I2C_BUS_NUM, default=DEFAULT_I2C_BUS): cv.positive_int,
    vol.Required(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Required(CONF_MODE, default=BMP085_HIGHRES): cv.positive_int,
    vol.Required(CONF_MONITORED_CONDITIONS): vol.All(
            cv.ensure_list, [vol.In(_SENSOR_TYPES)]
        ),
})

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the sensor platform."""

    # if discovery_info is None:
        # return
    i2c_address = config.get(CONF_I2C_ADDRESS)
    i2c_bus_num = config.get(CONF_I2C_BUS_NUM)
    name = config.get(CONF_NAME)
    mode = config.get(CONF_MODE)
    #_LOGGER.warning(config[CONF_MONITORED_CONDITIONS])
    for monitored_condition in config[CONF_MONITORED_CONDITIONS]:
        async_add_entities([BMP180(name, i2c_address, i2c_bus_num, monitored_condition, mode)])

class BMP180(SensorEntity):

    def __init__(self, name, i2c_address, i2c_bus_num, monitored_condition, mode):
        """Initialize the sensor."""
        self._monitored_condition = monitored_condition
        self._name = name
        self._state = None
        self.raw_data = None
 
        self._i2c_bus_num = i2c_bus_num
        self._i2c_address = i2c_address        
        self._i2c_bus = smbus.SMBus(self._i2c_bus_num)  

        if mode not in [BMP085_ULTRALOWPOWER, BMP085_STANDARD, BMP085_HIGHRES, BMP085_ULTRAHIGHRES]:
            raise ValueError('Unexpected mode value {0}.  Set mode to one of BMP085_ULTRALOWPOWER, BMP085_STANDARD, BMP085_HIGHRES, or BMP085_ULTRAHIGHRES'.format(mode))
        
        self.mode = mode
        self.read_calibration_data()
        
        return      
    
    def read_signed_16_bit(self, register):
        """Reads a signed 16-bit value.
        register -- the register to read from.
        Returns the read value.
        """
        msb = self._i2c_bus.read_byte_data(self._i2c_address, register)
        lsb = self._i2c_bus.read_byte_data(self._i2c_address, register + 1)

        if msb > 127:
            msb -= 256

        return (msb << 8) + lsb

    def read_unsigned_16_bit(self, register):
        """Reads an unsigned 16-bit value.
        Reads the given register and the following, and combines them as an
        unsigned 16-bit value.
        register -- the register to read from.
        Returns the read value.
        """
        msb = self._i2c_bus.read_byte_data(self._i2c_address, register)
        lsb = self._i2c_bus.read_byte_data(self._i2c_address, register + 1)

        return (msb << 8) + lsb

    # BMP180 interaction methods

    def read_calibration_data(self):
        """Reads and stores the raw calibration data."""
        self.calAC1 = self.read_signed_16_bit(CAL_AC1_REG)
        self.calAC2 = self.read_signed_16_bit(CAL_AC2_REG)
        self.calAC3 = self.read_signed_16_bit(CAL_AC3_REG)
        self.calAC4 = self.read_unsigned_16_bit(CAL_AC4_REG)
        self.calAC5 = self.read_unsigned_16_bit(CAL_AC5_REG)
        self.calAC6 = self.read_unsigned_16_bit(CAL_AC6_REG)
        self.calB1 = self.read_signed_16_bit(CAL_B1_REG)
        self.calB2 = self.read_signed_16_bit(CAL_B2_REG)
        self.calMB = self.read_signed_16_bit(CAL_MB_REG)
        self.calMC = self.read_signed_16_bit(CAL_MC_REG)
        self.calMD = self.read_signed_16_bit(CAL_MD_REG)
        # _LOGGER.warning(self.calAC1)
        # _LOGGER.warning(self.calAC2)
        # _LOGGER.warning(self.calAC3)
        # _LOGGER.warning(self.calAC4)
        # _LOGGER.warning(self.calAC5)
        # _LOGGER.warning(self.calB1)
        # _LOGGER.warning(self.calB2)
        # _LOGGER.warning(self.calMB)
        # _LOGGER.warning(self.calMC)
        # _LOGGER.warning(self.calMD)        
        
    def get_raw_temp(self):
        """Reads and returns the raw temperature data."""
        # Write 0x2E to CONTROL_REG to start the measurement
        self._i2c_bus.write_byte_data(self._i2c_address, CONTROL_REG, 0x2E)

        # Wait 4,5 ms
        time.sleep(0.05)

        # Read the raw data from the DATA_REG, 0xF6
        raw_data = self.read_unsigned_16_bit(DATA_REG)

        # Return the raw data
        return raw_data

    def get_raw_pressure(self):
        """Reads and returns the raw pressure data."""
        # Write appropriate data to sensor to start the measurement
        self._i2c_bus.write_byte_data(self._i2c_address, CONTROL_REG, 0x34 + (self.mode << 6))

        # Sleep for 8 ms.
        # TODO: Way to use the correct wait time for the current mode
        time.sleep(0.05)

        MSB = self._i2c_bus.read_byte_data(self._i2c_address, DATA_REG)
        LSB = self._i2c_bus.read_byte_data(self._i2c_address, DATA_REG + 1)
        XLSB = self._i2c_bus.read_byte_data(self._i2c_address, DATA_REG + 2)

        raw_data = ((MSB << 16) + (LSB << 8) + XLSB) >> (8 - self.mode)

        return MSB, LSB, XLSB 

    def get_temp(self):
        """Reads the raw temperature and calculates the actual temperature.
        The calculations used to get the actual temperature are from the BMP-180
        datasheet.
        Returns the actual temperature in degrees Celcius.
        """
        UT = self.get_raw_temp()

        X1 = 0
        X2 = 0
        B5 = 0
        actual_temp = 0.0

        X1 = ((UT - self.calAC6) * self.calAC5) / math.pow(2, 15)
        X2 = (self.calMC * math.pow(2, 11)) / (X1 + self.calMD)
        B5 = X1 + X2
        actual_temp = ((B5 + 8) / math.pow(2, 4)) / 10

        return round(actual_temp, 1)

    def get_pressure(self):
        """Reads and calculates the actual pressure.
        Gets the compensated pressure in Pascals."""
        UT = self.get_raw_temp()
        X1 = 0
        X2 = 0
        B5 = 0
        X1 = ((UT - self.calAC6) * self.calAC5) / math.pow(2, 15)
        X2 = (self.calMC * math.pow(2, 11)) / (X1 + self.calMD)
        B5 = X1 + X2
        
        MSB, LSB, XLSB = self.get_raw_pressure()        
        UP = ((MSB << 16)+(LSB << 8)+XLSB) >> (8-self.mode)
        B6 = B5-4000
        X1 = (self.calB2*(B6**2/2**12))/2**11
        X2 = self.calAC2*B6/2**11
        X3 = X1+X2
        B3 = ((int((self.calAC1*4+X3)) << self.mode)+2)/4
        X1 = self.calAC3*B6/2**13
        X2 = (self.calB1*(B6**2/2**12))/2**16
        X3 = ((X1+X2)+2)/2**2
        B4 = abs(self.calAC4)*(X3+32768)/2**15
        B7 = (abs(UP)-B3) * (50000 >> self.mode)
        if B7 < 0x80000000:
            pressure = (B7*2)/B4
        else:
            pressure = (B7/B4)*2
        X1 = (pressure/2**8)**2
        X1 = (X1*3038)/2**16
        X2 = (-7357*pressure)/2**16
        return round(pressure+(X1+X2+3791)/2**4, 0)

    def get_altitude(self):
        """Calulates the altitude.
        This method calculates the altitude using the pressure.
        This method is not reliable when the sensor is inside.
        """
        pressure = float(self.get_pressure())

        altitude = 44330.0 * (1.0 - pow(pressure / DEF_SEA_LEVEL_PRESSURE, (1.0/5.255)))

        return round(altitude, 1)
    
    def get_data(self):
        
        try:   
            #_LOGGER.warning(self._monitored_condition == SENSOR_TEMP)
            if self._monitored_condition == SENSOR_TEMP:                
                self._state = self.get_temp()               
            elif self._monitored_condition == SENSOR_PRESS:              
                self._state = self.get_pressure()
            elif self._monitored_condition == SENSOR_ALT:  
                self._state = self.get_altitude()    
        except Exception as ex:
            _LOGGER.error("Error retrieving BMP180 data: %s" % (ex))
       
    @property
    def name(self):
        """Return the name of the entity."""
        return "{} - {}".format(self._name, _SENSOR_TYPES[self._monitored_condition][0])
        
    @property
    def state(self):
        """Return the state of the entity."""
        return self._state

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        return _SENSOR_TYPES[self._monitored_condition][2]

    async def async_update(self):
        self.get_data()

    @property
    def unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        return _SENSOR_TYPES[self._monitored_condition][3]