from lcd_api import LcdApi
from machine import I2C
from time import sleep_ms

class I2cLcd(LcdApi):
    def __init__(self, i2c, addr, num_lines, num_columns):
        self.i2c = i2c
        self.addr = addr
        super().__init__(num_lines, num_columns)

    def hal_write_command(self, cmd):
        self.i2c.writeto(self.addr, bytes([cmd]))
        sleep_ms(5)

    def hal_write_data(self, data):
        self.i2c.writeto(self.addr, bytes([data]))
        sleep_ms(1)