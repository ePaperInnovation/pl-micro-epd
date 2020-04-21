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
# 'pl_scrambler'
# ====================================================
# CircuitPython scrambling module
# * Author(s): Andreas Boenicke

from micropython import const


# defines a structure representing a array scrambling configuration

# source_interlaced: defines whether the data will be interlaced or not
#                    0 -> no interlacing:  S0, S1, S2, S3, S4, ...
#                    1 -> interlacing:     S0, Sn, S1, Sn+1, S2, Sn+2, ...  (with n = slCount/2)

# source_direction: direction of source data
# 					  0 -> upwards: 		S0, S1, S2, S3, ...
# 					  1 -> downwards: 		Sn, Sn-1, Sn-2, Sn-3, ...        (with n = slCount)

# source_start: starting position for source outputs, either left (default) or right
# 					  0 -> left:			S0 is output first
# 					  1 -> right:			Sn is output first 				 (with n = slCount/2)

# gate_direction: direction of gate data
# 					  0 -> upwards: 		G0, G1, G2, G3, ...
# 					  1 -> downwards: 		Gn, Gn-1, Gn-2, Gn-3, ...		 (with n = glCount)



SCRAMBLING_SOURCE_START_BIT = const(0)              
SCRAMBLING_SOURCE_INTERLACED_BIT = const(1)
SCRAMBLING_SOURCE_DIRECTION_BIT	= const(2)
SCRAMBLING_GATE_DIRECTION_BIT = const(3)
SCRAMBLING_SOURCE_SCRAMBLE_BIT = const(4)	        # source line is connected to every 2nd pixel
SCRAMBLING_GATE_SCRAMBLE_BIT = const(5)             # gate line is connected to every 2nd pixel
SCRAMBLING_SCRAMBLE_FIRST_ODD_LINE_BIT = const(6)	# if is set the odd lines will be first
SCRAMBLING_SOURCE_MIRROR_RH_BIT = const(7)	        # mirrors the second half image
SCRAMBLING_SOURCE_INTERLACED_FIRST_ODD_LINE_BIT = const(8)
SCRAMBLING_SOURCE_MIRROR_LH_BIT = const(9)	        # mirrors the first half image

# creates a 10bit-mask depending on scrambling-modes in use
SCRAMBLING_SOURCE_START_MASK = const(1 << SCRAMBLING_SOURCE_START_BIT)
SCRAMBLING_SOURCE_INTERLACED_MASK =	const(1 << SCRAMBLING_SOURCE_INTERLACED_BIT)
SCRAMBLING_SOURCE_DIRECTION_MASK = const(1 << SCRAMBLING_SOURCE_DIRECTION_BIT)
SCRAMBLING_GATE_DIRECTION_MASK = const(1 << SCRAMBLING_GATE_DIRECTION_BIT)
SCRAMBLING_SOURCE_SCRAMBLE_MASK	= const(1 << SCRAMBLING_SOURCE_SCRAMBLE_BIT)
SCRAMBLING_GATE_SCRAMBLE_MASK =	const(1 << SCRAMBLING_GATE_SCRAMBLE_BIT)
SCRAMBLING_SCRAMBLE_FIRST_ODD_LINE_MASK	= const(1 << SCRAMBLING_SCRAMBLE_FIRST_ODD_LINE_BIT)
SCRAMBLING_SOURCE_MIRROR_RH_MASK = const(1 << SCRAMBLING_SOURCE_MIRROR_RH_BIT)
SCRAMBLING_SOURCE_INTERLACED_FIRST_ODD_LINE_MASK = const(1 << SCRAMBLING_SOURCE_INTERLACED_FIRST_ODD_LINE_BIT)
SCRAMBLING_SOURCE_MIRROR_LH_MASK = const(1 << SCRAMBLING_SOURCE_MIRROR_LH_BIT)
    
# initial values if not otherwise defined
# parameters taken from smallest available display (as of this writing 1.1")
scramblingmode = 0x00
slcount = 72
glcount = 148

  
def getscramblemode():
    global scramblingmode
    return scramblingmode
         
def setscramblemode(x):
    global scramblingmode
    scramblingmode = x
       
def getglcount():
    global glcount
    return glcount
                
def setglcount(x):
    global glcount
    glcount = x
            
def getslcount():
    global slcount
    return slcount
            
def setslcount(x):
    global slcount
    slcount = x
    
def scramble_array(sourcebuffer):
# copies data from source to target array while applying a scrambling algorithm
# Expects data in source array as sourceline fast addressed and starting with gate=0 and source=0
    global scramblingmode
    global slcount
    global glcount
    _sourcebuffer = sourcebuffer
    _slcount = slcount
    _glcount = glcount
    if (scramblingmode == 0):
        # no need to scramble image data, just return the source-buffer
        return _sourcebuffer
    else:
        # need to scramble image data based on scrambling mode
        targetbuffer = bytearray(len(_sourcebuffer))
        for gl in range(0, _glcount, 1):
            for sl in range(0, _slcount, 1):
            
                          
                # calculates the consecutive pixel-position in source- and target-framebuffer
                target_pix = calc_scrambled_index(gl, sl, _glcount, _slcount)
                source_pix = calc_pixel_index(gl, sl, slcount) 
            
                # buffer-index assuming 4 pixel per byte
                source_idx = (source_pix // 4)
                target_idx = (target_pix // 4)
            
                # get pixel-color information from source-framebuffer
                source_offset = 3 - (source_pix & 0x03)
                pixel = (_sourcebuffer[source_idx] >> (source_offset * 2)) & 0x03
            
                # write the just gained pixel-color information in the right position in the target-framebuffer
                if ((target_pix % 4) == 0):
                    targetbuffer[target_idx] = ((targetbuffer[target_idx] & 0x3f) | (pixel << 6))
                elif ((target_pix % 4) == 1):
                    targetbuffer[target_idx] = ((targetbuffer[target_idx] & 0xcf) | (pixel << 4))
                elif ((target_pix % 4) == 2):
                    targetbuffer[target_idx] = ((targetbuffer[target_idx] & 0xf3) | (pixel << 2))
                elif ((target_pix % 4) == 3):
                    targetbuffer[target_idx] = ((targetbuffer[target_idx] & 0xfc) | pixel)
                          
        return targetbuffer


def calc_pixel_index(gl, sl, slcount):
# returns the consecutive number of the pixel-position in the source-framebuffer
    return (gl * slcount + sl)


def calc_scrambled_index(gl, sl, _glcount, _slcount):
# returns the scrambled but still consecutive number of the pixel-position in the target-framebuffer
    
    # set starting values
    global scramblingmode
    global glcount
    global slcount
    new_gl_idx = gl
    new_sl_idx = sl
        
    # source line scrambling for half nbr of gate lines and double nbr of source lines
    # scrambling between the scrambling resolution
    if (scramblingmode & SCRAMBLING_SOURCE_SCRAMBLE_MASK):
        _glcount = _glcount // 2
        _slcount = _slcount * 2
        if (scramblingmode & SCRAMBLING_SCRAMBLE_FIRST_ODD_LINE_MASK):
                        
            if ((new_gl_idx % 2) == 1):
                new_sl_idx = new_sl_idx * 2
                new_gl_idx = new_gl_idx // 2
            else:
                new_sl_idx = ((new_sl_idx * 2) + 1)
                new_gl_idx = new_gl_idx // 2
                
        else:
                        
            if  ((new_gl_idx % 2) == 1):
                new_sl_idx = ((new_sl_idx * 2) + 1)
                new_gl_idx = new_gl_idx // 2
            else:
                new_sl_idx = new_sl_idx * 2
                new_gl_idx = new_gl_idx // 2
                
    # gate line scrambling for half nbr of source lines and double nbr of gate lines            
    elif (scramblingmode & SCRAMBLING_GATE_SCRAMBLE_MASK):
        _glcount = _glcount * 2
        _slcount = _slcount // 2
        
        if (scramblingmode & SCRAMBLING_SCRAMBLE_FIRST_ODD_LINE_MASK):
        # scrambling between image resolution and scrambling resolution
        # move every even source line to the next gate line
        # by bisect the source line index
            new_gl_idx = (new_gl_idx * 2) + ((new_sl_idx + 1) % 2)
            new_sl_idx = (new_sl_idx // 2)
        else:
        # scrambling between image resolution and scrambling resolution
        # move every odd source line to the next gate line
        # by bisect the source line index
            new_gl_idx = (new_gl_idx * 2) + (new_sl_idx % 2)
            new_sl_idx = (new_sl_idx // 2)
                    
    # check for difference in source interlaced setting
    if (scramblingmode & SCRAMBLING_SOURCE_INTERLACED_MASK):
        if (scramblingmode & SCRAMBLING_SOURCE_INTERLACED_FIRST_ODD_LINE_MASK):
            if (((new_sl_idx + 1) % 2) == 1):
                new_sl_idx = (new_sl_idx // 2) + (_slcount // 2)
            else:
                new_sl_idx = (new_sl_idx // 2)
                
        else:
            if ((new_sl_idx % 2) == 1):
                new_sl_idx = ((new_sl_idx // 2) + (_slcount // 2))
            else:
                new_sl_idx = (new_sl_idx // 2)
                
    # mirrors the first half image
    if (scramblingmode & SCRAMBLING_SOURCE_MIRROR_LH_MASK):
        if (new_sl_idx < (_slcount // 2)):
            new_sl_idx = (((_slcount // 2) - 1) - new_sl_idx)
            
    # mirrors the second half image
    if (scramblingmode & SCRAMBLING_SOURCE_MIRROR_RH_MASK):
        if (new_sl_idx >= (_slcount // 2)):
            new_sl_idx = (_slcount - 1) - (new_sl_idx - (_slcount // 2))
            
    # check for difference in source direction setting
    if (scramblingmode & SCRAMBLING_SOURCE_DIRECTION_MASK):
        new_sl_idx = (_slcount - new_sl_idx - 1)
        
    # check for difference in source output position setting
    if (scramblingmode & SCRAMBLING_SOURCE_START_MASK):
        new_sl_idx = ((new_sl_idx + (_slcount // 2)) % _slcount)
        
    # check for difference in gate direction setting
    if (scramblingmode & SCRAMBLING_GATE_DIRECTION_MASK):
        new_gl_idx = (_glcount - new_gl_idx - 1)
    
  
    return calc_pixel_index(new_gl_idx, new_sl_idx, _slcount)
            
    