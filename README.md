# pl-micro-epd
Library and tools written in CircuitPython to control flexible organic displays from PlasticLogic. Welcome to the  docs!

![Feather Wing with 2.1" E Ink](https://user-images.githubusercontent.com/21104467/80134899-b61efd80-859f-11ea-9539-a8c45b5f9cbc.JPG) 
[*Feather Wing with 1.4" E Ink*](https://www.plasticlogic.com)


![Feather Wing with 1.38" E Ink](https://user-images.githubusercontent.com/21104467/80135014-e1a1e800-859f-11ea-9418-de34d0307a01.JPG)
[*Feather Wing with 1.4" E Ink*](https://www.plasticlogic.com)


How To Use
-------------------

### Installation


### Hardware hookup


### Example: Hello World!

This is the [first](https://robpo.github.io/Paperino/exampleHelloWorld/), and shortest possible demo and shows how to address the ePaper: 

```cpp
#import digitalio
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

# The displays support up to 4 grayscale-colors:
WHITE = PL_UC8156.WHITE
LGRAY = PL_UC8156.LGRAY     # light gray
DGRAY = PL_UC8156.DGRAY     # dark gray
BLACK = PL_UC8156.BLACK

display.begin(reset = False)
display.text(string = 'Hello world!', x = 1, y = 1, color = BLACK, font_name = 'font5x8.bin')
```

You should now be able to see the ePaper screen updating. Congratulation! If you feel more like a pro’ this is now the time for the next examples.


License Information
-------------------

This library is _**open source**_!

CircuitPython driver for Plastic Logic ePaper displays
* Author(s): Andreas Boenicke
  based on 'adafruit_epd.epd' by Dean Miller
  License: MIT License (https://opensource.org/licenses/MIT)

We invested time and resources providing this open source code, please support open source hardware by purchasing this product @Adafruit and @Plasticlogic.
