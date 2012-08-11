# -*- coding: utf-8 -*-
"""
    lantz.drivers.pco.sensicam
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Implements Sensicam driver


    Implementation Notes
    --------------------

    The Sensicam operates using a COC = Command Operation Code

    ---

    :copyright: 2012 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from time import sleep
from collections import namedtuple

import ctypes as ct
import numpy as np

from lantz import Action, Feat
from lantz.errors import InstrumentError
from lantz.foreign import LibraryDriver, RetTuple

class Status(object):
    READ_BUSY = 1
    BUFFER_EMPTY = 2
    COC_RUNNING = 4
    BUFFERS_FULL = 8

_ERRORS = {
        0: "Success",
        -1: "No camera connected",
        -2: "Timeout",
        -3: "Wrong parameter",
        -4: "cannot locate card",
        -5: "cannot allocate DMA buffer",
        -7: "DMA timeout",
        -8: "Invalid camera mode",
        -9: "No driver installed",
        -10: "No PCI bios found",
        -11: "Device is hold by another process",
        -12: "Error in reading or writing data to board",
        -13: "Wrong driver function",
        -20: "Load COC error",
        -21: "Too many values in COC",
        -22: "Temperatur out of range",
        -23: "Buffer allocate error",
        -24: "Read image error",
        -25: "Set/reset buffer flags is failed",
        -26: "Buffer is used",
        -27: "Call to a windows function is failed",
        -28: "DMA error",
        -29: "Cannot open file",
        -30: "Registry error",
        -31: "Open dialog error",
        -32: "Needs newer called vxd or dll",
        100: 'no image in PCI buffer',
        101: 'picture too dark',
        102: 'picture too bright',
        103: 'one or more values changed',
        104: 'buffer for builded string too short'}

#: Command Operation Code tuple
COC = namedtuple('COC', 'mode trigger roi binning table')


class Sensicam(LibraryDriver):
    """PCO Sensicam
    """

    LIBRARY_NAME = 'senntcam.dll'

    def __init__(self, board, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.board = board

    def _return_handler(self, func_name, ret_value):
        if ret_value < 0:
            raise InstrumentError(_ERRORS[ret_value])
        elif (ret_value > 0 and
              func_name not in ('GET_COCTIME', 'GET_DELTIME', 'GET_BELTIME', 'GET_EXPTIME')):
            self.log_warning('While calling {}: {}', func_name, _ERRORS[ret_value])

        return ret_value

    def initialize(self):
        self.lib.SET_BOARD(_boardnr)
        err = self.lib.SET_INIT(1)
        self.stop_coc()

    def finalize(self):
        self.stop_coc()
        self.lib.SET_INIT(0)

    @Feat()
    def status(self):
        # Get camera type, temperature of electronics and temp. of CCD
        cam_type = ct.pointer(ct.c_int())
        temp_ele = ct.pointer(ct.c_int())
        temp_ccd = ct.pointer(ct.c_int())
        err = self.lib.GET_STATUS(cam_type, temp_ele, temp_ccd)
        #return "{}".format(_ERRORS[err])
        return cam_type, temp_ele, temp_ccd

    @Feat()
    def mode(self):
        """Imaging mode as a 3-element tuple (type, gain and submode).
        """
        _mode = self.coc.mode
        return _mode & 0xFF, (_mode >> 8) & 0xFF, (_mode >> 16) & 0xFF

    @mode.setter
    def mode(self, typ_gain_submode):
        typ, gain, submode = typ_gain_submode
        _mode = (typ & 0xFF) | ((gain & 0xFF) << 8) | ((submode & 0xFF) << 16)
        self.coc = self.recall('coc')._replace(mode=_mode)

    @Feat()
    def trigger(self):
        """Triger mode.
        """
        return self.coc.trigger

    @trigger.setter
    def trigger(self, value):
        self.coc = self.recall('coc')._replace(trigger=value)

    @Feat()
    def roi(self):
        """Region of interest in pixels as a 4-element tuple (x1, x2, y1, y2).
        """
        return self.coc.roi

    @roi.setter
    def roi(self, roi):
        roix1, roix2, roiy1, roiy2 = roi
        self.coc = self.recall('coc')._replace(roi=(roix1, roix2, roiy1, roiy2))

    @Feat()
    def binning(self):
        """Binning in pixels as a 2-element tuple (horizontal, vertical).
        """
        return self.coc.binning

    @binning.setter
    def binning(self, hbin_vbin):
        hbin, vbin = hbin_vbin
        self.coc = self.recall('coc')._replace('binning', (hbin, vbin))

    @Feat(units='ms')
    def exposure_time(self):
        """Exposure time.
        """
        return float(self.coc.table.split(',')[1])

    @exposure_time.setter
    def exposure_time(self, value):
        self.table = '0,{},-1,-1'.format(value)

    @Feat()
    def table(self):
        """COC table
        """
        return self.coc.table

    @Action()
    def stop_coc(self):
        # Stop camera
        self.lib.STOP_COC(0)

    @Action()
    def run_coc(self, runmode = 4):
         # 0 continuous - 4 single
        self.lib.RUN_COC(runmode)
        
    @Feat()
    def coc(self):
        """Command Operation Code
        """

        mode = ct.pointer(ct.c_int())
        trig = ct.pointer(ct.c_int())
        roix1 = ct.pointer(ct.c_int())
        roix2 = ct.pointer(ct.c_int())
        roiy1 = ct.pointer(ct.c_int())
        roiy2 = ct.pointer(ct.c_int())
        hbin = ct.pointer(ct.c_int())
        vbin = ct.pointer(ct.c_int())
        table = ct.create_string_buffer(40)
        self.lib.GET_SETTINGS(mode, trig, roix1, roix2, roiy1, roiy2,
                               hbin, vbin, table) #Todo: Try RetTuple

        return COC(mode[0], trig[0], (roix1[0], roix2[0], roiy1[0], roiy2[0]),
            (hbin[0], vbin[0]), table[0].decode('ascii'))

    @coc.setter
    def coc(self, value):
        newcoc = (value.mode, value.trigger) + value.roi + \
                  value.binning + (value.table, )
        self.lib.SET_COC(*newcoc)
        
    @Feat()
    def image_status(self):
        """Image status
        """
        stat = ct.pointer(ct.c_int())
        self.lib.GET_IMAGE_STATUS(stat)
        return stat

    @Feat()
    def image_size(self):
        """Image size in pixels (width, height).
        """
        width = ct.pointer(ct.c_int())
        height = ct.pointer(ct.c_int())
        self.lib.GET_IMAGE_SIZE(width, height)

        return width[0], height[0]

    @Feat(units='microseconds') #TODO: check units
    def coc_time(self):
        return self.lib.GET_COCTIME()

    @Feat(units='microseconds')
    def delay_time(self):
        return self.lib.GET_DELTIME()

    @Feat(units='microseconds')
    def exp_time(self):
        return self.lib.GET_EXPTIME()

    @Feat(units='microseconds')
    def bel_time(self):
        return self.lib.GET_BELTIME()

    @Action(units='ms')
    def expose(self, exposure = 1):
        """Expose.

        :param exposure: exposure time.

        """
        self.exposure_time = exposure
        delay = self.coc_time()
        self.run_coc()
        sleep(delay / 1000)
        while not (self.image_status & Status.COC_RUNNING):
            sleep(delay / 1000 * .1)

    @Action()
    def read_out(self):
        """Readout image from the CCD.

        :rtype: NumPy array
        """
        width, height = self.image_size
        imagearray = np.zeros((width,height), dtype=np.dtype(np.ushort))
        image = np.ascontiguousarray(imagearray)
        ptrimage = image.ctypes.data_as(ct.POINTER(ct.c_ushort))
        self.lib.READ_IMAGE_12BIT(0, width, height, ptrimage)
        return image


    @Action(units='ms')
    def take_image(self, exposure=1):
        """Take image.

        :param exposure: exposure time.
        :rtype: NumPy array
        """
        self.expose(exposure)
        return self.read_out()


if __name__ == '__main__':
    import argparse
    import lantz.log

    parser = argparse.ArgumentParser(description='Test Kentech HRI')
    parser.add_argument('-i', '--interactive', action='store_true',
                        default=False, help='Show interactive GUI')
    parser.add_argument('-b', '--board', type=int, default='0',
                        help='Board number')

    args = parser.parse_args()
    lantz.log.log_to_socket(lantz.log.DEBUG)
    with Sensicam(args.board) as inst:
        if args.interactive:
            from lantz.ui.qtwidgets import start_test_app
            start_test_app(inst)
        else:
            import matplotlib.pyplot as plt

            image = inst.take_image(10)

            print(np.min(image), np.max(image), np.mean(image))

            plt.imshow(image, cmap='gray')
            plt.show()
