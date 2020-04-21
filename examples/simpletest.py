# SETUP
# =====

import digitalio
import busio
import board
from pl_uc8156 import PL_UC8156

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

# OPTIONAL: If you want to change the baudrate of the spi-connection
# (default = 4MHz), uncomment and adapt the next line!
#display.setbaudrate(4000000)

# OPTIONAL: Color-definitions
# The displays support up to 4 grayscale-colors:
WHITE = PL_UC8156.WHITE
LGRAY = PL_UC8156.LGRAY     # light gray
DGRAY = PL_UC8156.DGRAY     # dark gray
BLACK = PL_UC8156.BLACK


# DRAWING FUNCTIONS
# =================

# MANDATORY command! 
# Begin communication with the display and initialize it
# may trigger an additional hardware-reset if needed (already done in __init__-sequence)
display.begin(reset = False)

# OPTIONAL but recommended: A "whiteerase" clears the display-content
# and performs a white-black-white update-cycle to reliable
# remove any artifacts from previous images
display.whiteerase()

# OPTIONAL: Fill the whole display with one color
display.fill(color = WHITE)

# OPTIONAL: Switch the color of the displays border-electrode
# (acts as a "picture-frame"). Can only be BLACK or WHITE!
display.set_vborder_color(color = BLACK)

# OPTIONAL: set the rotation of the image
# 0 = 0° rotation (default)
# 1 = 90° rotation clockwise
# 2 = 180° rotation clockwise
# 3 = 270° rotation clockwise
display.setrotation(0)

# NOTE: The used cordinate-system also rotates accordingly,
# with origin at the top-left, X-positive right, Y-positive down

# Drawing strings requires a font-file stored in the root-directory
# of your microcontroller:
display.text(string = 'Hello world!', x = 1, y = 1, color = BLACK, font_name = 'font5x8.bin')

# draw a rectangle:
display.rect(x = 0, y = 10, width = 18, height = 18, color = BLACK)

# fill a rectangle with the passed color:
display.fill_rect(x = 18, y = 10, width = 18, height = 18, color = LGRAY)
display.fill_rect(x = 36, y = 10, width = 18, height = 18, color = DGRAY)
display.fill_rect(x = 54, y = 10, width = 18, height = 18, color = BLACK)

# Draw a line from (x_0, y_0) to (x_1, y_1) in passed color:
display.line(x_0 = 0, y_0 = 40, x_1 = display._width - 1, y_1 = display._height - 1, color = DGRAY)
display.line(x_0 = 0, y_0 = display._height - 1, x_1 = display._width - 1, y_1 = 40, color = LGRAY)

# Draw a circle at the given midpoint location, radius and color:
display.circle(center_x = display._width // 2, center_y = 48, radius = 20, color = BLACK)

# draw a single pixel in the display buffer:
display.pixel(x = display._width // 2, y = 48, color = BLACK)

# Update the display from internal memory
# mode: 0 = full update, 1 = only changed pixels are updated, 2 = monochrome (everything that is not BLACK will turn WHITE)
display.update(mode = 0)