# Example-code for using the BLE Connect UART as a kind of REPL 
# to transmit commands to the display.
# To use, start this program, and start the Adafruit Bluefruit LE Connect app.
# Connect, and then select UART

from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService
import digitalio
import busio
import board
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
display.setrotation(0)

# define fontfile used for displaying text
FONTFILE = 'font5x8.bin'


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
            # raw_bytes = uart_server.read(uart_server.in_waiting)
            raw_bytes = uart_server.readline()
            text = raw_bytes.decode().strip()
            
            if (text.find("(") == -1):
                print("No command called")
            else:
                command = text[0:text.find("(")]
                parameter = text[(text.find("(") + 1):text.find(")")]
                argument = list()
                arg_start = parameter.find("(") + 1
                
                # Extracting the function-arguments from the transmitted command-string.
                # Arguments are to be comma-separated!
                for i in range(0, parameter.count(","), 1):
                    
                    if (parameter[arg_start] == '"'):
                        arg_end = parameter.find('"', (arg_start + 1)) + 1
                        argument.append(parameter[(arg_start + 1):(arg_end - 1)])
                    else:
                        arg_end = parameter.find(",", arg_start)
                        argument.append(parameter[arg_start:arg_end])
                    arg_start = arg_end + 1
                    print(type(argument[i]))
                argument.append(parameter[arg_start:])
                
                if (command == 'hardware_reset'):
                    # Triggers a hardware reset
                    # Arguments: none
                    display.hardware_reset()
                    
                elif (command == 'begin'):
                    # Begin communication with the display and initialize it
                    # Arguments: reset (0 or 1) 
                    display.begin(reset = int(argument[0]))
                    
                elif (command == 'deep_sleep'):
                    # Putting the UC8156 in deep sleep mode with less than 1µA current @3.3V.
                    # Reset pin toggling needed to wakeup the driver IC again.
                    # Arguments: none
                    display.deep_sleep()
                    
                elif (command == 'setrotation'):
                    # Set the rotation of the image
                    # Arguments: rotation (0 = 0°, 1 = 90°, 2 = 180°, 3 = 270° rotation clockwise)
                    display.setrotation(rotation = int(argument[0]))
                    
                elif (command == 'set_vborder_color'):
                    # border-electrode (= "frame" around the display) can be driven independendly 
                    # Arguments: color (0 = black or 3 = white)
                    display.set_vborder_color(color = int(argument[0]))
                    
                elif (command == 'update'):
                    # Update the display from internal memory
                    # Arguments: mode (0 = full update, 1 = only changed pixels are updated, 2 = monochrome)
                    display.update(mode = int(argument[0]))
                    
                elif (command == 'whiteerase'):
                    # clears the display-content and performs a white-black-white update-cycle 
                    # to reliable remove any artifacts from previous images
                    # Arguments: none
                    display.whiteerase()
                    
                elif (command == 'fill'):
                    # fill the screen with the passed color 
                    # Arguments: color (0 = black, 1 = dark gray, 2 = light gray. 3 = white)
                    display.fill(color = int(argument[0]))
                    display.update(0)
                    
                elif (command == 'pixel'):
                    # draw a single pixel at position x, y in the display buffer
                    # Arguments: x, y, color (0 = black, 1 = dark gray, 2 = light gray. 3 = white)
                    display.pixel(x = int(argument[0]), y = int(argument[1]), color = int(argument[2]))
                    display.update(1)
                    
                elif (command == 'fill_rect'):
                    # fill a rectangle with the passed color
                    # Arguments: x, y, width, height, color (0 = black, 1 = dark gray, 2 = light gray. 3 = white)
                    display.fill_rect(x = int(argument[0]), y = int(argument[1]), width = int(argument[2]), height = int(argument[3]), color = int(argument[4]))
                    display.update(0)
                    
                elif (command == 'rect'):
                    # draw a rectangle (outline)
                    # Arguments: x, y, width, height, color (0 = black, 1 = dark gray, 2 = light gray. 3 = white)
                    display.rect(x = int(argument[0]), y = int(argument[1]), width = int(argument[2]), height = int(argument[3]), color = int(argument[4]))
                    display.update(1)
                    
                elif (command == 'line'):
                    # draw a line from coordinate x_0, y_0 to coordinate x_1, y_1
                    # Arguments: x_0, y_0, x_1, y_1, color (0 = black, 1 = dark gray, 2 = light gray. 3 = white)
                    display.line(x_0 = int(argument[0]), y_0 = int(argument[1]), x_1 = int(argument[2]), y_1 = int(argument[3]), color = int(argument[4]))
                    display.update(1)
                    
                elif (command == 'circle'):
                    # Draw a circle (outline) at the given midpoint location, radius and color.
                    # Arguments: center_x, center_y, radius, color (0 = black, 1 = dark gray, 2 = light gray. 3 = white)
                    display.circle(center_x = int(argument[0]), center_y = int(argument[1]), radius = int(argument[2]), color = int(argument[3]))
                    display.update(1)
                    
                elif (command == 'text'):
                    # Write text string at location (x, y) in given color, using above specified font file
                    # NOTE: Comma is a forbidden character for the text string since already used as argument-separator!
                    # Arguments: string, x, y, color (0 = black, 1 = dark gray, 2 = light gray. 3 = white)
                    display.text(string = argument[0], x = int(argument[1]), y = int(argument[2]), color = int(argument[3]), font_name = FONTFILE)
                    display.update(0)
                    
                elif (command == 'image_bmp'):
                    # draws an bitmap-image on the screen (converted to 2-bit grayscale)
                    # the image-file must:
                    # - be in  24bit(!!!) *.bmp format AND 
                    # - fit in size (pixel*pixel) to the display-dimensions (smaller is possible) AND
                    # - stored in the root-directory of the microcontroller-board
                    # Arguments: filename
                    display.whiteerase()
                    display.image_bmp(filename = str(argument[0]))
                    display.update(0)
                    
                else:
                    print("Unknown command")
   
    # Disconnected