# -*- coding: utf-8 -*-
"""
    lantz.drivers.rigol.ds1052e
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Implements the drivers to control an oscilloscope.

    :copyright: 2015 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
    
    Source: DS1052e manual
"""


from lantz.messagebased import MessageBasedDriver


class DS1052e(MessageBasedDriver):
    pass



if __name__ == '__main__':
    with DS1052e('USB0::0x1AB1::0x0588::DS1K00005888::INSTR') as inst:
        print(inst.query('*IDN?'))
