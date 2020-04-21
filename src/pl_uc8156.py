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
# 'pl_uc8156' - ePaper display driver
# ====================================================================================
# CircuitPhyton driver Plastic Logic ePaper display driver using the UltraChip UC8156c
# * Author(s): Andreas Boenicke
#
# based on 'adafruit_epd.ssd1608' by Dean Miller and Ladyada
# License: MIT License (https://opensource.org/licenses/MIT)


import time
import pl_framebuf
import pl_scrambler
from micropython import const
from pl_epd import PL_EPD

# Register-adress
_UC8156c_REVISION = const(0x00)   # Revision, read only
_UC8156c_PANELSETTING = const(0x01)
_UC8156c_DRIVERVOLTAGE = const(0x02)
_UC8156c_POWERCONTROL = const(0x03)
_UC8156c_BOOSTSETTING = const(0x04)
_UC8156c_TCOMTIMING = const(0x06)
_UC8156c_INITTEMPERATURE = const(0x07)
_UC8156c_SETRESOLUTION = const(0x0c)
_UC8156c_WRITEPXRECTSET = const(0x0d)
_UC8156c_PIXELACESSPOS = const(0x0e)
_UC8156c_DATENTRYMODE = const(0x0f)
_UC8156c_WRITERAM = const(0x10)
_UC8156c_DISPLAYENGINE = const(0x14)
_UC8156c_STATUS = const(0x15)  # Statusregister, read only
_UC8156c_VCOMCONFIG = const(0x18)
_UC8156c_BORDERSETTING = const(0x1d)
_UC8156c_POWERSEQUENCE = const(0x1f)
_UC8156c_SOFTWARERESET = const(0x20)   # write only
_UC8156c_SLEEPMODE = const(0x21)
_UC8156c_PROGRAMMTP = const(0x40)
_UC8156c_MTPADDRESSSETTING = const(0x41)
_UC8156c_MTPREAD = const(0x043)
_UC8156c_LOADMONOWF = const(0x44)


class PL_UC8156(PL_EPD):
    # driver class for Plastic Logic ePaper display with UltraChip 8156c driver-chip
    
    
    # pylint: disable=too-many-arguments
    def __init__(self, spi, *, cs_pin, rst_pin, busy_pin):
        super(PL_UC8156, self).__init__(spi, cs_pin, rst_pin, busy_pin)        
        
        # hardware reset & communication-check
        self.hardware_reset()
        self.comm_check()
        
        # retrieves display-parameters stored on the driver-chip
        self.getepdsize()   
        
        # Framebuffer-Setup with just retrieved display-geometry-data
        self._buffersize = self._width * self._height // 4
        self._buffer = bytearray(self._buffersize)
        self._framebuf = pl_framebuf.FrameBuffer(self._buffer, self._width, self._height, buf_format=pl_framebuf.GS4_HMSB)
    
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
            self.busy_wait(0.001)
            print("Reset driver-chip")
            
    def comm_check(self): 
    # checks connection to the display by reading the revision-register
    # to avoid confusing error-messages by consequential errors
        if (self.read(_UC8156c_REVISION, 1) == b'\x00'):
            raise RuntimeError("Display not responding. Please check wiring/ power-supply!")
        else:
            print("Connected to display")
           
    def begin(self, reset=False):
        # Begin communication with the display and set basic settings
        if reset:
            self.hardware_reset()
        
        # Driver-chip configuration
        if (self.epdsize == 11):
            self.command(_UC8156c_PANELSETTING, bytearray([0x12]))
            self.command(_UC8156c_WRITEPXRECTSET, bytearray([0x00, 0x47, 0x00, 0x93]))
            self.command(_UC8156c_VCOMCONFIG, bytearray([0x00, 0x00, 0x24, 0x07]))
            self.command(_UC8156c_DATENTRYMODE, bytearray([0x02]))
        elif (self.epdsize == 14):
            self.command(_UC8156c_PANELSETTING, bytearray([0x12]))
            self.command(_UC8156c_WRITEPXRECTSET, bytearray([0x00, 0xb3, 0x3c, 0x9f]))
            self.command(_UC8156c_VCOMCONFIG, bytearray([0x00, 0x00, 0x24, 0x07]))
            self.command(_UC8156c_DATENTRYMODE, bytearray([0x02]))
        elif (self.epdsize == 21):
            self.command(_UC8156c_PANELSETTING, bytearray([0x11]))
            self.command(_UC8156c_WRITEPXRECTSET, bytearray([0x00, 0xef, 0x00, 0x91]))
            self.command(_UC8156c_VCOMCONFIG, bytearray([0x00, 0x00, 0x24, 0x07]))
            self.command(_UC8156c_DATENTRYMODE, bytearray([0x00]))
        elif (self.epdsize == 31):
            self.command(_UC8156c_PANELSETTING, bytearray([0x12]))
            self.command(_UC8156c_WRITEPXRECTSET, bytearray([0x00, 0x93, 0x00, 0x9b]))
            self.command(_UC8156c_VCOMCONFIG, bytearray([0x50, 0x01, 0x24, 0x07]))
            self.command(_UC8156c_DATENTRYMODE, bytearray([0x02]))
        else:
            raise RuntimeError("Unimplemented display-type!")
        
        self.command(_UC8156c_DRIVERVOLTAGE, bytearray([0x25, 0xff]))
        self.command(_UC8156c_BORDERSETTING, bytearray([0x04]))
        self.command(_UC8156c_LOADMONOWF, bytearray([0x60]))
        self.command(_UC8156c_INITTEMPERATURE, bytearray([0x0a]))
        self.command(_UC8156c_BOOSTSETTING, bytearray([0x22, 0x17]))
        
        print("Init complete!")
   
    def busy_wait(self, duration):
        # Wait for display to be done with current task, either by polling the
        # busy pin, or pausing
        if self._busy:
            while not self._busy.value:
                time.sleep(duration)
        else:
            time.sleep(0.005)

    def power_up(self):
        # Power up the display in preparation for writing RAM and updating
        self.busy_wait(duration = 0.001)
        if (self.epdsize == 11):
            self.command(_UC8156c_SETRESOLUTION, bytearray([0x00, 0xef, 0x00, 0x93]))
        elif (self.epdsize == 14):
            self.command(_UC8156c_SETRESOLUTION, bytearray([0x00, 0xef, 0x00, 0x9f]))
        elif (self.epdsize == 21):
            self.command(_UC8156c_SETRESOLUTION, bytearray([0x00, 0xef, 0x00, 0x9f]))
        elif (self.epdsize == 31):
            self.command(_UC8156c_SETRESOLUTION, bytearray([0x00, 0xef, 0x00, 0x9f]))
        self.command(_UC8156c_TCOMTIMING, bytearray([0x67, 0x55]))
        self.command(_UC8156c_POWERSEQUENCE, bytearray([0x00, 0x00, 0x00]))
        self.command(_UC8156c_POWERCONTROL, bytearray([0xd1]))
        
        while(self.read(_UC8156c_STATUS, 1) == b'\x00'):   # wait until internal voltage-pump is ready
            pass
        self.busy_wait(duration = 0.001)   
        
        
    def power_down(self):
        # Power down the display - required when not actively displaying!
        self.command(_UC8156c_POWERCONTROL, bytearray([0xd0]))
        self.busy_wait(duration = 0.07)
        self.command(_UC8156c_POWERCONTROL, bytearray([0xc0]))
        self.busy_wait(duration = 0.001)
        

    def deep_sleep(self):
    # Putting the UC8156 in deep sleep mode with less than 1µA current @3.3V.
    # Reset pin toggling needed to wakeup the driver IC again.
        self.command(_UC8156c_SLEEPMODE, bytearray([0xff, 0xff, 0xff, 0xff]))
        print("Sleepmode activated. Reset required before further display-updates are possible again!")
    
    
# UPDATE
# Triggers an image update based on the content written in the image buffer.
# There are three different updateModes supported: Mode = 0 (full update) is set by default,
# achieves four greyelevels, takes about 800ms and refreshes all pixels.
# This is the update mode having the best image quality.
# Mode = 1 (partial update) is a variant of the previous one but only changing pixels are refreshed.
# This results in less flickering for the price of a slightly higher pixel-pixel crosstalk.
# Mode = 2 (monochrome) is again a variant of the previous update mode but only ~250ms long.
# This allows slightly faster and more responsive updates for the price of
# only two greylevels being supported (BLACK and WHITE).
# Depending on your application it is recommended to insert a full update
# (Mode = 0) after a couple of mono updates (Mode = 2) to increase the image quality.
# THIS KIND OF DISPLAY IS NOT SUITED FOR LONG RUNNING ANIMATIONS OR APPLICATIONS
# WITH CONTINUOUSLY HIGH UPDATE RATES. AS A RULE OF THUMB PLEASE TRIGGER UPDATES
# IN AVERAGE NOT FASTER THAN MINUTELY
# (OR RUN BACK2BACK UPDATES NOT LONGER AS ONE HOUR PER DAY.)
    
    def update(self, mode):    # mode: 0 = full update, 1 = only changed pixels are updated, 2 = monochrome
        # Update the display from internal memory
        self.write_ram()
        self.power_up()
        if (mode == 0):
            self.command(_UC8156c_PROGRAMMTP, bytearray([0x00]))
            self.command(_UC8156c_DISPLAYENGINE, bytearray([0x03]))
            self.busy_wait(duration = 0.88)
        elif (mode == 1):
            self.command(_UC8156c_PROGRAMMTP, bytearray([0x00]))
            self.command(_UC8156c_DISPLAYENGINE, bytearray([0x07]))
            self.busy_wait(duration = 0.88)
        elif (mode == 2):
            self.command(_UC8156c_PROGRAMMTP, bytearray([0x02]))
            self.command(_UC8156c_DISPLAYENGINE, bytearray([0x07]))
            self.busy_wait(duration = 0.34)
        else:
            print('Error while configuring update-mode!')
        self.power_down()
        print("Update complete!")
        
    def write_ram(self):
        if (self.epdsize == 11):
            self.command(_UC8156c_PIXELACESSPOS, bytearray([0x00, 0x93]))
        elif (self.epdsize == 14):
            self.command(_UC8156c_PIXELACESSPOS, bytearray([0x00, 0x9f]))
        elif (self.epdsize == 21):
            self.command(_UC8156c_PIXELACESSPOS, bytearray([0x00, 0x00]))
        elif (self.epdsize == 31):
            self.command(_UC8156c_PIXELACESSPOS, bytearray([0x00, 0x9b]))
        else:
            raise RuntimeError("Unimplemented display-type!")
            
        self._buffer = self._framebuf.buf
        # scrambles the buffer        
        self._buffer = pl_scrambler.scramble_array(self._buffer)   # comment this line if you don't need to scramble at all
        # writes the buffer byte-wise to the RAM
        while not self._spi.try_lock():
            pass
        self._spi.configure(baudrate = self._spi_baudrate, phase = self._spi_phase, polarity = self._spi_polarity)
        self._cs.value = False
        self._spi.write(_UC8156c_WRITERAM.to_bytes(1, 1))
        for i in range(0, self._buffersize, 1):
            self._spi.write(self._buffer[i].to_bytes(1, 1)) 
        self._cs.value = True
        self._spi.unlock()
        self.busy_wait(0.001)

    def set_ram_address(self, x, y): # pylint: disable=unused-argument, no-self-use
        # Set the RAM address location, not used on this chipset but required by
        # the superclass
        # Set RAM address counter
        self.command(_UC8156c_PIXELACESSPOS, bytearray([x, y]))
        
    def getepdsize(self):
    # retrieves display-parameters stored on the driver-chip
        self.command(_UC8156c_PROGRAMMTP, bytearray([0x02]))
        self.command(_UC8156c_MTPADDRESSSETTING, bytearray([0xf2, 0x04]))
        data = self.read(_UC8156c_MTPREAD, 1)   # first byte read is a dummy byte
        data = self.read(_UC8156c_MTPREAD, 1)
        if (data == b'\x31'):
            data = self.read(_UC8156c_MTPREAD, 1)
            if (data == b'\x31'):
                self.epdsize = 11
                self._width = 72
                self._height = 148
                pl_scrambler.setglcount(148)
                pl_scrambler.setslcount(72)
                pl_scrambler.setscramblemode(0x00)
                print("72x148 pixel / 1.1 inch display detected")
            else: 
                self.epdsize = 14
                self._width = 180
                self._height = 100
                pl_scrambler.setglcount(100)
                pl_scrambler.setslcount(180)
                pl_scrambler.setscramblemode(0x00)
                print("180x100 pixel / 1.4 inch display detected")
        elif (data == b'\x30'):     # very old 1.4"-displays encoded with 0x30
            self.epdsize = 14
            self._width = 180
            self._height = 100
            pl_scrambler.setglcount(100)
            pl_scrambler.setslcount(180)
            pl_scrambler.setscramblemode(0x00)
            print("180x100 pixel / 1.4 inch display detected")     
        elif (data == b'\x32'):
            self.epdsize = 21
            self._width = 240
            self._height = 146
            pl_scrambler.setglcount(146)
            pl_scrambler.setslcount(240)
            pl_scrambler.setscramblemode(0x200)
            print("240x146 pixel / 2.1 inch display detected")
        elif (data == b'\x33'):
            self.epdsize = 31
            self._width = 74
            self._height = 312
            pl_scrambler.setglcount(312)  # 312 gatelines shorted in pairs to serve 2 sourcelines, physically just 156 gatelines
            pl_scrambler.setslcount(74)
            pl_scrambler.setscramblemode(0x50)
            print("74x312 pixel / 3.1 inch display detected")
        else:
            self.epdsize = 99   # unknown display
            pl_scrambler.setglcount(148)  # parameters taken from smallest available display (as of this writing 1.1")
            pl_scrambler.setslcount(72)   
            pl_scrambler.setscramblemode(0x00)
            print("Unknown display detected!", data)
            
    def set_vborder_color(self, color):
    # border-electrode (= "frame" around the display) can be driven independendly to either black or white 
        if (color == 0x00):     # black border
            self.command(_UC8156c_BORDERSETTING, bytearray([0x07]))
        elif (color == 0x03):   # white border
            self.command(_UC8156c_BORDERSETTING, bytearray([0xf7]))
        else:        
            raise RuntimeError("Border-color can only be BLACK or WHITE")
        
        # partial update so only the border-color will change
        self.update(mode=1)
        
        # restore original register-value to keep border-color locked during further updates
        self.command(_UC8156c_BORDERSETTING, bytearray([0x04]))
        print("Border-update complete!")
        
        
        
        