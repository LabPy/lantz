# -*- coding: utf-8 -*-
"""
    lantz.drivers.andor.neo
    ~~~~~~~~~~~~~~~~~~~~~~~

    Implements a high level driver for the Andor Neo CMOS Camera


    Sources::

        - Andor Neo Manual

    :copyright: 2012 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""


import ctypes as ct

import numpy as np

from lantz import Feat, Action, Q_
from lantz.foreign import RetStr, RetTuple

from .andor import Andor

class Neo(Andor):
    """Neo Andor CMOS Camera
    """

    def initialize(self):
        super().initialize()
        self.flush()
        self.fan_speed = 1
        self.width ,self.height = self.sensor_size
        self.length = self.width * self.height
        self.clock_rate = 100
        self.pixel_encoding = 32
        self.imagesizebytes = self.getint("ImageSizeBytes")
        self.userbuffer = ct.create_string_buffer(' ' * self.imagesizebytes)

    @Feat(None, values={32: 'Mono32', 64: 'Mono64'})
    def pixel_encoding(self, value):
        """Pixel encoding.
        """
        self.setenumstring("PixelEncoding", value)

    @Feat()
    def sensor_size(self):
        width = self.getint("SensorWidth")
        height = self.getint("SensorHeight")        
        return width, height

    @Feat(None, values={100: '100 MHz', 200: '200 MHz', 280: '280 MHz'})
    def clock_rate(self, value):
        """Pixel clock rate
        """
        self.setenumstring("PixelReadoutRate", value)

    @Feat(None)
    def fan_peed(self, value = 1):
        """Fan speed.
        """
        self.setenumerated("FanSpeed", value)

    @Feat()
    def sensor_temp(self):
        """Sensor temperature.
        """
        return self.getfloat("SensorTemperature")

    @Feat()
    def exposure_time(self):
        """Get exposure time.
        """
        return self.getfloat("ExposureTime")

    @exposure_time.setter
    def exposure_time(self, exposure):
        self.setfloat("ExposureTime", exposure)

    @Feat(None)
    def roi(self, width_height_top_left):
        """Set region of interest
        """
        width, height, top, left = width_height_top_left
        self.setint("AOIWidth", width)
        self.setint("AOILeft", left)
        self.setint("AOIHeight", height)
        self.setint("AOITop", top)

    @Action()
    def take_image(self):
        """Image acquisition.
        """
        self.queuebuffer(self.userbuffer, self.imagesizebytes)
        self.command("AcquisitionStart")
        self.waitbuffer(*RetStr(1))
        self.command("AcquisitionStop")
        self.flush()
        image = np.fromstring(self.userbuffer, dtype=np.uint32, count=self.length)
        image.shape = (self.height, self.width)
        return image

    @Action()
    def take_image(self, numbuff, numframes):
        """Image acquisition with circular buffer.
        """
        imagesizebytes = self.getint("ImageSizeBytes")
        userbuffer = []
        for i in range(numbuff):
            userbuffer.append(ct.create_string_buffer(' ' * imagesizebytes))
        self.queuebuffer(userbuffer, imagesizebytes)
        self.command("AcquisitionStart")
        for i in range(numbuff):
            self.waitbuffer(*RetStr(1))
            self.queuebuffer(userbuffer[i], imagesizebytes)
        self.command("AcquisitionStop")
        self.flush()
        image = np.fromstring(userbuffer[0], dtype=np.uint32, count=self.length)
        image.shape = (self.height, self.width)
        return image
