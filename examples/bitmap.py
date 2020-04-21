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


# DRAWING A BITMAP-IMAGE
# ======================

# MANDATORY command! 
# Begin communication with the display and initialize it
# may trigger an additional hardware-reset if needed (already done in __init__-sequence)
display.begin(reset = False)

# OPTIONAL but recommended: A "whiteerase" clears the display-content
# and performs a white-black-white update-cycle to reliable
# remove any artifacts from previous images
display.whiteerase()


# OPTIONAL: set the rotation of the image
# 0 = 0° rotation (default)
# 1 = 90° rotation clockwise
# 2 = 180° rotation clockwise
# 3 = 270° rotation clockwise
display.setrotation(0)

# Specify the image-filename to display on the screen.
# The image-file must:
# - be in  24bit(!!!) *.bmp format AND 
# - fit in size (pixel*pixel) to the display-dimensions (smaller is possible) AND
# - stored in the root-directory of the microcontroller-board 

if (display.epdsize == 11):     # 72x148 pixel / 1.1 inch display
    FILENAME = "TestPic_11in.bmp"
elif (display.epdsize == 14):   # 180x100 pixel / 1.4 inch display
    FILENAME = "TestPic_14in.bmp"
elif (display.epdsize == 21):   # 240x146 pixel / 2.1 inch display
    FILENAME = "TestPic_21in.bmp"
elif (display.epdsize == 31):   # 74x312 pixel / 3.1 inch display
    FILENAME = "TestPic_31in.bmp"
else:
    raise RuntimeError("Unimplemented display-type!")

# Draws the bitmap-image to the internal memory (converted to 2-bit grayscale)    
display.image_bmp(FILENAME)
    
# Update the display from internal memory
# mode: 0 = full update, 1 = only changed pixels are updated, 2 = monochrome (everything that is not BLACK will turn WHITE)
display.update(mode = 0)