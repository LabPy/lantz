# -*- coding: utf-8 -*-
"""
    lantz.drivers.ni.daqmx.channels
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Implementation of specialized channel classes.

    :copyright: 2012 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from .base import Channel, Task
from .constants import Constants


class VoltageInputChannel(Channel):
    """Creates channel(s) to measure voltage and adds the channel(s)
    to the task you specify with taskHandle.

    If your measurement requires the use of internal excitation or you need
    the voltage to be scaled by excitation, call DAQmxCreateAIVoltageChanWithExcit.

    :param phys_channel: The names of the physical channels to use
                         to create virtual channels. You can specify
                         a list or range of physical channels.
    :param channel_name: The name(s) to assign to the created virtual channel(s).
                         If you do not specify a name, NI-DAQmx uses the physical
                         channel name as the virtual channel name. If you specify
                         your own names for nameToAssignToChannel, you must use the
                         names when you refer to these channels in other NI-DAQmx
                         functions.

                         If you create multiple virtual channels with one call to
                         this function, you can specify a list of names separated by
                         commas. If you provide fewer names than the number of
                         virtual channels you create, NI-DAQmx automatically assigns
                         names to the virtual channels.

    :param terminal: {'default', 'rse', 'nrse', 'diff', 'pseudodiff'}
      The input terminal configuration for the channel:

        'default'
          At run time, NI-DAQmx chooses the default terminal
          configuration for the channel.

        'rse'
          Referenced single-ended mode

        'nrse'
          Nonreferenced single-ended mode

        'diff'
          Differential mode

        'pseudodiff'
          Pseudodifferential mode

    :param min_val: The minimum value, in units, that you expect to measure.
    :param max_val: The maximum value, in units, that you expect to measure.
    :param units: units to use to return the voltage measurements
    """

    IO_TYPE = 'AI'

    CREATE_FUN = 'CreateAIVoltageChan'

    terminal_map = dict (default = Constants.Val_Cfg_Default,
                         rse = Constants.Val_RSE,
                         nrse = Constants.Val_NRSE,
                         diff = Constants.Val_Diff,
                         pseudodiff = Constants.Val_PseudoDiff)

    def __init__(self, phys_channel, name='', terminal='default',
                 min_max=(-10., 10.), units='volts', task=None):

        if not name:
            name = ''#phys_channel

        terminal_val = self.terminal_map[terminal]

        if units != 'volts':
            custom_scale_name = units
            units = Constants.Val_FromCustomScale
        else:
            custom_scale_name = None
            units =  Constants.Val_Volts

        self._create_args = (phys_channel, name, terminal_val,
                             min_max[0], min_max[1], units, custom_scale_name)

        super().__init__(task=task, name=name)


class VoltageOutputChannel(Channel):
    """Creates channel(s) to generate voltage and adds the channel(s)
    to the task you specify with taskHandle.

        See VoltageOutputChannel
    """

    CHANNEL_TYPE = 'AO'

    def __init__(self, phys_channel, channel_name='', terminal='default', min_max=(-1, -1), units='volts'):

        terminal_val = self.terminal_map[terminal]

        if units != 'volts':
            custom_scale_name = units
            units = Constants.FROM_CUSTOM_SCALE
        else:
            custom_scale_name = None
            units =  Constants.VOLTS

        err = self.lib.CreateAOVoltageChan(phys_channel, channel_name,
                                           min_max[0], min_max[1], units, custom_scale_name)

# Not implemented:
# DAQmxCreateAIAccelChan, DAQmxCreateAICurrentChan, DAQmxCreateAIFreqVoltageChan,
# DAQmxCreateAIMicrophoneChan, DAQmxCreateAIResistanceChan, DAQmxCreateAIRTDChan,
# DAQmxCreateAIStrainGageChan, DAQmxCreateAITempBuiltInSensorChan,
# DAQmxCreateAIThrmcplChan, DAQmxCreateAIThrmstrChanIex, DAQmxCreateAIThrmstrChanVex,
# DAQmxCreateAIVoltageChanWithExcit
# DAQmxCreateAIPosLVDTChan, DAQmxCreateAIPosRVDTChan/
# DAQmxCreateTEDSAI*

# Not implemented: DAQmxCreateAOCurrentChan
# DAQmxCreateDIChan, DAQmxCreateDOChan
# DAQmxCreateCI*, DAQmxCreateCO*


class DigitalInputChannel(Channel):
    """
    Creates channel(s) to measure digital signals and adds the
    channel(s) to the task you specify with taskHandle. You can
    group digital lines into one digital channel or separate them
    into multiple digital channels. If you specify one or more
    entire ports in lines by using port physical channel names,
    you cannot separate the ports into multiple channels. To
    separate ports into multiple channels, use this function
    multiple times with a different port each time.

    Parameters
    ----------

    lines : str

      The names of the digital lines used to create a virtual
      channel. You can specify a list or range of lines.

    name : str

      The name of the created virtual channel(s). If you create
      multiple virtual channels with one call to this function,
      you can specify a list of names separated by commas. If you
      do not specify a name, NI-DAQmx uses the physical channel
      name as the virtual channel name. If you specify your own
      names for name, you must use the names when you refer to
      these channels in other NI-DAQmx functions.

    group_by : {'line', 'all_lines'}

      Specifies whether to group digital lines into one or more
      virtual channels. If you specify one or more entire ports in
      lines, you must set grouping to 'for_all_lines':

        'line' - One channel for each line

        'all_lines' - One channel for all lines
    """


    def __init__(self, lines, name='', group_by='line'):

        if group_by == 'line':
            grouping_val = Constants.ChanPerLine
            self.one_channel_for_all_lines = False
        else:
            grouping_val = Constants.ChanForAllLines
            self.one_channel_for_all_lines = True

        self.lib.CreateDIChan(lines, name, grouping_val)


class DigitalOutputChannel(Channel):
    """
    Creates channel(s) to generate digital signals and adds the
    channel(s) to the task you specify with taskHandle. You can
    group digital lines into one digital channel or separate them
    into multiple digital channels. If you specify one or more
    entire ports in lines by using port physical channel names,
    you cannot separate the ports into multiple channels. To
    separate ports into multiple channels, use this function
    multiple times with a different port each time.

    See DigitalInputChannel
    """

    def __init__(self, lines, name='', group_by='line'):

        if group_by == 'line':
            grouping_val = Constants.ChanPerLine
            self.one_channel_for_all_lines = False
        else:
            grouping_val = Constants.ChanForAllLines
            self.one_channel_for_all_lines = True

        self.lib.CreateDOChan(lines, name, grouping_val)


class CountEdgesChannel(Channel):
    """
    Creates a channel to count the number of rising or falling
    edges of a digital signal and adds the channel to the task you
    specify with taskHandle. You can create only one counter input
    channel at a time with this function because a task can
    include only one counter input channel. To read from multiple
    counters simultaneously, use a separate task for each
    counter. Connect the input signal to the default input
    terminal of the counter unless you select a different input
    terminal.

    Parameters
    ----------

    counter : str

      The name of the counter to use to create virtual channels.

    name : str

      The name(s) to assign to the created virtual channel(s). If
      you do not specify a name, NI-DAQmx uses the physical
      channel name as the virtual channel name. If you specify
      your own names for nameToAssignToChannel, you must use the
      names when you refer to these channels in other NI-DAQmx
      functions.

      If you create multiple virtual channels with one call to
      this function, you can specify a list of names separated by
      commas. If you provide fewer names than the number of
      virtual channels you create, NI-DAQmx automatically assigns
      names to the virtual channels.

    edge : {'rising', 'falling'}

      Specifies on which edges of the input signal to increment or
      decrement the count, rising or falling edge(s).

    init : int

      The value from which to start counting.

    direction : {'up', 'down', 'ext'}

      Specifies whether to increment or decrement the
      counter on each edge:

        'up' - Increment the count register on each edge.

        'down' - Decrement the count register on each edge.

        'ext' - The state of a digital line controls the count
        direction. Each counter has a default count direction
        terminal.
    """

    CHANNEL_TYPE = 'CI'


    def __init__ (self, counter, name="", edge='rising', init=0, direction='up'):

        if edge == 'rising':
            edge_val = Constants.RISING
        else:
            edge_val = Constants.FALLING

        if direction == 'up':
            direction_val = Constants.COUNT_UP
        else:
            direction_val = Constants.COUNT_DOWN

        self.lib.CreateCICountEdgesChan(counter, name, edge_val, direction_val)


class LinearEncoderChannel(Channel):
    """
    Creates a channel that uses a linear encoder to measure linear position.
    You can create only one counter input channel at a time with this function
    because a task can include only one counter input channel. To read from
    multiple counters simultaneously, use a separate task for each counter.
    Connect the input signals to the default input terminals of the counter
    unless you select different input terminals.

    Parameters
    ----------

    counter : str

      The name of the counter to use to create virtual channels.

    name : str

      The name(s) to assign to the created virtual channel(s). If
      you do not specify a name, NI-DAQmx uses the physical
      channel name as the virtual channel name. If you specify
      your own names for nameToAssignToChannel, you must use the
      names when you refer to these channels in other NI-DAQmx
      functions.

      If you create multiple virtual channels with one call to
      this function, you can specify a list of names separated by
      commas. If you provide fewer names than the number of
      virtual channels you create, NI-DAQmx automatically assigns
      names to the virtual channels.

    decodingType : {'X1', 'X2', 'X4', 'TwoPulseCounting'}

      Specifies how to count and interpret the pulses that the encoder
      generates on signal A and signal B. X1, X2, and X4 are valid for
      quadrature encoders only. TwoPulseCounting is valid only for
      two-pulse encoders.

      X2 and X4 decoding are more sensitive to smaller changes in position
      than X1 encoding, with X4 being the most sensitive. However, more
      sensitive decoding is more likely to produce erroneous measurements
      if there is vibration in the encoder or other noise in the signals.

    ZidxEnable : bool

      Specifies whether to enable z indexing for the measurement.

    ZidxVal : float

      The value, in units, to which to reset the measurement when signal Z
      is high and signal A and signal B are at the states you specify with
      ZidxPhase.

    ZidxPhase : {'AHighBHigh', 'AHighBLow', 'ALowBHigh', 'ALowBLow'}

      The states at which signal A and signal B must be while signal Z is high
      for NI-DAQmx to reset the measurement. If signal Z is never high while
      the signal A and signal B are high, for example, you must choose a phase
      other than Constants.Val_AHighBHigh.

      When signal Z goes high and how long it stays high varies from encoder to
      encoder. Refer to the documentation for the encoder to determine the
      timing of signal Z with respect to signal A and signal B.

    units  : {'Meters', 'Inches', 'Ticks', 'FromCustomScale'}

      The units to use to return linear position measurements from the channel.

    distPerPulse : float

      The distance measured for each pulse the encoder generates. Specify this
      value in units.

    init : float

      The position of the encoder when the measurement begins. This value is
      in units.

    customScaleName : str

      The name of a custom scale to apply to the channel. To use this parameter,
      you must set units to Constants.Val_FromCustomScale. If you do not set units
      to FromCustomScale, you must set customScaleName to NULL.
    """

    def __init__(
            self,
            counter,
            name="",
            decodingType='X1',
            ZidxEnable=False,
            ZidxVal=0.0,
            ZidxPhase='AHighBHigh',
            units='Ticks',
            distPerPulse=1.0,
            init=0.0,
            customScaleName=None
    ):
        counter = str(counter)
        name = str(name)

        decodingType_map = dict(X1=Constants.Val_X1, X2=Constants.Val_X2, X4=Constants.Val_X4,
                                TwoPulseCounting=Constants.Val_TwoPulseCounting)
        ZidxPhase_map = dict(AHighBHigh=Constants.Val_AHighBHigh, AHighBLow=Constants.Val_AHighBLow,
                             ALowBHigh=Constants.Val_ALowBHigh, ALowBLow=Constants.Val_ALowBLow)
        units_map = dict(Meters=Constants.Val_Meters, Inches=Constants.Val_Inches,
                         Ticks=Constants.Val_Ticks, FromCustomScale=Constants.Val_FromCustomScale)

        decodingType_val = self._get_map_value ('decodingType', decodingType_map, decodingType)
        ZidxPhase_val = self._get_map_value ('ZidxPhase', ZidxPhase_map, ZidxPhase)
        units_val = self._get_map_value ('units', units_map, units)

        if units_val != Constants.Val_FromCustomScale:
            customScaleName = None

        return CALL(
            'CreateCILinEncoderChan',
            self,
            counter,
            name,
            decodingType_val,
            bool32(ZidxEnable),
            float64(ZidxVal),
            ZidxPhase_val,
            units_val,
            float64(distPerPulse),
            float64(init),
            customScaleName
        )==0


class MeasureFrequencyChannel(Channel):
    """
    Creates a channel to measure the frequency of a digital signal
    and adds the channel to the task. You can create only one
    counter input channel at a time with this function because a
    task can include only one counter input channel. To read from
    multiple counters simultaneously, use a separate task for each
    counter. Connect the input signal to the default input
    terminal of the counter unless you select a different input
    terminal.

    Parameters
    ----------

    counter : str
      The name of the counter to use to create virtual channels.

    name : str
      The name(s) to assign to the created virtual channel(s). If
      you do not specify a name, NI-DAQmx uses the physical
      channel name as the virtual channel name. If you specify
      your own names for nameToAssignToChannel, you must use the
      names when you refer to these channels in other NI-DAQmx
      functions.

      If you create multiple virtual channels with one call to
      this function, you can specify a list of names separated by
      commas. If you provide fewer names than the number of
      virtual channels you create, NI-DAQmx automatically assigns
      names to the virtual channels.

    min_val : float
      The minimum value, in units, that you expect to measure.

    max_val : float
      The maximum value, in units, that you expect to measure.

    units : {'hertz', 'ticks', 'custom'}
      Units to use to return the measurement and to specify the
      min/max expected value.

      'hertz' - Hertz, cycles per second
      'ticks' - timebase ticks
      'custom' - use custom_scale_name to specify units

    edge : {'rising', 'falling'}
      Specifies which edges to measure the frequency or period of the signal.

    method : {'low_freq', 'high_freq', 'large_range'}
      The method used to calculate the period or frequency of the
      signal.  See the M series DAQ User Manual (371022K-01), page
      7-9 for more information.

        'low_freq'
          Use one counter that uses a constant timebase to measure
          the input signal.

        'high_freq'
          Use two counters, one of which counts pulses of the
          signal to measure during the specified measurement time.

        'large_range'
          Use one counter to divide the frequency of the input
          signal to create a lower frequency signal that the
          second counter can more easily measure.

    meas_time : float
      The length of time to measure the frequency or period of the
      signal, when meas_method is 'high_freq'.  Measurement accuracy
      increases with increased meas_time and with increased signal
      frequency.  Ensure that the meas_time is low enough to prevent
      the counter register from overflowing.

    divisor : int
      The value by which to divide the input signal, when
      meas_method is 'large_range'. The larger this value, the more
      accurate the measurement, but too large a value can cause the
      count register to roll over, resulting in an incorrect
      measurement.

    custom_scale_name : str
      The name of a custom scale to apply to the channel. To use
      this parameter, you must set units to 'custom'.  If you do
      not set units to 'custom', you must set custom_scale_name to
      None.
    """

    def __init__(self, counter, name='', min_val=1e2, max_val=1e3,
                            units="hertz", edge="rising", method="low_freq",
                            meas_time=1.0, divisor=1, custom_scale_name=None):

        self.data_type = float

        assert divisor > 0

        if method == 'low_freq':
            meas_meth_val = Constants.LOW_FREQ1_CTR
        elif method == 'high_freq':
            meas_meth_val = Constants.HIGH_FREQ2_CTR
        elif method == 'large_range':
            meas_meth_val = Constants.LARGE_RANGE2_CTR


        if units != ('hertz', 'ticks'):
            custom_scale_name = units
            units = Constants.FROM_CUSTOM_SCALE
        else:
            custom_scale_name = None
            if units == 'hertz':
                units =  Constants.HZ
            else:
                units = Contstants.TICKS

        self.lib.CreateCIFreqChan(counter, name, min_max[0], min_max[1],
                                  units_val, edge_val, meas_meth_val,
                                  meas_time, divisor, custom_scale_name)



def create_channel_frequency(self, counter, name="", units='hertz', idle_state='low',
                             delay=0.0, freq=1.0, duty_cycle=0.5):
    """
    Creates channel(s) to generate digital pulses that freq and
    duty_cycle define and adds the channel to the task.  The
    pulses appear on the default output terminal of the counter
    unless you select a different output terminal.

    Parameters
    ----------

    counter : str

      The name of the counter to use to create virtual
      channels. You can specify a list or range of physical
      channels.

    name : str

      The name(s) to assign to the created virtual channel(s). If
      you do not specify a name, NI-DAQmx uses the physical
      channel name as the virtual channel name. If you specify
      your own names for nameToAssignToChannel, you must use the
      names when you refer to these channels in other NI-DAQmx
      functions.

      If you create multiple virtual channels with one call to
      this function, you can specify a list of names separated by
      commas. If you provide fewer names than the number of
      virtual channels you create, NI-DAQmx automatically assigns
      names to the virtual channels.

    units : {'hertz'}

      The units in which to specify freq:

        'hertz' - hertz

    idle_state : {'low', 'high'}

      The resting state of the output terminal.

    delay : float

      The amount of time in seconds to wait before generating the
      first pulse.

    freq : float

      The frequency at which to generate pulses.

    duty_cycle : float

      The width of the pulse divided by the pulse period. NI-DAQmx
      uses this ratio, combined with frequency, to determine pulse
      width and the interval between pulses.

    Returns
    -------

      success_status : bool
    """
    counter = str(counter)
    name = str(name)
    units_map = dict (hertz = Constants.Val_Hz)
    idle_state_map = dict (low=Constants.Val_Low, high=Constants.Val_High)
    units_val = self._get_map_value('units', units_map, units)
    idle_state_val = self._get_map_value('idle_state', idle_state_map, idle_state)
    self.lib.CreateCOPulseChanFreq(counter, name, units_val, idle_state_val,
                                   delay, freq, (duty_cycle))

def create_channel_ticks(self, counter, name="", source="", idle_state='low',
                         delay = 0, low_ticks=1, high_ticks=1):
    """
    Creates channel(s) to generate digital pulses defined by the
    number of timebase ticks that the pulse is at a high state and
    the number of timebase ticks that the pulse is at a low state
    and also adds the channel to the task. The pulses appear on
    the default output terminal of the counter unless you select a
    different output terminal.

    Parameters
    ----------

    counter : str

      The name of the counter to use to create virtual
      channels. You can specify a list or range of physical
      channels.

    name : str

      The name(s) to assign to the created virtual channel(s). If
      you do not specify a name, NI-DAQmx uses the physical
      channel name as the virtual channel name. If you specify
      your own names for nameToAssignToChannel, you must use the
      names when you refer to these channels in other NI-DAQmx
      functions.

      If you create multiple virtual channels with one call to
      this function, you can specify a list of names separated by
      commas. If you provide fewer names than the number of
      virtual channels you create, NI-DAQmx automatically assigns
      names to the virtual channels.

    source : str

      The terminal to which you connect an external timebase. You
      also can specify a source terminal by using a terminal name.

    idle_state : {'low', 'high'}

      The resting state of the output terminal.

    delay : int

      The number of timebase ticks to wait before generating the
      first pulse.

    low_ticks : int

      The number of timebase ticks that the pulse is low.

    high_ticks : int

      The number of timebase ticks that the pulse is high.

    Returns
    -------

      success_status : bool
    """
    counter = str(counter)
    name = str(name)
    idle_state_map = dict (low=Constants.Val_Low, high=Constants.Val_High)
    idle_state_val = self._get_map_value('idle_state', idle_state_map, idle_state)
    return CALL('CreateCOPulseChanTicks', self, counter, name, source, idle_state_val,
                int32 (delay), int32 (low_ticks), int32 (high_ticks))==0

def create_channel_time(self, counter, name="", units="seconds", idle_state='low',
                        delay = 0, low_time=1, high_time=1):
    """
    Creates channel(s) to generate digital pulses defined by the
    number of timebase ticks that the pulse is at a high state and
    the number of timebase ticks that the pulse is at a low state
    and also adds the channel to the task. The pulses appear on
    the default output terminal of the counter unless you select a
    different output terminal.

    Parameters
    ----------

    counter : str

      The name of the counter to use to create virtual
      channels. You can specify a list or range of physical
      channels.

    name : str

      The name(s) to assign to the created virtual channel(s). If
      you do not specify a name, NI-DAQmx uses the physical
      channel name as the virtual channel name. If you specify
      your own names for nameToAssignToChannel, you must use the
      names when you refer to these channels in other NI-DAQmx
      functions.

      If you create multiple virtual channels with one call to
      this function, you can specify a list of names separated by
      commas. If you provide fewer names than the number of
      virtual channels you create, NI-DAQmx automatically assigns
      names to the virtual channels.

    units : {'seconds'}

      The units in which to specify high and low time.

    idle_state : {'low', 'high'}

      The resting state of the output terminal.

    delay : float

      The amount of time in seconds to wait before generating the
      first pulse.

    low_time : float

      The amount of time the pulse is low, in seconds.

    high_time : float

      The amount of time the pulse is high, in seconds.

    Returns
    -------

      success_status : bool
    """
    counter = str(counter)
    name = str(name)
    units_map = dict (seconds = Constants.Val_Seconds)
    idle_state_map = dict (low=Constants.Val_Low, high=Constants.Val_High)
    units_val = self._get_map_value('units', units_map, units)
    idle_state_val = self._get_map_value('idle_state', idle_state_map, idle_state)
    return CALL('CreateCOPulseChanTime', self, counter, name, units_val, idle_state_val,
                float64 (delay), float64(low_time), float64(high_time))==0
