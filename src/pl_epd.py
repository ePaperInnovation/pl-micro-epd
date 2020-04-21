# The MIT License (MIT)
#
# Copyright (c) 2020 Andreas Boenicke for PL Germany GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# 'pl_epd' - ePaper display driver
#===========================================================================
# CircuitPython driver for Plastic Logic ePaper displays
# * Author(s): Andreas Boenicke
#
# based on 'adafruit_epd.epd' by Dean Miller
# License: MIT License (https://opensource.org/licenses/MIT)

import time
from digitalio import Direction
import busio
from micropython import const
import pl_framebuf
import pl_scrambler



class PL_EPD:
    
    # EPD-color-definitions
    BLACK = const(0x00)
    DGRAY = const(0x01)
    LGRAY = const(0x02)
    WHITE = const(0x03)
    
    def __init__(self, spi, cs_pin, rst_pin, busy_pin):
        
        self._framebuf = None
                       
        # Setup of image-rotation
        # 0 = 0° rotation (default)
        # 1 = 90° rotation clockwise
        # 2 = 180° rotation clockwise
        # 3 = 270° rotation clockwise
        self.rotation = 0
        
        # initial value for epd-type, will be auto-updated 
        self.epdsize = 99
                              
        # Setup reset pin, if we have one
        self._rst = rst_pin
        if rst_pin:
            self._rst.direction = Direction.OUTPUT

        # Setup busy pin, if we have one
        self._busy = busy_pin
        if self._busy:
            self._busy.direction = Direction.INPUT
        
        # Setup cs pin (required)
        self._cs = cs_pin
        self._cs.direction = Direction.OUTPUT
        self._cs.value = True

        # SPI interface (required)
        self._spi = spi
        self._spi_baudrate = 4000000
        self._spi_polarity = 1
        self._spi_phase = 1
                     
        print("Init EPD...")
        
    def getrotation(self):
        return self.rotation

    def setrotation(self, x):
        if not x in (0, 1, 2, 3):
            raise RuntimeError("The rotation setting of the display can only be one of (0, 1, 2, 3)!")
        # in case of switching between portrait- and landscape-mode
        if ((self.rotation in (0, 2) and x in (1, 3)) or (self.rotation in (1, 3) and x in (0, 2))): 
            # display-size-parameter-conversion accounting for rotation
            self._width += self._height
            self._height = self._width - self._height
            self._width -= self._height
        # handover of new assigned rotation-modes
        self.rotation = x
        self._framebuf._rotation = x
               
    def getframebuf(self):
        return self._framebuf
        
    def setframebuf(self, x):
        self._framebuf = x
        
    def getbaudrate(self):
        return self._spi_baudrate
        
    def setbaudrate(self, x):
        self._spi_baudrate = x
             
    def busy_wait(self, duration):
        # Wait for display to be done with current task, either by polling the
        # busy pin, or pausing
        if self._busy:
            while not self._busy.value:
                time.sleep(duration)
        else:
            time.sleep(0.5)
                    
    def hardware_reset(self):
        # If we have a reset pin, do a hardware reset by toggling it 
        
        # UC8156c's reset is triggered by a Hi-Lo-Hi sequence of 5ms each
        # followed by an additional 30ms waiting time for the driver-chip's internal power-up-sequence
        if self._rst:
            self._rst.value = True
            time.sleep(0.005)
            self._rst.value = False
            time.sleep(0.005)
            self._rst.value = True
            time.sleep(0.035)
    
    def command(self, cmd, data):
    # Send command byte followed by the instruction byte(s) to display.
        while not self._spi.try_lock():
            pass
        self._spi.configure(baudrate = self._spi_baudrate, phase = self._spi_phase, polarity = self._spi_polarity)
        self._cs.value = False
        self._spi.write(cmd.to_bytes(1, 1))
        self._spi.write(data)
        self._cs.value = True
        self._spi.unlock()
        self.busy_wait(0.001)
        
    def read(self, cmd, amount_bytes):     
    # Send command byte and read register-value.
        while not self._spi.try_lock():
            pass
        self._spi.configure(baudrate = self._spi_baudrate, phase = self._spi_phase, polarity = self._spi_polarity)
        self._cs.value = False
        spi_buffer = bytearray(amount_bytes)
        instruction = (cmd | 0x80).to_bytes(1, 1)
        self._spi.write(instruction)
        self._spi.readinto(spi_buffer)
        self._cs.value = True
        self._spi.unlock()
        return spi_buffer
        self.busy_wait(0.001)
        
    def clear(self):
    # set all pixel-values to "white"
    # does not rely on drawing-functions in "pl_framebuf"-module for debugging-reasons
        for i in range(0, self._buffersize, 1):
            self._buffer[i] = 0xff
            self.busy_wait(0.001)
            
    def bit_not(self, n):
    # 8-bit inverter, for unknown reasons the python-operator only inverted the LSB during tests
        return (0b11111111 - n)
        
    def invert_buffer(self):
    # inverts all pixel-color-values in the buffer
    # does not rely on drawing-functions in "pl_framebuf"-module for speed-reasons
        for i in range(0, self._buffersize, 1):
            self._buffer[i] = self.bit_not(self._buffer[i])
            self.busy_wait(0.001)
            
    def whiteerase(self):
    # Runs an update-cycle white-black-white to reliable remove 
    # faint artifacts from previous images on the display.
    # Does not use drawing-functions of "pl_framebuf" module or scrambling 
    # to allow faster updates
    
        tmp = pl_scrambler.getscramblemode()    # save scramblingmode in temporary variable
        pl_scrambler.setscramblemode(0)         # disable scrambling
        self.clear()
        self.update(2)
        self.invert_buffer()
        self.update(2)
        self.invert_buffer()
        self.update(2)
        pl_scrambler.setscramblemode(tmp)       # restores original scramblingmode
     
    def power_up(self):
        # Power up the display in preparation for writing RAM and updating.
        # must be implemented in subclass
        raise NotImplementedError()

    def power_down(self):
        # Power down the display, must be implemented in subclass
        raise NotImplementedError()

    def update(self, mode):
        # Update the display from internal memory, must be implemented in subclass
        raise NotImplementedError()

    def write_ram(self):
        # Send the one byte command for starting the RAM write process. 
        # must be implemented in subclass
        raise NotImplementedError()
    
    def set_ram_address(self, x, y):
        # Set the RAM address location, must be implemented in subclass
        raise NotImplementedError()
        
    def draw(self, func, args, color):
        drw = getattr(self._framebuf, func)
        drw(*args, color = color)
        
    def pixel(self, x, y, color):
        # draw a single pixel in the display buffer
        self.draw('pixel', (x, y), color)
        
    def fill(self, color):
        # fill the screen with the passed color
        self._framebuf.fill(color)
        
    def rect(self, x, y, width, height, color):     # pylint: disable=too-many-arguments
        # draw a rectangle
        self.draw('rect', (x, y, width, height), color)
        
    def fill_rect(self, x, y, width, height, color):     # pylint: disable=too-many-arguments
        # fill a rectangle with the passed color
        self.draw('fill_rect', (x, y, width, height), color)
        
    def line(self, x_0, y_0, x_1, y_1, color):     # pylint: disable=too-many-arguments
        # Draw a line from (x_0, y_0) to (x_1, y_1) in passed color
        self.draw('line', (x_0, y_0, x_1, y_1), color)
        
    def circle(self, center_x, center_y, radius, color):
        # Draw a circle at the given midpoint location, radius and color.
        # The ```circle``` method draws only a 1 pixel outline.
        self._framebuf.circle(center_x, center_y, radius, color)
        
    def text(self, string, x, y, color, *, font_name):
        # Write text string at location (x, y) in given color, using font file
        self._framebuf.text(string, x, y , color, font_name=font_name)
        
    def hline(self, x, y, width, color):
        # draw a horizontal line
        self.fill_rect(x, y, width, 1, color)
        
    def vline(self, x, y, height, color):
        # draw a vertical line
        self.fill_rect(x, y, 1, height, color)
        
    def image(self, image):
        # Set buffer to value of Python Imaging Library image.  The image should
        # be in RGB mode and a size equal to the display size.
        # 
        #if image.mode != 'RGB':
        #    raise ValueError('Image must be in mode RGB.')
        imwidth, imheight = image.size
        if imwidth != self._width or imheight != self._height:
            raise ValueError('Image must be same dimensions as display ({0}x{1}).' \
                .format(self._width, self._height))
        
        # Grab all the pixels from the image, faster than getpixel.
        pix = image.load()
        # clear out any display buffers
        self.fill(WHITE)

        for y in range(image.size[1]):
            for x in range(image.size[0]):
                pixel = pix[x, y]
                graylevel = (pixel[0] + pixel[1] + pixel[2]) // 3
                if (graylevel < 0x40):
                    # very dark up to black
                    self.pixel(x, y, BLACK)
                elif (graylevel < 0x80):
                    # dark gray
                    self.pixel(x, y, DGRAY)
                elif (graylevel < 0xc0):
                    # light gray
                    self.pixel(y, y, LGRAY)
                else:
                    # very bright up to white
                    self.pixel(x, y, WHITE)


# The following code is taken and/ or derived from
# Adafruit_CircuitPython_EPD/examples/epd_bitmap.py
# Author(s): Dean Miller
# License: MIT License (https://opensource.org/licenses/MIT)
                    
    def read_le(self, s):
    # helper-function (int.from_bytes does not have LittleEndian support)
        result = 0
        shift = 0
        for byte in bytearray(s):
            result += byte << shift
            shift += 8
        return result

                  
                    
    def image_bmp(self, filename):    
    # draws an bitmap-image on the screen (converted to 2-bit grayscale)
    # the image-file must:
    # - be in  24bit(!!!) *.bmp format AND 
    # - fit in size (pixel*pixel) to the display-dimensions (smaller is possible) AND
    # - stored in the root-directory of the microcontroller-board     
        try:
            f = open("/" + filename, "rb")
        except OSError:
            print("Couldn't open file")
            return

        print("File opened")
        try:
            if f.read(2) != b'BM':  # check signature
                raise BMPError("Not BitMap file")

            bmpFileSize = self.read_le(f.read(4))
            f.read(4)  # Read & ignore creator bytes

            bmpImageoffset = self.read_le(f.read(4))  # Start of image data
            headerSize = self.read_le(f.read(4))
            bmpWidth = self.read_le(f.read(4))
            bmpHeight = self.read_le(f.read(4))
            flip = True

            print("Size: %d\nImage offset: %d\nHeader size: %d" % (bmpFileSize, bmpImageoffset, headerSize))
            print("Width: %d\nHeight: %d" % (bmpWidth, bmpHeight))

            if self.read_le(f.read(2)) != 1:
                raise BMPError("Not singleplane")
            bmpDepth = self.read_le(f.read(2))  # bits per pixel
            print("Bit depth: %d" % (bmpDepth))
            if bmpDepth != 24:
                raise BMPError("Not 24-bit")
            if self.read_le(f.read(2)) != 0:
                raise BMPError("Compressed file")

            print("Image OK! Drawing...")

            rowSize = (bmpWidth * 3 + 3) & ~3  # 32-bit line boundary

            for row in range(bmpHeight):  # For each scanline...
                if flip:  # Bitmap is stored bottom-to-top order (normal BMP)
                    pos = bmpImageoffset + (bmpHeight - 1 - row) * rowSize
                else:  # Bitmap is stored top-to-bottom
                    pos = bmpImageoffset + row * rowSize

                # print ("seek to %d" % pos)
                f.seek(pos)
                rowdata = f.read(3*bmpWidth)
                for col in range(bmpWidth):
                    b, g, r = rowdata[3*col:3*col+3]  # BMP files store RGB in BGR
                    graylevel = (b + g + r) // 3    # convert into grayscale-values
                    if (graylevel < 0x40):      # very dark up to black
                        self.pixel(col, row, BLACK)
                    elif (graylevel < 0x80):    # dark gray
                        self.pixel(col, row, DGRAY)
                    elif (graylevel < 0xc0):    # light gray
                        self.pixel(col, row, LGRAY)
                    else:                       # very bright up to white  
                        self.pixel(col, row, WHITE)
        except OSError:
            print("Couldn't read file")
        except BMPError as e:
            print("Failed to parse BMP: " + e.args[0])
        finally:
            f.close()
        print("Finished drawing")    

class BMPError(Exception):
        pass          
        