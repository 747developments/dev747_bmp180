"""CONSTANTS"""
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