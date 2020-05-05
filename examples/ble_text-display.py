# Example-code for displaying text transmitted by using the BLE Connect UART
# To use, start this program, and start the Adafruit Bluefruit LE Connect app.
# Connect, and then select UART

from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService
import digitalio
import busio
import board
import struct
import os
from pl_uc8156 import PL_UC8156


ble = BLERadio()
uart_server = UARTService()
advertisement = ProvideServicesAdvertisement(uart_server)

# define the pins we will need
clk = board.SCK                             # clock
mosi = board.MOSI                           # MOSI
miso = board.MISO                           # MISO
cs = digitalio.DigitalInOut(board.D5)       # chip-select
rst = digitalio.DigitalInOut(board.D12)     # reset
busy = digitalio.DigitalInOut(board.D9)     # busy

# create the spi-device
spi = busio.SPI(clock = clk, MOSI = mosi, MISO = miso)

# give them all to our driver
display = PL_UC8156(spi = spi, cs_pin = cs, rst_pin = rst, busy_pin = busy)

# OPTIONAL: set the rotation of the image
# 0 = 0° rotation (default)
# 1 = 90° rotation clockwise
# 2 = 180° rotation clockwise
# 3 = 270° rotation clockwise
display.setrotation(0)

# define fontfile used for displaying the text
FONTFILE = 'font5x8.bin'

# helper-function to extract character-dimensions from the fontfile
def gettextdim(font_name = FONTFILE):
    try:
        font = open(font_name, 'rb')
        font_width, font_height = struct.unpack('BB', font.read(2))
    except OSError:
            print("Could not find font file", font_name)
    font.close()
    return font_width, font_height
    
char_width = gettextdim(FONTFILE)[0]
char_height = gettextdim(FONTFILE)[1]

# starting position for text
# NOTE: The used cordinate-systems origin is at the top-left, 
# X-positive right, Y-positive down
_x = 1
_y = 1

# amount of characters fitting on the display per line
char_line = (display._width - _x) // (char_width + 1)

# Define textcolor
# 0 = black, 1 = dark gray, 2 = light gray, 3 = white
_color = 0

# Begin communication with the display and initialize it
# may trigger an additional hardware-reset if needed (already done in __init__-sequence)
display.begin(reset = False)

# Clears the display-content and performs a white-black-white update-cycle 
# to reliable remove any artifacts from previous images
display.whiteerase()

while True:
    print("WAITING...")
    # Advertise when not connected.
    ble.start_advertising(advertisement)
    while not ble.connected:
        pass

    # Connected
    ble.stop_advertising()
    print("CONNECTED")

    # Loop and read packets
    while ble.connected:
        if uart_server.in_waiting:
            # Requires a newline character at the end (the Adafruit Bluefruit LE Connect app can be set to add this automatically)
            # If transmitted text-strings are expected to be very long, use
            # the uart_server.readinto(enter_buffername_here) method instead
            raw_bytes = uart_server.readline()
            text = raw_bytes.decode().strip()
            num_lines = len(text) // char_line
            if ((len(text) % char_line) > 0):
                num_lines += 1
            print("text =", text)
            
            # auto-wraps, -scrolls and displays the received text-string
            for line in range(0, num_lines, 1):
                start = line * char_line
                if (line == (num_lines - 1)):
                        end = start + (len(text) % char_line)
                else:
                    end = start + char_line
                    
                display.text(string = text[start:end], x = _x, y = _y, color = _color, font_name = FONTFILE)
                display.update(0)
                
                if ((_y + char_height + 1) > (display._height - char_height)):
                    if (display.rotation == 0):
                        x_offset = 0
                        y_offset = -1 - char_height
                    elif (display.rotation == 1):
                        x_offset = char_height + 1
                        y_offset = 0
                    elif (display.rotation == 2):
                        x_offset = 0
                        y_offset = char_height + 1
                    elif (display.rotation == 3):
                        x_offset = -1 - char_height
                        y_offset = 0
                    display._framebuf.scroll(delta_x = x_offset, delta_y = y_offset)
                    display.fill_rect(_x, _y, display._width, char_height + 1, 3)                    
                else:
                    _y += char_height + 1
 
    # Disconnected