# -*- coding: utf-8 -*-
"""
    lantz.drivers.legacy.stanford.sr830
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2015 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from collections import OrderedDict

import numpy as np
from lantz import Action, Feat, DictFeat, ureg
from lantz.drivers.legacy.serial import SerialDriver
from lantz.drivers.legacy.visa import GPIBVisaDriver

SENS = OrderedDict([
        ('2 nV/fA', 0),
        ('5 nV/fA', 1),
        ('10 nV/fA', 2),
        ('20 nV/fA', 3),
        ('50 nV/fA', 4),
        ('100 nV/fA', 5),
        ('200 nV/fA', 6),
        ('500 nV/fA', 7),
        ('1 uV/pA', 8),
        ('2 uV/pA', 9),
        ('5 uV/pA', 10),
        ('10 uV/pA', 11),
        ('20 uV/pA', 12),

        ('50 uV/pA', 13),
        ('100 uV/pA', 14),
        ('200 uV/pA', 15),
        ('500 uV/pA', 16),
        ('1 mV/nA', 17),
        ('2 mV/nA', 18),
        ('5 mV/nA', 19),
        ('10 mV/nA', 20),
        ('20 mV/nA', 21),
        ('50 mV/nA', 22),
        ('100 mV/nA', 23),
        ('200 mV/nA', 24),
        ('500 mV/nA', 25),
        ('1 V/uA', 26)
        ])

TCONSTANTS = OrderedDict([
    ('10 us', 0),
    ('30 us', 1),
    ('100 us', 2),
    ('300 us', 3),
    ('1 ms', 4),
    ('3 ms', 5),
    ('10 ms', 6),
    ('30 ms', 7),
    ('100 ms', 8),
    ('300 ms', 9),
    ('1 s', 10),
    ('3 s', 11),
    ('10 s', 12),
    ('30 s', 13),
    ('100 s', 14),
    ('300 s', 15),
    ('1 ks', 16),
    ('3 ks', 17),
    ('10 ks', 18),
    ('30 ks', 19),
])

SAMPLE_RATES = OrderedDict([
    ('62.5 mHz', 0),
    ('125 mHz', 1),
    ('250 mHz', 2),
    ('500 mHz', 3),
    ('1 Hz', 4),
    ('2 Hz', 5),
    ('4 Hz', 6),
    ('8 Hz', 7),
    ('16 Hz', 8),
    ('32 Hz', 9),
    ('64 Hz', 10),
    ('128 Hz', 11),
    ('256 Hz', 12),
    ('512 Hz', 13),
    ('trigger', 14)
])

class _SR830(object):

    @Feat(units='degrees', limits=(-360, 729.99, 0.01))
    def reference_phase_shift(self):
        """Phase shift of the reference.
        """
        return self.query('PHAS?')

    @reference_phase_shift.setter
    def reference_phase_shift(self, value):
        self.send('PHAS{:.2f}'.format(value))

    @Feat(values={True: 1, False: 0})
    def reference_internal(self):
        """Reference source.
        """
        return self.query('FMOD?')

    @reference_internal.setter
    def reference_internal(self, value):
        self.send('FMOD {}'.format(value))

    @Feat(units='Hz', limits=(0.001, 102000, 0.00001))
    def frequency(self):
        """Reference frequency.
        """
        return self.query('FREQ?')

    @frequency.setter
    def frequency(self, value):
        self.send('FREQ{:.5f}'.format(value))

    @Feat(values={'zero_crossing': 0, 'rising_edge': 1})
    def reference_trigger(self):
        """Reference trigger when using the external reference mode.
        """

    @reference_trigger.setter
    def reference_trigger(self, value):
        self.send('RSLP {}'.format(value))

    @Feat(limits=(1, 19999, 1))
    def harmonic(self):
        """Detection harmonic.
        """
        return self.query('HARM?')

    @harmonic.setter
    def harmonic(self, value):
        self.send('HARM {}'.format(value))

    @Feat(units='volt', limits=(0.004, 5., 0.002))
    def sine_output_amplitude(self):
        """Amplitude of the sine output.
        """
        return self.query('SLVL?')

    @sine_output_amplitude.setter
    def sine_output_amplitude(self, value):
        self.send('SLVL{:.2f}'.format(value))

    @Feat(values={'A': 0, 'A-B': 1, 'I1': 2, 'I100': 3})
    def input_configuration(self):
        """Configuration of the Input.
        """
        return self.query('ISRC?')

    @input_configuration.setter
    def input_configuration(self, value):
        self.send('ISRC {}'.format(value))

    @Feat(values={'float': 0, 'ground': 1})
    def input_shield(self):
        """Input shield grounding.
        """
        return self.query('IGND?')

    @input_shield.setter
    def input_shield(self, value):
        self.send('IGND {}'.format(value))

    @Feat(values={'AC': 0, 'DC': 1})
    def input_coupling(self):
        """Input coupling.
        """
        return self.query('ICPL?')

    @input_coupling.setter
    def input_coupling(self, value):
        self.send('ICPL {}'.format(value))

    @Feat(values={(False, False): 0, (True, False): 1, (False, True): 2, (True, True): 3})
    def input_filter(self):
        """Input line notch filters (1x, 2x).
        """
        return self.query('ILIN?')

    @input_filter.setter
    def input_filter(self, value):
        self.send('ILIN {}'.format(value))


    # GAIN and TIME CONSTANT COMMANDS.

    @Feat(values=SENS)
    def sensitivity(self):
        """Sensitivity.
        """
        return self.query('SENS?')

    @sensitivity.setter
    def sensitivity(self, value):
        self.send('SENS {}'.format(value))

    @Feat(values={'high': 0, 'normal': 1, 'low': 2})
    def reserve_mode(self):
        """Reserve mode.
        """
        return self.query('RMOD?')

    @reserve_mode.setter
    def reserve_mode(self, value):
        self.send('RMOD {}'.format(value))

    @Feat(values=TCONSTANTS)
    def time_constants(self):
        """Time constant.
        """
        return self.query('OFLT?')

    @time_constants.setter
    def time_constants(self, value):
        self.send('OFLT {}'.format(value))

    @Feat(values={6, 12, 18, 24})
    def filter_db_per_oct(self):
        """Time constant.
        """
        return self.query('OFSL?')

    @filter_db_per_oct.setter
    def filter_db_per_oct(self, value):
        self.send('OFSL {}'.format(value))

    @Feat(values={False: 0, True: 1})
    def sync_filter(self):
        """Synchronous filter status.
        """
        return self.query('SYNC?')

    @sync_filter.setter
    def sync_filter(self, value):
        self.send('SYNC {}'.format(value))


    ## DISPLAY and OUTPUT COMMANDS

    @DictFeat(keys={1, 2})
    def display(self, channel):
        """Front panel output source.
        """
        return self.query('DDEF? {}'.format(channel))

    @display.setter
    def display(self, channel, value):
        value, normalization = value
        self.send('DDEF {}, {}, {}'.format(channel, value, normalization))

    @DictFeat(keys={1, 2}, values={'display': 0, 'xy': 1})
    def front_output(self, channel):
        """Front panel output source.
        """
        return self.query('FPOP? {}'.format(channel))

    @front_output.setter
    def front_output(self, channel, value):
        self.send('FPOP {}, {}'.format(channel, value))

    # OEXP

    # AOFF is below.

    ## AUX INPUT and OUTPUT COMMANDS

    @DictFeat(keys={1, 2, 3, 4}, units='volt')
    def analog_input(self, key):
        """Input voltage in the auxiliary analog input.
        """
        self.query('AOUX? {}'.format(key))

    @DictFeat(None, keys={1, 2, 3, 4}, units='volt', limits=(-10.5, 10.5, 0.001))
    def analog_output(self, key):
        """Ouput voltage in the auxiliary analog output.
        """
        self.query('AUXV? {}'.format(key))

    @analog_output.setter
    def analog_output(self, key, value):
        self.query('AUXV {}, {}'.format(key, value))


    ## SETUP COMMANDS

    remote = Feat(None, values={True: 0, False: 1})

    @remote.setter
    def remote(self, value):
        """Lock Front panel.
        """
        self.query('OVRM {}'.format(value))

    @Feat(values={True: 1, False: 0})
    def key_click_enabled(self):
        """Key click
        """
        return self.query('KCLK?')

    @key_click_enabled.setter
    def key_click_enabled(self, value):
        self.send('KCLK {}'.format(value))

    @Feat(values={True: 1, False: 0})
    def alarm_enabled(self):
        """Key click
        """
        return self.query('ALRM?')

    @alarm_enabled.setter
    def alarm_enabled(self, value):
        self.send('ALRM {}'.format(value))

    @Action(limits=(1, 9))
    def recall_state(self, location):
        """Recalls instrument state in specified non-volatile location.

        :param location: non-volatile storage location.
        """
        self.send('RSET {}'.format(location))

    @Action()
    def save_state(self, location):
        """Saves instrument state in specified non-volatile location.

        Previously stored state in location is overwritten (no error is generated).
        :param location: non-volatile storage location.
        """
        self.send('SSET'.format(location))


    ## AUTO FUNCTIONS

    def wait_bit1(self):
        pass

    @Action()
    def auto_gain_async(self):
        """Equivalent to press the Auto Gain key in the front panel.
        Might take some time if the time constant is long.
        Does nothing if the constant is greater than 1 second.
        """
        self.send('AGAN')

    @Action()
    def auto_gain(self):
        self.auto_gain_async()
        self.wait_bit1()

    @Action()
    def auto_reserve_async(self):
        """Equivalent to press the Auto Reserve key in the front panel.
        Might take some time if the time constant is long.
        """
        self.send('ARSV')

    @Action()
    def auto_reserve(self):
        self.auto_reserve_async()
        self.wait_bit1()

    @Action()
    def auto_phase_async(self):
        """Equivalent to press the Auto Phase key in the front panel.
        Might take some time if the time constant is long.
        Does nothing if the phase is unstable.
        """
        self.send('ARSV')

    @Action()
    def auto_phase(self):
        self.auto_phase_async()
        self.wait_bit1()

    @Action(values={'x': 1, 'y': 2, 'r': 3})
    def auto_offset_async(self, channel_name):
        """Automatically offset a given channel to zero.
        Is equivalent to press the Auto Offset Key in the front panel.

        :param channel_name: the name of the channel.
        """
        self.send('AOFF {}'.format(channel_name))

    @Action()
    def auto_offset(self):
        self.auto_offset_async()
        self.wait_bit1()


    ## DATA STORAGE COMMANDS

    @Feat(values=SAMPLE_RATES)
    def sample_rate(self):
        """Sample rate.
        """
        return self.query('SRAT?')

    @sample_rate.setter
    def sample_rate(self, value):
        self.send('SRAT {}'.format(value))

    @Feat(values={True: 0, False: 1})
    def single_shot(self):
        """End of buffer mode.

        If loop mode (single_shot = False), make sure to pause data storage
        before reading the data to avoid confusion about which point is the
        most recent.
        """
        return self.query('SEND?')

    @single_shot.setter
    def single_shot(self, value):
        self.send('SEND {}'.format(value))

    @Action()
    def trigger(self):
        """Software trigger.
        """
        self.send('TRIG')

    @Feat()
    def trigger_start_mode(self):
        self.query('TSTR?')

    @trigger_start_mode.setter
    def trigger_start_mode(self, value):
        self.send('TSTR {}'.format(value))

    @Action()
    def start_data_storage(self):
        """Start or resume data storage
        """
        self.send('STRT')

    @Action()
    def pause_data_storage(self):
        """Pause data storage
        """
        self.send('PAUS')

    @Action()
    def reset_data_storage(self):
        """Reset data buffers. The command can be sent at any time -
        any storage in progress, paused or not. will be reset. The command
        will erase the data buffer.
        """
        self.send('REST')


    ## DATA TRANSFER COMMANDS

    @DictFeat(keys={'x', 'y', 'r', 't', 1, 2}, units='volt')
    def analog_value(self, key):
        if key in 'xyrt':
            return self.query('OUTP? {}'.format(key))
        else:
            return self.query('OUTR? {}'.format(key))

    @Action()
    def measure(self, channels):
        d = {'x': '1', 'y': '2', 'r': '3', 't': '4',
             '1': '5', '2': '6', '3': '7', '4': '8',
             'f': '9'} # '': 10, '': 11} TODO: How to deal with these?
        channels = ','.join(d[ch] for ch in channels)
        self.query('SNAP? {}'.format(channels))

    # OAUX See above

    @Feat()
    def buffer_length(self):
        return self.query('SPTS?')

    @Action()
    def read_buffer(self, channel, start=0, length=None, format='A'):
        """Queries points stored in the Channel buffer

        :param channel: Number of the channel (1, 2).
        :param start: Index of the buffer to start.
        :param length: Number of points to read.
                       Defaults to the number of points in the buffer.
        :param format: Transfer format
                      'a': ASCII (slow)
                      'b': IEEE Binary (fast) - NOT IMPLEMENTED
                      'c': Non-IEEE Binary (fastest) - NOT IMPLEMENTED
        """

        cmd = 'TRCA'
        if not length:
            length = self.buffer_length
        self.send('{}? {},{},{}'.format(cmd, channel, start, length))
        if cmd == 'TRCA':
            data = self.recv()
            return np.fromstring(data, sep=',') * ureg.volt
        else:
            raise ValueError('{} transfer format is not implemented'.format(format))

    # Fast
    # STRD

class SR830GPIB(_SR830, GPIBVisaDriver):

    RECV_TERMINATION = '\n'
    SEND_TERMINATION = '\n'


class SR830Serial(_SR830, SerialDriver):

    RECV_TERMINATION = '\n'
    SEND_TERMINATION = '\n'
