# -*- coding: utf-8 -*-
"""
    lantz.drivers.ni.daqmx.tasks
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Implementation of specialized tasks clases.

    :copyright: 2012 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

import numpy as np

from lantz import Feat, Action
from lantz.foreign import RetStr, RetTuple, RetValue

from .base import Task, Channel
from .constants import Constants

_GROUP_BY = {'scan': Constants.Val_GroupByScanNumber,
             'channel': Constants.Val_GroupByChannel}



class AnalogInputTask(Task):
    """Analog Input Task
    """

    IO_TYPE = 'AI'

    @Feat()
    def max_convert_rate(self):
        """Maximum convert rate supported by the task, given the current
        devices and channel count.

        This rate is generally faster than the default AI Convert
        Clock rate selected by NI-DAQmx, because NI-DAQmx adds in an
        additional 10 microseconds per channel settling time to
        compensate for most potential system settling constraints.

        For single channel tasks, the maximum AI Convert Clock rate is the
        maximum rate of the ADC. For multiple channel tasks, the maximum
        AI Convert Clock rate is the maximum convert rate of the analog
        hardware, including the ADC, filters, multiplexers, and amplifiers.
        Signal conditioning accessories can further constrain the maximum AI
        Convert Clock based on timing and settling requirements.
        """
        err, value = self.lib.GetAIConvMaxRate(RetValue('f64'))
        return value

    def read_scalar(self, timeout=10.0):
        """Return a single floating-point sample from a task that
        contains a single analog input channel.

        :param timeout:  The amount of time, in seconds, to wait for the function to
                         read the sample(s). The default value is 10.0 seconds. To
                         specify an infinite wait, pass -1 (DAQmx_Val_WaitInfinitely).
                         This function returns an error if the timeout elapses.

                         A value of 0 indicates to try once to read the requested
                         samples. If all the requested samples are read, the function
                         is successful. Otherwise, the function returns a timeout error
                         and returns the samples that were actually read.

        :rtype: float
        """

        err, value = self.lib.ReadAnalogScalarF64(timeout, RetValue('f64'), None)
        return value

    @Action(units=(None, 'seconds', None), values=(None, None, _GROUP_BY))
    def read(self, samples_per_channel=None, timeout=10.0, group_by='channel'):
        """Reads multiple floating-point samples from a task that
        contains one or more analog input channels.

        :param samples_per_channel:
          The number of samples, per channel, to read. The default
          value of -1 (DAQmx_Val_Auto) reads all available samples. If
          readArray does not contain enough space, this function
          returns as many samples as fit in readArray.

          NI-DAQmx determines how many samples to read based on
          whether the task acquires samples continuously or acquires a
          finite number of samples.

          If the task acquires samples continuously and you set this
          parameter to -1, this function reads all the samples
          currently available in the buffer.

          If the task acquires a finite number of samples and you set
          this parameter to -1, the function waits for the task to
          acquire all requested samples, then reads those samples. If
          you set the Read All Available Samples property to TRUE, the
          function reads the samples currently available in the buffer
          and does not wait for the task to acquire all requested
          samples.

        :param timeout: float
          The amount of time, in seconds, to wait for the function to
          read the sample(s). The default value is 10.0 seconds. To
          specify an infinite wait, pass -1
          (DAQmx_Val_WaitInfinitely). This function returns an error
          if the timeout elapses.

          A value of 0 indicates to try once to read the requested
          samples. If all the requested samples are read, the function
          is successful. Otherwise, the function returns a timeout
          error and returns the samples that were actually read.

        :param group_by:

            'channel'
              Group by channel (non-interleaved)::

                ch0:s1, ch0:s2, ..., ch1:s1, ch1:s2,..., ch2:s1,..

            'scan'
              Group by scan number (interleaved)::

                ch0:s1, ch1:s1, ch2:s1, ch0:s2, ch1:s2, ch2:s2,...

        :rtype: numpy.ndarray
        """

        if samples_per_channel is None:
            samples_per_channel = self.samples_per_channel_available()

        number_of_channels = self.number_of_channels()
        if group_by == Constants.Val_GroupByScanNumber:
            data = np.zeros((samples_per_channel, number_of_channels), dtype=np.float64)
        else:
            data = np.zeros((number_of_channels, samples_per_channel), dtype=np.float64)

        err, data, count = self.lib.ReadAnalogF64(samples_per_channel, timeout, group_by,
                                                  data.ctypes.data, data.size, RetValue('i32'), None)

        if samples_per_channel < count:
            if group_by == 'scan':
                return data[:count]
            else:
                return data[:,:count]

        return data


class AnalogOutputTask(Task):
    """Analog Output Task
    """

    CHANNEL_TYPE = 'AO'

    @Action(units=(None, None, 'seconds', None), values=(None, None, None, _GROUP_BY))
    def write(self, data, auto_start=True, timeout=10.0, group_by='scan'):
        """Write multiple floating-point samples or a scalar to a task
        that contains one or more analog output channels.

        Note: If you configured timing for your task, your write is
        considered a buffered write. Buffered writes require a minimum
        buffer size of 2 samples. If you do not configure the buffer
        size using DAQmxCfgOutputBuffer, NI-DAQmx automatically
        configures the buffer when you configure sample timing. If you
        attempt to write one sample for a buffered write without
        configuring the buffer, you will receive an error.

        :param data: The array of 64-bit samples to write to the task
                     or a scalar.

        :param auto_start: Whether or not this function automatically starts
                           the task if you do not start it.

        :param timeout: The amount of time, in seconds, to wait for this
                        function to write all the samples. The default value is 10.0
                        seconds. To specify an infinite wait, pass -1
                        (DAQmx_Val_WaitInfinitely). This function returns an error
                        if the timeout elapses.

                        A value of 0 indicates to try once to write the submitted
                        samples. If this function successfully writes all submitted
                        samples, it does not return an error. Otherwise, the
                        function returns a timeout error and returns the number of
                        samples actually written.

        :param group_by: how the samples are arranged, either interleaved or noninterleaved

            'channel' - Group by channel (non-interleaved).

            'scan' - Group by scan number (interleaved).

        :return: The actual number of samples per channel successfully
                 written to the buffer.

        """
        if np.isscalar(data):
            err = self.lib.WriteAnalogScalarF64(bool32(auto_start),
                                                float64(timeout),
                                                float64(data), None)
            return 1

        data = np.asarray(data, dtype = np.float64)

        number_of_channels = self.number_of_channels()

        if data.ndims == 1:
            if number_of_channels == 1:
                samples_per_channel = data.shape[0]
                shape = (samples_per_channel, 1)
            else:
                samples_per_channel = data.size / number_of_channels
                shape = (samples_per_channel, number_of_channels)

            if not group_by == Constants.Val_GroupByScanNumber:
                shape = tuple(reversed(shape))

            data.reshape(shape)
        else:
            if group_by == Constants.Val_GroupByScanNumber:
                samples_per_channel = data.shape[0]
            else:
                samples_per_channel = data.shape[-1]

        err, count = self.lib.WriteAnalogF64(samples_per_channel, auto_start,
                                             timeout, group_by,
                                             data.ctypes.data, RetValue('i32'),
                                             None)

        return count


class DigitalTask(Task):

    @Action(units=(None, 'seconds', None), values=(None, None, _GROUP_BY))
    def read(self, samples_per_channel=None, timeout=10.0, group_by='scan'):
        """
        Reads multiple samples from each digital line in a task. Each
        line in a channel gets one byte per sample.

        :param samples_per_channel: int or None

          The number of samples, per channel, to
          read. The default value of -1 (DAQmx_Val_Auto) reads all
          available samples. If readArray does not contain enough
          space, this function returns as many samples as fit in
          readArray.

          NI-DAQmx determines how many samples to read based on
          whether the task acquires samples continuously or acquires a
          finite number of samples.

          If the task acquires samples continuously and you set this
          parameter to -1, this function reads all the samples
          currently available in the buffer.

          If the task acquires a finite number of samples and you set
          this parameter to -1, the function waits for the task to
          acquire all requested samples, then reads those samples. If
          you set the Read All Available Data property to TRUE, the
          function reads the samples currently available in the buffer
          and does not wait for the task to acquire all requested
          samples.

        :param timeout: float

          The amount of time, in seconds, to wait for the function to
          read the sample(s). The default value is 10.0 seconds. To
          specify an infinite wait, pass -1
          (DAQmx_Val_WaitInfinitely). This function returns an error
          if the timeout elapses.

          A value of 0 indicates to try once to read the requested
          samples. If all the requested samples are read, the function
          is successful. Otherwise, the function returns a timeout
          error and returns the samples that were actually read.

        :param group_by: {'group', 'scan'}

          Specifies whether or not the samples are interleaved:

            'channel' - Group by channel (non-interleaved).

            'scan' - Group by scan number (interleaved).

        Returns
        -------

          data : array

            The array to read samples into. Each `bytes_per_sample`
            corresponds to one sample per channel, with each element
            in that grouping corresponding to a line in that channel,
            up to the number of lines contained in the channel.

          bytes_per_sample : int

            The number of elements in returned `data` that constitutes
            a sample per channel. For each sample per channel,
            `bytes_per_sample` is the number of bytes that channel
            consists of.

        """

        if samples_per_channel in (None, -1):
            samples_per_channel = self.samples_per_channel_available()

        if self.one_channel_for_all_lines:
            nof_lines = []
            for channel in self.names_of_channels():
                nof_lines.append(self.number_of_lines (channel))
            c = int (max (nof_lines))
            dtype = getattr(np, 'uint%s' % (8 * c))
        else:
            c = 1
            dtype = np.uint8

        number_of_channels = self.number_of_channels()

        if group_by == Constants.Val_GroupByScanNumber:
            data = np.zeros((samples_per_channel, number_of_channels),dtype=dtype)
        else:
            data = np.zeros((number_of_channels, samples_per_channel),dtype=dtype)

        err, count, bps = self.lib.ReadDigitalLines(samples_per_channel, float64 (timeout),
              group_by, data.ctypes.data, uInt32 (data.size * c),
              RetValue('i32'), RetValue('i32'),
              None
        )
        if count < samples_per_channel:
            if group_by == 'scan':
                return data[:count], bps
            else:
                return data[:,:count], bps
        return data, bps


class DigitalInputTask(DigitalTask):
    """Exposes NI-DAQmx digital input task to Python.
    """

    CHANNEL_TYPE = 'DI'


class DigitalOutputTask(DigitalTask):
    """Exposes NI-DAQmx digital output task to Python.
    """

    CHANNEL_TYPE = 'DO'

    @Action(units=(None, None, 'seconds', None), values=(None, {True, False}, None, _GROUP_BY))
    def write(self, data, auto_start=True, timeout=10.0, group_by='scan'):
        """
        Writes multiple samples to each digital line in a task. When
        you create your write array, each sample per channel must
        contain the number of bytes returned by the
        DAQmx_Read_DigitalLines_BytesPerChan property.

	Note: If you configured timing for your task, your write is
	considered a buffered write. Buffered writes require a minimum
	buffer size of 2 samples. If you do not configure the buffer
	size using DAQmxCfgOutputBuffer, NI-DAQmx automatically
	configures the buffer when you configure sample timing. If you
	attempt to write one sample for a buffered write without
	configuring the buffer, you will receive an error.

        Parameters
        ----------

        data : array

          The samples to write to the task.

        auto_start : bool

          Specifies whether or not this function automatically starts
          the task if you do not start it.

        timeout : float

          The amount of time, in seconds, to wait for this function to
          write all the samples. The default value is 10.0 seconds. To
          specify an infinite wait, pass -1
          (DAQmx_Val_WaitInfinitely). This function returns an error
          if the timeout elapses.

          A value of 0 indicates to try once to write the submitted
          samples. If this function successfully writes all submitted
          samples, it does not return an error. Otherwise, the
          function returns a timeout error and returns the number of
          samples actually written.

        layout : {'group_by_channel', 'group_by_scan_number'}

          Specifies how the samples are arranged, either interleaved
          or noninterleaved:

            'group_by_channel' - Group by channel (non-interleaved).

            'group_by_scan_number' - Group by scan number (interleaved).
        """

        number_of_channels = self.get_number_of_channels()

        if np.isscalar(data):
            data = np.array([data]*number_of_channels, dtype = np.uint8)
        else:
            data = np.asarray(data, dtype = np.uint8)

        if data.ndims == 1:
            if number_of_channels == 1:
                samples_per_channel = data.shape[0]
                shape = (samples_per_channel, 1)
            else:
                samples_per_channel = data.size / number_of_channels
                shape = (samples_per_channel, number_of_channels)

            if not group_by == Constants.Val_GroupByScanNumber:
                shape = tuple(reversed(shape))

            data.reshape(shape)
        else:
            if group_by == Constants.Val_GroupByScanNumber:
                samples_per_channel = data.shape[0]
            else:
                samples_per_channel = data.shape[-1]

        err, count = self.lib.WriteDigitalLines(samples_per_channel,
                                                bool32(auto_start),
                                                float64(timeout), group_by,
                                                data.ctypes.data, RetValue('u32'), None)

        return count

        # NotImplemented: WriteDigitalU8, WriteDigitalU16, WriteDigitalU32, WriteDigitalScalarU32

class CounterInputTask(Task):
    """Exposes NI-DAQmx counter input task to Python.
    """

    CHANNEL_TYPE = 'CI'

    def read_scalar(self, timeout=10.0):
        """Read a single floating-point sample from a counter task. Use
        this function when the counter sample is scaled to a
        floating-point value, such as for frequency and period
        measurement.

        :param float:
          The amount of time, in seconds, to wait for the function to
          read the sample(s). The default value is 10.0 seconds. To
          specify an infinite wait, pass -1
          (DAQmx_Val_WaitInfinitely). This function returns an error if
          the timeout elapses.

          A value of 0 indicates to try once to read the requested
          samples. If all the requested samples are read, the function
          is successful. Otherwise, the function returns a timeout error
          and returns the samples that were actually read.

        :return: The sample read from the task.
        """

        err, value = self.lib.ReadCounterScalarF64(timeout, RetValue('f64'), None)
        return value

    def read(self, samples_per_channel=None, timeout=10.0):
        """Read multiple 32-bit integer samples from a counter task.
        Use this function when counter samples are returned unscaled,
        such as for edge counting.

        :param samples_per_channel:
          The number of samples, per channel, to read. The default
          value of -1 (DAQmx_Val_Auto) reads all available samples. If
          readArray does not contain enough space, this function
          returns as many samples as fit in readArray.

          NI-DAQmx determines how many samples to read based on
          whether the task acquires samples continuously or acquires a
          finite number of samples.

          If the task acquires samples continuously and you set this
          parameter to -1, this function reads all the samples
          currently available in the buffer.

          If the task acquires a finite number of samples and you set
          this parameter to -1, the function waits for the task to
          acquire all requested samples, then reads those samples. If
          you set the Read All Available Samples property to TRUE, the
          function reads the samples currently available in the buffer
          and does not wait for the task to acquire all requested
          samples.

        :param timeout:
          The amount of time, in seconds, to wait for the function to
          read the sample(s). The default value is 10.0 seconds. To
          specify an infinite wait, pass -1
          (DAQmx_Val_WaitInfinitely). This function returns an error
          if the timeout elapses.

          A value of 0 indicates to try once to read the requested
          samples. If all the requested samples are read, the function
          is successful. Otherwise, the function returns a timeout
          error and returns the samples that were actually read.


        :return: The array of samples read.
        """

        if samples_per_channel is None:
            samples_per_channel = self.samples_per_channel_available()

        data = np.zeros((samples_per_channel,),dtype=np.int32)

        err, count = self.lib.ReadCounterU32(samples_per_channel, float64(timeout),
                                             data.ctypes.data, data.size, RetValue('i32'), None)

        return data[:count]


class CounterOutputTask(Task):

    """Exposes NI-DAQmx counter output task to Python.
    """

    channel_type = 'CO'


Task.register_class(AnalogInputTask)
