#! /usr/bin/env python
"""\
Scan for serial ports.

Part of pySerial (http://pyserial.sf.net)
(C) 2002-2003 <cliechti@gmx.net>

The scan function of this module tries to open each port number
from 0 to 255 and it builds a list of those ports where this was
successful.
"""

import serial

def scan():
    """Scan for available ports. return a list of tuples (num, name)
    """
    for i in range(256):
        try:
            s = serial.Serial(i)
            yield i, s.portstr
            s.close()
        except serial.SerialException:
            pass

if __name__=='__main__':
    print("Found ports:")
    for n, s in scan():
        print("{} {}".format(n, s))
