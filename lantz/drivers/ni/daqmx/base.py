# -*- coding: utf-8 -*-
"""
    lantz.drivers.ni.daqmx.base
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Implementation of base classes for Channels, Tasks and Devices


    :copyright: 2012 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from lantz import Feat, Action
from lantz.errors import InstrumentError
from lantz.foreign import LibraryDriver, RetValue, RetStr

from .constants import Constants, Types

default_buf_size = 2048

_SAMPLE_MODES = {'finite': Constants.Val_FiniteSamps,
                 'continuous': Constants.Val_ContSamps,
                 'hwtimed': Constants.Val_HWTimedSinglePoint}

_BUS_TYPES = {'PCI': Constants.Val_PCI, 'PCIe': Constants.Val_PCIe,
              'PXI': Constants.Val_PXI, 'SCXI': Constants.Val_SCXI,
              'PCCard': Constants.Val_PCCard, 'USB': Constants.Val_USB,
              'UNKNOWN': Constants.Val_Unknown}

_SIGNAL_TYPES = {'sample_clock': Constants.Val_SampleClock,
                 'sample_complete': Constants.Val_SampleCompleteEvent,
                 'change_direction': Constants.Val_ChangeDetectionEvent,
                 'counter_output': Constants.Val_CounterOutputEvent}

_EDGE_TYPES = {'rising': Constants.Val_Rising, 'falling': Constants.Val_Falling}

_SLOPE_TYPES = {'rising': Constants.Val_RisingSlope, 'falling': Constants.Val_FallingSlope}

_WHEN_WINDOW = {'entering': Constants.Val_EnteringWin, 'leaving': Constants.Val_LeavingWin}

_WHEN_TRIGGER_DIG = {'high': Constants.Val_High, 'low': Constants.Val_Low}

_WHEN_TRIGGER_ALVL = {'above': Constants.Val_AboveLvl, 'below': Constants.Val_BelowLvl}

_WHEN_TRIGGER_AWIN = {'inside': Constants.Val_InsideWin, 'outside': Constants.Val_OutsideWin}

_WHEN_MATCH = {True: Constants.Val_PatternMatches, False: Constants.Val_PatternDoesNotMatch}

_TRIGGER_TYPES = {'digital_level': Constants.Val_DigLvl,
                  'analog_level': Constants.Val_AnlgLvl,
                  'analog_window': Constants.Val_AnlgWin}

_CHANNEL_TYPES = {'AI': Constants.Val_AI, 'AO': Constants.Val_AO,
                  'DI': Constants.Val_DI, 'DO': Constants.Val_DO,
                  'CI': Constants.Val_CI, 'CO': Constants.Val_CO}

class _Base(LibraryDriver):
    """Base class for NIDAQmx
    """

    LIBRARY_NAME = 'nicaiu', 'nidaqmx'
    LIBRARY_PREFIX = 'DAQmx'

    _DEVICES = {}
    _TASKS = {}
    _CHANNELS = {}

    def _get_error_string(self, error_code):
        size = self.lib.GetErrorString(error_code, None, 0)
        if size <= 0:
            raise InstrumentError('Could not retrieve error string.')
        err, msg = self.lib.GetErrorString(error_code, *RetStr(size))
        if err < 0:
            raise InstrumentError('Could not retrieve error string.')
        return msg

    def _get_error_extended_error_info(self):
        size = self.lib.GetExtendedErrorInfo(None, 0)
        if size <= 0:
            raise InstrumentError('Could not retrieve extended error info.')
        err, msg = self.lib.GetExtendedErrorInfo(*RetStr(size))
        if err < 0:
            raise InstrumentError('Could not retrieve extended error info.')
        return msg

    def _return_handler(self, func_name, ret_value):
        if ret_value < 0 and func_name not in ('GetErrorString', 'GetExtendedErrorInfo'):
            msg = self._get_error_string(ret_value)
            raise InstrumentError(msg)
        return ret_value

    def __get_fun(self, name):
        return getattr(self.lib, name.format(self.operation_direction.title()))

    def _add_types(self):

        super()._add_types()
        T = Types
        self.lib.CreateAIVoltageChan.argtypes = [T.TaskHandle, T.string, T.string, T.int32, T.float64, T.float64, T.int32, T.string]
        self.lib.ReadAnalogScalarF64.argtypes = [T.TaskHandle, T.float64, T._, T._]

class _ObjectDict(object):

    def __init__(self, key_fun, obj_creator, dictionary=None):
        self.key_fun = key_fun
        self.obj_creator = obj_creator
        self._internal = {} if dictionary is None else dictionary

    def __getitem__(self, item):

        if item in self._internal:
            return self._internal[item]

        if item not in self:
            raise KeyError('{} not found'.format(item))

        value = self.obj_creator(item)

        self._internal[item] = value

        return value

    def __len__(self):
        return sum((1 for key in self.keys()))

    def __contains__(self, item):
        return item in self.key_fun()

    def keys(self):
        for key in self.key_fun():
            yield key

    def values(self):
        for key in self.keys():
            yield self[key]

    def items(self):
        for key in self.keys():
            yield key, self[key]


class System(_Base):
    """NI-DAQmx System
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.devices = _ObjectDict(self._device_names, Device, self._DEVICES)
        self.tasks = _ObjectDict(self._task_names, Task, self._TASKS)
        self.channels = _ObjectDict(self._channel_names, Channel, self._CHANNELS)

    @Feat(read_once=True)
    def version(self):
        """Version of installed NI-DAQ library. 
        """
        err, major  = self.lib.GetSysNIDAQMajorVersion(RetValue('u32'))
        err, minor  = self.lib.GetSysNIDAQMinorVersion(RetValue('u32'))
        return major, minor

    def _device_names(self):
        """Return a tuple containing the names of all global devices installed in the system.
        """
        err, buf = self.lib.GetSysDevNames(*RetStr(default_buf_size))
        names = tuple(n.strip() for n in buf.split(',') if n.strip())
        return names

    def _task_names(self):
        """Return a tuple containing the names of all global tasks saved in the system.
        """
        err, buf = self.lib.GetSysTasks(*RetStr(default_buf_size))
        names = tuple(n.strip() for n in buf.split(',') if n.strip())
        return names

    def _channel_names(self):
        """Return a tuple containing the names of all global channels saved in the system.
        """
        err, buf = self.lib.GetSysGlobalChans(*RetStr(default_buf_size))
        names = tuple(n.strip() for n in buf.split(',') if n.strip())
        return names


class Device(_Base):
    """Device
    """

    def __init__(self, device_name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.device_name = device_name

    def _preprocess_args(self, name, *args):
        """Injects device_name to all call to the library
        """
        if name in ('GetErrorString', 'GetExtendedErrorInfo'):
            return super()._preprocess_args(name, *args)
        else:
            return super()._preprocess_args(name, *((self.device_name, ) + args))

    @Feat(read_once=True)
    def is_simulated(self):
        """Return True if it is a simulated device
        """
        err, value = self.lib.GetDevIsSimulated(RetValue('u32'))
        return value != 0

    @Feat(read_once=True)
    def product_type(self):
        """Return the product name of the device.
        """
        err, buf = self.lib.GetDevProductType(*RetStr(default_buf_size))
        return buf

    @Feat(read_once=True)
    def product_number(self):
        """Return the unique hardware identification number for the device.
        """
        err, value = self.lib.GetDevProductNum(RetValue('u32'))
        return value

    @Feat(read_once=True)
    def serial_number (self):
        """Return the serial number of the device. This value is zero
        if the device does not have a serial number.
        """
        err, value = self.lib.GetDevSerialNum(RetValue('u32'))
        return value

    @Feat(read_once=True)
    def analog_input_channels(self):
        """Return a tuple with the names of the analog input
        physical channels available on the device.
        """

        err, buf = self.lib.GetDevAIPhysicalChans(*RetStr(default_buf_size))
        names = tuple(n.strip() for n in buf.split(',') if n.strip())
        return names

    @Feat(read_once=True)
    def analog_output_channels(self):
        """Return a tuple with the names of the analog output
        physical channels available on the device.
        """
        err, buf = self.lib.GetDevAOPhysicalChans(*RetStr(default_buf_size))
        names = tuple(n.strip() for n in buf.split(',') if n.strip())
        return names

    @Feat(read_once=True)
    def digital_input_lines(self):
        """Return a tuple with the names of the digital input lines
        physical channels available on the device.
        """
        err, buf = self.lib.GetDevDILines(*RetStr(default_buf_size))
        names = tuple(n.strip() for n in buf.split(',') if n.strip())
        return names

    @Feat(read_once=True)
    def digital_output_lines(self):
        """Return a tuple with the names of the digital lines
        ports available on the device.
        """
        err, buf = self.lib.GetDevDOLines(*RetStr(default_buf_size))
        names = tuple(n.strip() for n in buf.split(',') if n.strip())
        return names

    @Feat(read_once=True)
    def digital_input_ports(self):
        """Return a tuple with the names of the digital input
        ports available on the device.
        """
        err, buf = self.lib.GetDevDIPorts(*RetStr(default_buf_size))
        names = tuple(n.strip() for n in buf.split(',') if n.strip())
        return names

    @Feat(read_once=True)
    def digital_output_ports(self):
        """Return a tuple with the names of the digital output
        ports available on the device.
        """
        err, buf = self.lib.GetDevDOPorts(*RetStr(default_buf_size))
        names = tuple(n.strip() for n in buf.split(',') if n.strip())
        return names

    @Feat(read_once=True)
    def counter_input_channels(self):
        """Return a tuple with the names of the counter input
        physical channels available on the device.
        """
        err, buf = self.lib.GetDevCIPhysicalChans(*RetStr(default_buf_size))
        names = tuple(n.strip() for n in buf.split(',') if n.strip())
        return names

    @Feat(read_once=True)
    def counter_output_channels(self):
        """Return a tuple with the names of the counter input
        physical channels available on the device.
        """
        err, buf = self.lib.GetDevCOPhysicalChans(*RetStr(default_buf_size))
        names = tuple(n.strip() for n in buf.split(',') if n.strip())
        return names

    @Feat(read_once=True, values=_BUS_TYPES)
    def bus_type(self):
        """Return the bus type of the device.
        """
        err, value = self.lib.GetDevBusType(RetValue('i32'))
        return value

    @Feat(read_once=True)
    def pci_bus_number (self):
        """Return the PCI bus number of the device.
        """
        err, value = self.lib.GetDevPCIBusNum(RetValue('i32'))
        return value

    @Feat(read_once=True)
    def pci_device_number (self):
        """Return the PCI slot number of the device.
        """
        err, value = self.lib.GetDevPCIDevNum(RetValue('i32'))
        return value

    @Feat(read_once=True)
    def pxi_slot_number(self):
        """Return the PXI slot number of the device.
        """
        err, value = self.lib.GetDevPXISlotNum(RetValue('u32'))
        return value

    @Feat(read_once=True)
    def pxi_chassis_number(self):
        """Return the PXI chassis number of the device, as identified
        in MAX.
        """
        err, value = self.lib.GetDevPXIChassisNum(RetValue('u32'))
        return value

    @Feat(read_once=True)
    def bus_info(self):
        t = self.bus_type
        if t in ('PCI', 'PCIe'):
            return '%s (bus=%s, device=%s)' % (t, self.pci_bus_number, self.pci_device_number)
        if t == 'PXI':
            return '%s (chassis=%s, slot=%s)' % (t, self.pxi_chassis_number, self.pxi_slot_number)
        return t

    @Action()
    def reset(self):
        """Stops and deletes all tasks on a device and rests outputs to their defaults
        """
        return self.lib.ResetDevice()


class Task(_Base):
    """A task is a collection of one or more virtual channels with timing,
    triggering, and other properties. Conceptually, a task represents a
    measurement or generation you want to perform. All channels in a task
    must be of the same I/O type, such as analog input or counter output.

    However, a task can include channels of different measurement types,
    such as an analog input temperature channel and an analog input voltage
    channel. For most devices, only one task per subsystem can run at once,
    but some devices can run multiple tasks simultaneously. With some devices,
    you can include channels from multiple devices in a task.

    :param name: Name assigned to the task (This can be changed by the
                 library. The final name will be stored in name attribute)

    """

    _REGISTRY = {}

    @classmethod
    def register_class(cls, klass):
        cls._REGISTRY[klass.IO_TYPE] = klass

    @classmethod
    def typed_task(cls, io_type):
        return cls._REGISTRY[io_type]

    def _load_task(self, name):
        err, self.__task_handle = self.lib.LoadTask(name, RetValue('u32'))
        self.name = name
        self.log_debug('Loaded task with {} ({})'.format(self.name, self.__task_handle))

    def _create_task(self, name):
        err, self.__task_handle = self.lib.CreateTask(name, RetValue('u32'))
        err, self.name = self.lib.GetTaskName(*RetStr(default_buf_size))
        self.log_debug('Created task with {} ({})'.format(self.name, self.__task_handle))

    def __init__(self, name='', *args, **kwargs):
        super().__init__(name, *args, **kwargs)
        if not name:
            self._create_task(name)
        else:
            try:
                self._load_task(name)
            except Exception as e:
                self._create_task(name)

        self.sample_mode = None
        self.channels = _ObjectDict(self._channel_names, self._create_channel_from_name, self._CHANNELS)
        self.devices = _ObjectDict(self._device_names, Device, self._DEVICES)

    @property
    def task_handle(self):
        return self.__task_handle

    def _preprocess_args(self, name, *args):
        """Injects device_name to all call to the library
        """
        if name in ('GetErrorString', 'GetExtendedErrorInfo', 'LoadTask', 'CreateTask'):
            return super()._preprocess_args(name, *args)
        else:
            return super()._preprocess_args(name, *((self.task_handle, ) + args))

    def _create_channel_from_name(self, name):
        return Channel(self, name=name)

    def _channel_names(self):
        """Return a tuple with the names of all virtual channels in the task.
        """
        err, buf = self.lib.GetTaskChannels(*RetStr(default_buf_size))
        names = tuple(n.strip() for n in buf.split(',') if n.strip())
        return names

    def _device_names(self):
        """Return a tuple with the names of all devices in the task.
        """
        err, buf = self.lib.GetTaskDevices(*RetStr(default_buf_size))
        names = tuple(n.strip() for n in buf.split(',') if n.strip())
        return names

    @Feat()
    def io_type(self):
        for name, channel in self.channels.items():
            return channel.io_type
        else:
            return None

    def add_channel(self, channel):
        if not isinstance(channel, Channel):
            raise TypeError('Only channels may be added to a task.')

        if channel.task is self.channels:
            return
        elif channel.task is None:
            channel.task = self
        else:
            raise ValueError('Cannot add a channel that is already in another task')

    def execute_fun(self, func_name, *args):
        return getattr(self.lib, func_name)(*args)

    def clear(self):
        """Clear the task.

        Before clearing, this function stops the task, if necessary,
        and releases any resources reserved by the task. You cannot
        use a task once you clear the task without recreating or
        reloading the task.

        If you use the DAQmxCreateTask function or any of the NI-DAQmx
        Create Channel functions within a loop, use this function
        within the loop after you finish with the task to avoid
        allocating unnecessary memory.
        """
        if self.task_handle:
            self.lib.ClearTask()
            self.__task_handle = None

    __del__ = clear

    @Feat()
    def is_done(self):
        """Queries the status of the task and indicates if it completed
        execution. Use this function to ensure that the specified
        operation is complete before you stop the task.
        """
        err, value = self.lib.IsTaskDone(RetValue('u32'))
        return value != 0

    # States

    @Action()
    def start(self):
        """Start the task

        Transitions the task from the committed state to the running
        state, which begins measurement or generation. Using this
        function is required for some applications and optional for
        others.

        If you do not use this function, a measurement task starts
        automatically when a read operation begins. The autoStart
        parameter of the NI-DAQmx Write functions determines if a
        generation task starts automatically when you use an NI-DAQmx
        Write function.

        If you do not call StartTask and StopTask when you
        call NI-DAQmx Read functions or NI-DAQmx Write functions
        multiple times, such as in a loop, the task starts and stops
        repeatedly. Starting and stopping a task repeatedly reduces
        the performance of the application.
        """

        self.lib.StartTask()

    @Action()
    def stop(self):
        """Stop the task.

        Stop the task and returns it to the state it was in before
        you called StartTask or called an NI-DAQmx Write function with
        autoStart set to TRUE.

        If you do not call StartTask and StopTask when you call
        NI-DAQmx Read functions or NI-DAQmx Write functions multiple
        times, such as in a loop, the task starts and stops
        repeatedly. Starting and stopping a task repeatedly reduces
        the performance of the application.

        """
        self.lib.StopTask()

    @Action()
    def verify(self):
        """Verifies that all task parameters are valid for the hardware.
        """
        self.alter_state('verify')

    @Action()
    def commit(self):
        """Programs the hardware as much as possible according
        to the task configuration.
        """
        self.alter_state('commit')

    @Action()
    def reserve(self):
        """Reserves the hardware resources needed for the
        task. No other tasks can reserve these same resources.
        """
        self.alter_state('reserve')

    @Action()
    def unreserve(self):
        """Release all reserved resources.
        """
        self.alter_state('unreserve')

    @Action()
    def abort(self):
        """Abort an operation, such as Read or Write, that is currently active.

        The task is put into an unstable but recoverable state. To recover the
        task, call Start to restart the task or call Stop to reset the task
        without starting it.
        """
        self.alter_state('abort')

    @Action(values={'start': Constants.Val_Task_Start, 'stop': Constants.Val_Task_Stop,
                    'verify': Constants.Val_Task_Verify, 'commit': Constants.Val_Task_Commit,
                    'reserve': Constants.Val_Task_Reserve, 'unreserve': Constants.Val_Task_Unreserve,
                    'abort': Constants.Val_Task_Abort})
    def alter_state(self, new_state):
        """Alters the state of a task according to the action you
        specify. To minimize the time required to start a task, for
        example, DAQmxTaskControl can commit the task prior to
        starting.

        :param new_state:
        """
        self.lib.TaskControl(new_state)

    _register_every_n_samples_event_cache = None

    def register_every_n_samples_event(self, func, samples=1, options=0, cb_data=None):
        """Register a callback function to receive an event when the
        specified number of samples is written from the device to the
        buffer or from the buffer to the device. This function only
        works with devices that support buffered tasks.

        When you stop a task explicitly any pending events are
        discarded. For example, if you call DAQmxStopTask then you do
        not receive any pending events.

        :param func: The function that you want DAQmx to call when the event
          occurs. The function you pass in this parameter must have
          the following prototype::

            def func(task, event_type, samples, cb_data):
                ...
                return 0

          Upon entry to the callback, the task parameter contains the
          handle to the task on which the event occurred. The
          event_type parameter contains the value you passed in the
          event_type parameter of this function. The samples parameter
          contains the value you passed in the samples parameter of
          this function. The cb_data parameter contains the value you
          passed in the cb_data parameter of this function.

        :param samples: The number of samples after which each event should occur.

        :param options:

        :param cb_data:

        See also: register_signal_event, register_done_event
        """

        if self.operation_direction == 'input':
            event_type = Constants.Val_Acquired_Into_Buffer
        else:
            event_type = Constants.Val_Transferred_From_Buffer

        if options == 'sync':
            options = Constants.Val_SynchronousEventCallbacks

        if func is None:
            c_func = None # to unregister func
        else:
            if self._register_every_n_samples_event_cache is not None:
                # unregister:
                self.register_every_n_samples_event(None, samples=samples, options=options, cb_data=cb_data)
                # TODO: check the validity of func signature
            # TODO: use wrapper function that converts cb_data argument to given Python object
            c_func = EveryNSamplesEventCallback_map[self.CHANNEL_TYPE](func)

        self._register_every_n_samples_event_cache = c_func

        self.lib.RegisterEveryNSamplesEvent(event_type, uInt32(samples), uInt32(options), c_func, cb_data)

    _register_done_event_cache = None

    def register_done_event(self, func, options=0, cb_data=None):
        """Register a callback function to receive an event when a task
        stops due to an error or when a finite acquisition task or
        finite generation task completes execution. A Done event does
        not occur when a task is stopped explicitly, such as by
        calling DAQmxStopTask.


        :param func:

          The function that you want DAQmx to call when the event
          occurs.  The function you pass in this parameter must have
          the following prototype::

            def func(task, status, cb_data = None):
                ...
                return 0

          Upon entry to the callback, the taskHandle parameter
          contains the handle to the task on which the event
          occurred. The status parameter contains the status of the
          task when the event occurred. If the status value is
          negative, it indicates an error. If the status value is
          zero, it indicates no error. If the status value is
          positive, it indicates a warning. The callbackData parameter
          contains the value you passed in the callbackData parameter
          of this function.

        :param options : {int, 'sync'}

          Use this parameter to set certain options. You can
          combine flags with the bitwise-OR operator ('|') to set
          multiple options. Pass a value of zero if no options need to
          be set.

          'sync' - The callback function is called in the thread which
          registered the event. In order for the callback to occur,
          you must be processing messages. If you do not set this
          flag, the callback function is called in a DAQmx thread by
          default.

          Note: If you are receiving synchronous events faster than
          you are processing them, then the user interface of your
          application might become unresponsive.

        :param cb_data:

          A value that you want DAQmx to pass to the callback function
          as the function data parameter. Do not pass the address of a
          local variable or any other variable that might not be valid
          when the function is executed.

        See also

        register_signal_event, register_every_n_samples_event
        """
        if options=='sync':
            options = Constants.Val_SynchronousEventCallbacks

        if func is None:
            c_func = None
        else:
            if self._register_done_event_cache is not None:
                self.register_done_event(None, options=options, cb_data=cb_data)
                # TODO: check the validity of func signature
            c_func = DoneEventCallback_map[self.CHANNEL_TYPE](func)
        self._register_done_event_cache = c_func

        self.lib.RegisterDoneEvent(uInt32(options), c_func, cb_data)

    def operation_direction(self):
        return 'input' if self.CHANNEL_TYPE else 'output'

    _register_signal_event_cache = None

    @Action(values=(None, _SIGNAL_TYPES, None, None))
    def register_signal_event(self, func, signal, options=0, cb_data=None):
        """Registers a callback function to receive an event when the
        specified hardware event occurs.

        When you stop a task explicitly any pending events are
        discarded. For example, if you call DAQmxStopTask then you do
        not receive any pending events.

        :param func:

          The function that you want DAQmx to call when the event
          occurs. The function you pass in this parameter must have the
          following prototype::

            def func(task, signalID, cb_data):
              ...
              return 0

          Upon entry to the callback, the task parameter contains the
          handle to the task on which the event occurred. The signalID
          parameter contains the value you passed in the signal
          parameter of this function. The cb_data parameter contains
          the value you passed in the cb_data parameter of this
          function.

        :param signal: {'sample_clock', 'sample_complete', 'change_detection', 'counter_output'}

          The signal for which you want to receive results:

          'sample_clock' - Sample clock
          'sample_complete' - Sample complete event
          'change_detection' - Change detection event
          'counter_output' - Counter output event

        :param options:

        :param cb_data:

        See also: register_done_event, register_every_n_samples_event
        """

        if options == 'sync':
            options = Constants.Val_SynchronousEventCallbacks

        if func is None:
            c_func = None
        else:
            if self._register_signal_event_cache is not None:
                self._register_signal_event(None, signal=signal, options=options, cb_data=cb_data)
                # TODO: check the validity of func signature
            c_func = SignalEventCallback_map[self.CHANNEL_TYPE](func)
        self._register_signal_event_cache = c_func
        self.lib.RegisterSignalEvent(signal, uInt32(options), c_func, cb_data)


    @Action(values=(str, str, _SAMPLE_MODES, None))
    def configure_timing_change_detection(self, rising_edge_channel='', falling_edge_channel='',
                                          sample_mode='continuous', samples_per_channel=1000):
        """Configures the task to acquire samples on the rising and/or
        falling edges of the lines or ports you specify.
        """

        self.lib.CfgChangeDetectionTiming(rising_edge_channel, falling_edge_channel,
                                          sample_mode, samples_per_channel)


    @Action(values=(_SAMPLE_MODES, None))
    def configure_timing_handshaking(self, sample_mode='continuous', samples_per_channel=1000):
        """Determines the number of digital samples to acquire or
        generate using digital handshaking between the device and a
        peripheral device.
        """
        self.samples_per_channel = samples_per_channel
        self.sample_mode = sample_mode
        self.lib.CfgHandshakingTiming(sample_mode, samples_per_channel)

    @Action(values=(_SAMPLE_MODES, None))
    def configure_timing_implicit(self, sample_mode='continuous', samples_per_channel=1000):
        """Sets only the number of samples to acquire or generate without
        specifying timing. Typically, you should use this function
        when the task does not require sample timing, such as tasks
        that use counters for buffered frequency measurement, buffered
        period measurement, or pulse train generation.
        """
        self.samples_per_channel = samples_per_channel
        self.sample_mode = sample_mode
        self.lib.CfgImplicitTiming(self, sample_mode, samples_per_channel)

    @Action(values=(str, None, _EDGE_TYPES, _SAMPLE_MODES, None))
    def configure_timing_sample_clock(self, source='on_board_clock', rate=1, active_edge='rising',
                                      sample_mode='continuous', samples_per_channel=1000):
        """Set the source of the Sample Clock, the rate of the Sample
        Clock, and the number of samples to acquire or generate.

        :param source:

            The source terminal of the Sample Clock. To use the
            internal clock of the device, use None or use
            'OnboardClock'.

        :param rate:

            The sampling rate in samples per second. If you use an
            external source for the Sample Clock, set this value to
            the maximum expected rate of that clock.

        :param active_edge:

            Specifies on which edge of the clock to
            acquire or generate samples:

              'rising' - Acquire or generate samples on the rising edges
              of the Sample Clock.

              'falling' - Acquire or generate samples on the falling
              edges of the Sample Clock.

        :param sample_mode: {'finite', 'continuous', 'hwtimed'}

            Specifies whether the task acquires or
            generates samples continuously or if it acquires or
            generates a finite number of samples:

              'finite' - Acquire or generate a finite number of samples.

              'continuous' - Acquire or generate samples until you stop the task.

              'hwtimed' - Acquire or generate samples continuously
              using hardware timing without a buffer. Hardware timed
              single point sample mode is supported only for the
              sample clock and change detection timing types.

        :param samples_per_channel:

            The number of samples to acquire or generate for each
            channel in the task if `sample_mode` is 'finite'.  If
            sample_mode is 'continuous', NI-DAQmx uses this value to
            determine the buffer size.
        """
        if source == 'on_board_clock':
            source = None
        self.samples_per_channel = samples_per_channel
        self.sample_mode = sample_mode
        self.lib.CfgSampClkTiming(source, float64(rate), active_edge, sample_mode, samples_per_channel)

    def configure_timing_burst_handshaking_export_clock(self, *args, **kws):
        """
        Configures when the DAQ device transfers data to a peripheral
        device, using the DAQ device's onboard sample clock to control
        burst handshaking timing.
        """
        raise NotImplementedError

    def configure_timing_burst_handshaking_import_clock(self, *args, **kws):
        """
        Configures when the DAQ device transfers data to a peripheral
        device, using an imported sample clock to control burst
        handshaking timing.
        """
        raise NotImplementedError

    @Action(values=(str, _SLOPE_TYPES, None))
    def configure_trigger_analog_edge_start(self, source, slope='rising', level=1.0):
        """
        Configures the task to start acquiring or generating samples
        when an analog signal crosses the level you specify.

        :param source:

          The name of a channel or terminal where there is an analog
          signal to use as the source of the trigger. For E Series
          devices, if you use a channel name, the channel must be the
          first channel in the task. The only terminal you can use for
          E Series devices is PFI0.

        :param slope:

          Specifies on which slope of the signal to start acquiring or
          generating samples when the signal crosses trigger level:

            'rising' - Trigger on the rising slope of the signal.

            'falling' - Trigger on the falling slope of the signal.

        :param level:

          The threshold at which to start acquiring or generating
          samples. Specify this value in the units of the measurement
          or generation. Use trigger slope to specify on which slope
          to trigger at this threshold.
        """

        self.lib.CfgAnlgEdgeStartTrig(source, slope, level)

    @Action(values=(str, _WHEN_WINDOW, None, None))
    def configure_trigger_analog_window_start(self, source, when='entering', top=1.0, bottom=-1.0):
        """Configure the task to start acquiring or generating samples
        when an analog signal enters or leaves a range you specify.

        :param source:

          The name of a virtual channel or terminal where there
          is an analog signal to use as the source of the trigger.

          For E Series devices, if you use a virtual channel, it must
          be the first channel in the task. The only terminal you can
          use for E Series devices is PFI0.

        :param when : {'entering', 'leaving'}

          Specifies whether the task starts measuring or generating
          samples when the signal enters the window or when it leaves
          the window. Use `bottom` and `top` to specify the limits of
          the window.

        :param top : float

          The upper limit of the window. Specify this value in the
          units of the measurement or generation.

        :param bottom : float

          The lower limit of the window. Specify this value in the
          units of the measurement or generation.
        """
        self.lib.CfgAnlgWindowStartTrig(self, source, when, top, bottom)

    @Action(values=(str, _EDGE_TYPES))
    def configure_trigger_digital_edge_start(self, source, edge='rising'):
        """Configure the task to start acquiring or generating samples
        on a rising or falling edge of a digital signal.

        :param source:

          The name of a terminal where there is a digital signal to
          use as the source of the trigger.

        :param edge: {'rising', 'falling'}

          Specifies on which edge of a digital signal to start
          acquiring or generating samples: rising or falling edge(s).
        """

        self.lib.CfgDigEdgeStartTrig(self, source, edge)

    @Action(values=(str, str, _WHEN_MATCH))
    def configure_trigger_digital_pattern_start(self, source, pattern, match=True):
        """Configure a task to start acquiring or generating samples
        when a digital pattern is matched.

        :param source:

          Specifies the physical channels to use for pattern
          matching. The order of the physical channels determines the
          order of the pattern. If a port is included, the order of
          the physical channels within the port is in ascending order.

        :param pattern:

          Specifies the digital pattern that must be met for the
          trigger to occur.

        :param when: {'matches', 'does_not_match'}

          Specifies the conditions under which the trigger
          occurs: pattern matches or not.
        """
        self.lib.CfgDigPatternStartTrig(self, source, pattern, match)

    def configure_trigger_disable_start(self):
        """
        Configures the task to start acquiring or generating samples
        immediately upon starting the task.

        Returns
        -------

          success_status : bool
        """
        self.lib.DisableStartTrig()

    @Action(values=(str, _SLOPE_TYPES, None, None))
    def configure_analog_edge_reference_trigger(self, source, slope='rising',level=1.0, pre_trigger_samps=0):
        """Configure the task to stop the acquisition when the device
        acquires all pretrigger samples, an analog signal reaches the
        level you specify, and the device acquires all post-trigger samples.

        :param source:

          The name of a channel or terminal where there is an analog
          signal to use as the source of the trigger. For E Series
          devices, if you use a channel name, the channel must be the
          first channel in the task. The only terminal you can use for
          E Series devices is PFI0.

        :param slope:

          Specifies on which slope of the signal to start acquiring or
          generating samples when the signal crosses trigger level:

            'rising' - Trigger on the rising slope of the signal.

            'falling' - Trigger on the falling slope of the signal.

        :param level:
          The threshold at which to start acquiring or generating
          samples. Specify this value in the units of the measurement
          or generation. Use trigger slope to specify on which slope
          to trigger at this threshold.

        :param pre_trigger_samps:

          The minimum number of samples per channel to acquire before
          recognizing the Reference Trigger. The number of posttrigger
          samples per channel is equal to number of samples per channel
          in the NI-DAQmx Timing functions minus pretriggerSamples.
        """

        self.lib.CfgAnlgEdgeRefTrig(source, slope, level, pre_trigger_samps)


    @Feat(values=(str, _WHEN_WINDOW, None, None, None))
    def configure_analog_window_reference_trigger(self, source, when='entering',top=1.0, bottom=1.0, pre_trigger_samps=0):
        """Configure the task to stop the acquisition when the device
        acquires all pretrigger samples, an analog signal enters or
        leaves a range you specify, and the device acquires all
        post-trigger samples.


        :param source : str

          The name of a channel or terminal where there is an analog
          signal to use as the source of the trigger. For E Series
          devices, if you use a channel name, the channel must be the
          first channel in the task. The only terminal you can use for
          E Series devices is PFI0.

        :param when : {'entering', 'leaving'}

          Specifies whether the Reference Trigger occurs when the signal
          enters the window or when it leaves the window. Use
          bottom and top to specify the limits of the window.

            'entering' - Trigger when the signal enters the window.

            'leaving' - Trigger when the signal leaves the window.

        :param top : float

          The upper limit of the window. Specify this value in the
          units of the measurement or generation.

        :param bottom : float

          The lower limit of the window. Specify this value in the
          units of the measurement or generation.

        :param pre_trigger_samps : uint32

          The minimum number of samples per channel to acquire before
          recognizing the Reference Trigger. The number of posttrigger
          samples per channel is equal to number of samples per channel
          in the NI-DAQmx Timing functions minus pretriggerSamples.
        """

        self.lib.CfgAnlgWindowRefTrig(source, when, top, bottom, pre_trigger_samps)

    @Action(values=(str, _SLOPE_TYPES, None))
    def configure_digital_edge_reference_trigger(self, source, slope='rising', pre_trigger_samps=0):
        """Configures the task to stop the acquisition when the device
        acquires all pretrigger samples, detects a rising or falling
        edge of a digital signal, and acquires all posttrigger samples.

        :param source:

          The name of a channel or terminal where there is an analog
          signal to use as the source of the trigger. For E Series
          devices, if you use a channel name, the channel must be the
          first channel in the task. The only terminal you can use for
          E Series devices is PFI0.

        :param slope:

          Specifies on which slope of the signal to start acquiring or
          generating samples when the signal crosses trigger level:

            'rising' - Trigger on the rising slope of the signal.

            'falling' - Trigger on the falling slope of the signal.

        :param pre_trigger_samps:

          The minimum number of samples per channel to acquire before
          recognizing the Reference Trigger. The number of posttrigger
          samples per channel is equal to number of samples per channel
          in the NI-DAQmx Timing functions minus pretriggerSamples.
        """
        if not source.startswith('/'): # source needs to start with a '/' TODO WHY?
            source = '/'  + source
        self.lib.CfgDigEdgeRefTrig(source, slope, pre_trigger_samps)


    @Action(values=(str, str, _WHEN_MATCH, None))
    def configure_digital_pattern_reference_trigger(self, source, pattern, match=True, pre_trigger_samps=0):
        """Configure the task to stop the acquisition when the device
        acquires all pretrigger samples, matches or does not match
        a digital pattern, and acquires all posttrigger samples.

        :param source:

          The name of a channel or terminal where there is an analog
          signal to use as the source of the trigger. For E Series
          devices, if you use a channel name, the channel must be the
          first channel in the task. The only terminal you can use for
          E Series devices is PFI0.

        :param pattern:

          Specifies the digital pattern that must be met for the trigger to occur.

        :param match: Specifies if the conditions under which the trigger occurs

            'match' - Trigger when the signal matches the pattern

            'nomatch' - Trigger when the signal does NOT match the pattern

        :param pre_trigger_samps : uint32

          The minimum number of samples per channel to acquire before
          recognizing the Reference Trigger. The number of posttrigger
          samples per channel is equal to number of samples per channel
          in the NI-DAQmx Timing functions minus pretriggerSamples.
        """

        if not source.startswith('/'): # source needs to start with a '/'
            source = '/' + source

        self.lib.CfgDigPatternRefTrig(self, source, pattern, match, pre_trigger_samps)

    @Action()
    def disable_reference_trigger(self):
        """
        Disables reference triggering for the measurement or generation.

        Returns
        -------

          success_status : bool
        """
        return self.lib.DisableRefTrig(self) == 0


    #TODO CHECK
    def set_buffer(self, samples_per_channel):
        """
        Overrides the automatic I/O buffer allocation that NI-DAQmx performs.

        Parameters
        ----------

        samples_per_channel : int

          The number of samples the buffer can hold for each channel
          in the task. Zero indicates no buffer should be
          allocated. Use a buffer size of 0 to perform a
          hardware-timed operation without using a buffer.

        Returns
        -------

          success_status : bool
        """
        #channel_io_type = self.channel_io_type
        #return CALL('Cfg%sBuffer' % (channel_io_type.title()), self, uInt32(samples_per_channel)) == 0
        pass

    @Feat(units='Hz')
    def sample_clock_rate(self):
        """Sample clock rate.

        Set to None to reset.
        """

        err, value = self.lib.GetSampClkRate(self, RetValue('f64'))
        return value

    @sample_clock_rate.setter
    def sample_clock_rate(self, value):
        if value is None:
            self.lib.ResetSampClkRate()
        else:
            return self.lib.SetSampClkRate(value)

    @Feat()
    def convert_clock_rate(self):
        """Convert clock rate.

        The rate at which to clock the analog-to-digital
        converter. This clock is specific to the analog input section
        of multiplexed devices.

        By default, NI-DAQmx selects the maximum convert rate
        supported by the device, plus 10 microseconds per channel
        settling time. Other task settings, such as high channel
        counts or setting Delay, can result in a faster default
        convert rate.

        Set to None to reset
        """
        err, value = self.lib.GetAIConvRate(RetValue('f64'))
        return value

    @convert_clock_rate.setter
    def convert_clock_rate(self, value):
        if value is None:
            self.lib.ResetAIConvRate()
        else:
            return self.lib.SetAIConvRate(value)

    def sample_clock_max_rate(self):
        """Maximum Sample Clock rate supported by the task,
        based on other timing settings. For output tasks, the maximum
        Sample Clock rate is the maximum rate of the DAC. For input
        tasks, NI-DAQmx calculates the maximum sampling rate
        differently for multiplexed devices than simultaneous sampling
        devices.

        For multiplexed devices, NI-DAQmx calculates the maximum
        sample clock rate based on the maximum AI Convert Clock rate
        unless you set Rate. If you set that property, NI-DAQmx
        calculates the maximum sample clock rate based on that
        setting. Use Maximum Rate to query the maximum AI Convert
        Clock rate. NI-DAQmx also uses the minimum sample clock delay
        to calculate the maximum sample clock rate unless you set
        Delay.

        For simultaneous sampling devices, the maximum Sample Clock
        rate is the maximum rate of the ADC.
        """
        err, value = self.lib.GetSampClkMaxRate(RetValue('f64'))
        return value

    # Not implemented:
    # DAQmxReadBinary*, DAQmxReadCounter*, DAQmxReadDigital*
    # DAQmxGetNthTaskReadChannel, DAQmxReadRaw
    # DAQmxWrite*
    # DAQmxExportSignal
    # DAQmxCalculateReversePolyCoeff, DAQmxCreateLinScale
    # DAQmxWaitForNextSampleClock
    # DAQmxSwitch*
    # DAQmxConnectTerms, DAQmxDisconnectTerms, DAQmxTristateOutputTerm
    # DAQmxResetDevice
    # DAQmxControlWatchdog*

    # DAQmxAOSeriesCalAdjust, DAQmxESeriesCalAdjust, DAQmxGet*,
    # DAQmxMSeriesCalAdjust, DAQmxPerformBridgeOffsetNullingCal, DAQmxRestoreLastExtCalConst
    # DAQmxSelfCal, DAQmxSetAIChanCalCalDate, DAQmxSetAIChanCalExpDate, DAQmxSSeriesCalAdjust
    # External Calibration, DSA Calibration, PXI-42xx Calibration, SCXI Calibration
    # Storage, TEDS
    # DAQmxSetAnalogPowerUpStates, DAQmxSetDigitalPowerUpStates
    # DAQmxGetExtendedErrorInfo

    @Feat(values={True: Constants.Val_AllowRegen, False: Constants.Val_DoNotAllowRegen})
    def regeneration_enabled(self):
        """Generating the same data more than once is allowed.

        Set to None to reset.
        """
        err, value = self.lib.GetWriteRegenMode(RetValue('i32'))
        return value

    @regeneration_enabled.setter
    def regeneration_enabled(self, value):
        if value is None:
            self.lib.ResetWriteRegenMode()
        else:
            self.lib.SetWriteRegenMode(value)

    #TODO CHECK
    @Feat(values={'digital_edge': Constants.Val_DigEdge, 'disable': Constants.Val_None, None: None})
    def arm_start_trigger_type(self):
        """the type of trigger to use to arm the task for a
        Start Trigger. If you configure an Arm Start Trigger, the task
        does not respond to a Start Trigger until the device receives
        the Arm Start Trigger.

        Use None to reset
        """

        err, value = self.lib.GetArmStartTrigType(RetValue('i32'))
        return value

    @arm_start_trigger_type.setter
    def arm_start_trigger_type(self, trigger_type):
        if trigger_type is None:
            self.lib.ResetArmStartTrigType()
        else:
            self.lib.SetArmStartTrigType(trigger_type)


    @Feat()
    def arm_start_trigger_source(self):
        """Rhe name of a terminal where there is a digital
        signal to use as the source of the Arm Start Trigger

        Use None to Reset
        """
        err, value = self.lib.GetDigEdgeArmStartTrigSrc(RetStr(default_buf_size))
        return value

    @arm_start_trigger_source.setter
    @arm_start_trigger_source.setter
    def arm_start_trigger_source(self, source):
        source = str (source)
        if source is None:
            self.lib.ResetDigEdgeArmStartTrigSrc()
        else:
            self.lib.SetDigEdgeArmStartTrigSrc(source)

    @Feat(values={None: None}.update(_EDGE_TYPES))
    def arm_start_trigger_edge(self):
        """on which edge of a digital signal to arm the task
        for a Start Trigger

        Set to None to reset
        """
        err, value = self.lib.GetDigEdgeArmStartTrigEdge(RetValue('i32'))

    @arm_start_trigger_edge.setter
    def arm_start_trigger_edge(self, edge):
        if edge is None:
            self.lib.ResetDigEdgeArmStartTrigEdge()
        else:
            self.lib.SetDigEdgeArmStartTrigEdge(edge)

    @Feat(values={None: None}.update(_TRIGGER_TYPES))
    def pause_trigger_type(self):
        """The type of trigger to use to pause a task.

        Set to None to Reset
        """
        err, value = self.lib.GetPauseTrigType(RetValue('i32'))
        return value

    @pause_trigger_type.setter
    def pause_trigger_type(self, trigger_type):
        if trigger_type is None:
            self.lib.ResetPauseTrigType()
        else:
            self.lib.SetPauseTrigType(trigger_type)

    @Feat()
    def pause_trigger_source(self):
        """The name of a virtual channel or terminal where
        there is an analog signal to use as the source of the trigger.

        For E Series devices, if you use a channel name, the channel
        must be the only channel in the task. The only terminal you
        can use for E Series devices is PFI0.
        """

        type = self.pause_trigger_type
        if type == 'digital_level':
            fun = self.lib.GetDigLvlPauseTrigSrc
        elif type == 'analog_level':
            fun = self.lib.GetAnlgLvlPauseTrigSrc
        elif type == 'analog_window':
            fun = self.lib.GetAnlgWinPauseTrigSrc
        else:
            raise InstrumentError('Pause trigger type is not specified')

        err, value = fun(*RetStr(default_buf_size))
        return value

    @pause_trigger_source.setter
    def pause_trigger_source(self, source):

        type = self.pause_trigger_type
        if type == 'digital_level':
            fun = self.lib.SetDigLvlPauseTrigSrc
        elif type == 'analog_level':
            fun = self.lib.SetAnlgLvlPauseTrigSrc
        elif type == 'analog_window':
            fun = self.lib.SetAnlgWinPauseTrigSrc
        else:
            raise InstrumentError('Pause trigger type is not specified')

        fun(source)

    @Feat()
    def pause_trigger_when(self):
        """
        Specifies whether the task pauses above or below the threshold
        you specify with Level.

        Specifies whether the task pauses while the trigger signal is
        inside or outside the window you specify with Bottom and Top.

        Specifies whether the task pauses while the signal is high or
        low.

        Set To None to reset
        """
        type = self.pause_trigger_type
        if type == 'digital_level':
            fun = self.lib.SetDigLvlPauseTrigWhen
            convert = _WHEN_TRIGGER_DIG
        elif type == 'analog_level':
            fun = self.lib.SetAnlgLvlPauseTrigWhen
            convert = _WHEN_TRIGGER_ALVL
        elif type == 'analog_window':
            fun = self.lib.SetAnlgWinPauseTrigWhen
            convert = _WHEN_TRIGGER_AWIN
        else:
            raise InstrumentError('Pause trigger type is not specified')

        err, val = fun(RetValue('i32'))
        for key, value in convert.items():
            if key == val:
                return val
        else:
            raise ValueError(val)

    @pause_trigger_when.setter
    def pause_trigger_when (self, when=None):

        if when is None:
            self.lib.ResetDigLvlPauseTrigWhen()
            return

        type = self.pause_trigger_type
        if type == 'digital_level':
            fun = self.lib.SetDigLvlPauseTrigWhen
            convert = _WHEN_TRIGGER_DIG
        elif type == 'analog_level':
            fun = self.lib.SetAnlgLvlPauseTrigWhen
            convert = _WHEN_TRIGGER_ALVL
        elif type == 'analog_window':
            fun = self.lib.SetAnlgWinPauseTrigWhen
            convert = _WHEN_TRIGGER_AWIN
        else:
            raise InstrumentError('Pause trigger type is not specified')

        fun(convert[when])

    def read_current_position (self):
        """Samples per channel the current position in the buffer.
        """
        err, value = self.lib.GetReadCurrReadPos(*RetValue('u64'))
        return value

    def samples_per_channel_available(self):
        """The number of samples available to read per channel.

         This value is the same for all channels in the task.
        """
        err, value = self.lib.GetReadAvailSampPerChan(*RetValue('u32'))
        return value

    def samples_per_channel_acquired(self):
        """The total number of samples acquired by each channel.

        NI-DAQmx returns a single value because this value is
        the same for all channels.
        """
        err, value = self.lib.GetReadTotalSampPerChanAcquired(*RetValue('u32'))
        return value

    @Action(units='seconds')
    def wait_until_done(self, timeout=-1):
        """Wait for the measurement or generation to complete. Use this
        function to ensure that the specified operation is complete
        before you stop the task.

        :param timeout: The maximum amount of time, in seconds, to wait for the
          measurement or generation to complete. The function returns
          an error if the time elapses before the measurement or
          generation is complete.

          A value of -1 (Constants.Val_WaitInfinitely) means to wait
          indefinitely.

          If you set timeout to 0, the function checks once and
          returns an error if the measurement or generation is not
          done.
        """
        if timeout < 0:
            timeout = Constants.Val_WaitInfinitely
        return self.lib.WaitUntilTaskDone(timeout)


class Channel(_Base):
    """A virtual channel is a collection of settings such as a name,
    a physical channel, input terminal connections, the type of measurement
    or generation, and can include scaling information.
    """

    IO_TYPE = None

    def __init__(self, task=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._task = None
        if task == 'create':
            task = Task.typed_task(self.IO_TYPE)()
            print(task)
        self.task = task

    @property
    def task(self):
        return self._task

    @task.setter
    def task(self, value):
        if not self._task is None:
            raise Exception
        self._task = value
        if value is not None:
            self.log_debug('Creating channel {} with {}'.format(self.CREATE_FUN, self._create_args))
            value.execute_fun(self.CREATE_FUN, *self._create_args)

    def _preprocess_args(self, name, *args):
        """Injects device_name to all call to the library
        """
        return super()._preprocess_args(name, *((self.task.task_handle, self.name) + args))

    @Feat(read_once=True, values=_CHANNEL_TYPES)
    def io_type(self):
        """The type of the virtual channel.
        """
        err, value = self.lib.GetChanType(RetValue('i32'))
        return value

    @Feat(read_once=True)
    def physical_channel_name(self,):
        """Name of the physical channel upon which this virtual channel is based.
        """
        err, value = self.lib.GetPhysicalChanName(*RetStr(default_buf_size))
        return value

    def operation_direction(self):
        return 'input' if self.CHANNEL_TYPE else 'output'

    @Feat(read_once=True)
    def is_global(self):
        """Indicates whether the channel is a global channel.
        """
        err, value = self.lib.GetChanIsGlobal(RetValue('u32'))
        return value

    # TODO: DAQmx*ChanDescr

    @Feat()
    def buffer_size_on_board(self):
        """The number of samples the I/O buffer can hold for each
        channel in the task.

        If on_board is True then specifies in samples per channel the
        size of the onboard I/O buffer of the device.

        See also
        --------
        set_buffer_size, reset_buffer_size
        """
        fun = self.__get_fun('GetBuf{}OnbrdBufSize')
        err, value = fun(RetValue('u32'))
        return value

    @Feat()
    def buffer_size(self):
        """The number of samples the I/O buffer can hold for each
        channel in the task.

        Set to 0 to perform a hardware-timed operation without
        using a buffer. Setting this property overrides the automatic I/O
        buffer allocation that NI-DAQmx performs.

        Set to None to reset.
        """
        fun = self.__get_fun('GetBuf{}BufSize')
        err, value = fun(RetValue('u32'))
        return value

    @buffer_size.setter
    def buffer_size(self, size):
        if size is None:
            fun = self.__get_fun('ResetBuf{}BufSize')
            err = fun()
        else:
            fun = self.__get_fun('SetBuf{}BufSize')
            err = fun(size)

    @Feat()
    def max(self):
        """Maximum value value.

        Set to None to reset.
        """
        fun = self.__get_fun('Get{}Max')
        err, value = fun(RetValue('f64'))
        return value

    @max.setter
    def max(self, value):
        if value is None:
            fun = self.__get_fun('Reset{}Max')
            err = fun()
        else:
            fun = self.__get_fun('Set{}Max')
            err = fun(value)

    @Feat()
    def min(self):
        """Minimum value value.

        Set to None to reset.
        """
        fun = self.__get_fun('Get{}Min')
        err, value = fun(RetValue('f64'))
        return value

    @min.setter
    def min(self, value):
        if value is None:
            fun = self.__get_fun('Reset{}Min')
            err = fun()
        else:
            fun = self.__get_fun('Set{}Min')
            err = fun(value)

    @Feat()
    def range_high(self):
        """The upper limit of the input range of the
        device. This value is in the native units of the device. On E
        Series devices, for example, the native units is volts.

        Set to None to reset.
        """
        fun = self.__get_fun('Get{}RngHigh')
        err, value = fun(RetValue('f64'))
        return value

    @range_high.setter
    def range_high(self, value):
        if value is None:
            fun = self.__get_fun('Reset{}RngHigh')
            err = fun()
        else:
            fun = self.__get_fun('Set{}RngHigh')
            err = fun(value)

    @Feat()
    def range_low(self):
        """The lower limit of the input range of the
        device. This value is in the native units of the device. On E
        Series devices, for example, the native units is volts.

        Set to None to reset.
        """
        fun = self.__get_fun('Get{}RngLow')
        err, value = fun(RetValue('f64'))
        return value

    @range_low.setter
    def range_low(self, value):
        if value is None:
            fun = self.__get_fun('Reset{}RngLow')
            err = fun()
        else:
            fun = self.__get_fun('Set{}RngLow')
            err = fun(value)

    @Feat()
    def gain(self):
        """Gain factor to apply to the channel.

        Set to None to reset.
        """
        fun = self.__get_fun('Get{}Gain')
        err, value = fun(RetValue('f64'))
        return value

    @gain.setter
    def gain(self, value):
        if value is None:
            fun = self.__get_fun('Reset{}Gain')
            err = fun()
        else:
            fun = self.__get_fun('Set{}Gain')
            err = fun(value)

    @Feat()
    def number_of_lines(self):
        """Number of digital lines in the channel.
        """
        err, value = self.__get_fun('Get{}NumLines')(RetValue('u32'))
        return value


    def get_units(self, channel_name):
        """
        Specifies in what units to generate voltage on the
        channel. Write data to the channel in the units you select.

        Specifies in what units to generate current on the
        channel. Write data to the channel is in the units you select.

        See also
        --------
        set_units, reset_units
        """
        channel_name = str(channel_name)
        mt = self.get_measurment_type(channel_name)
        channel_type = self.channel_type
        if mt=='voltage':
            d = int32(0)
            CALL('Get%sVoltageUnits' % (channel_type), self, channel_name, ctypes.byref(d))
            units_map = {Contants.Val_Volts:'volts',
                         #Constants.Val_FromCustomScale:'custom_scale',
                         #Constants.Val_FromTEDS:'teds',
            }
            return units_map[d.value]
        raise NotImplementedError('{} {}'.format(channel_name, mt))


    @Feat(values={'none': Constants.Val_None, 'once': Constants.Val_Once,
                  'every_sample': Constants.Val_EverySample})
    def auto_zero_mode(self):
        """When to measure ground. NI-DAQmx subtracts the
        measured ground voltage from every sample.

        Set to None to reset.
        """
        fun = self.__get_fun('Get{}AutoZeroMode')
        err, value = fun(RetValue('i32'))
        return value

    @auto_zero_mode.setter
    def auto_zero_mode(self, value):
        if value is None:
            fun = self.__get_fun('Reset{}AutoZeroMode')
            err = fun()
        else:
            fun = self.__get_fun('Set{}AutoZeroMode')
            err = fun(value)

    @Feat(values={'dma': Constants.Val_DMA, 'interrupts': Constants.Val_Interrupts,
                  'programmed_io': Constants.Val_ProgrammedIO,
                  'usb': Constants.Val_USBbulk})
    def data_transfer_mode(self):
        """When to measure ground. NI-DAQmx subtracts the
        measured ground voltage from every sample.

        Set to None to reset.
        """
        fun = self.__get_fun('Get{}DataXferMech')
        err, value = fun(RetValue('i32'))
        return value

    @data_transfer_mode.setter
    def data_transfer_mode(self, value):
        if value is None:
            fun = self.__get_fun('Reset{}DataXferMech')
            err = fun()
        else:
            fun = self.__get_fun('Set{}DataXferMech')
            err = fun(value)

    @Feat(values={True: 1, False: 0, None: None})
    def duplicate_count_prevention_enabled(self):
        """Duplicate count prevention enabled.

        Set to None to Reset
        """
        err, value = self.lib.GetCIDupCountPrevent(RetValue('u32'))
        return value != 0

    @duplicate_count_prevention_enabled.setter
    def duplicate_count_prevention_enabled(self, value):
        if value is None:
            err = self.lib.ResetCIDupCountPrevent()
        else:
            err = self.lib.SetCIDupCountPrevent(value)

    @Feat()
    def timebase_rate(self):
        """Frequency of the counter timebase (Hz)

        TODO Can I put units and still None

        Set to None to reset.
        See also
        --------
        set_timebase_rate, reset_timebase_rate
        """
        err, value = self.lib.GetCICtrTimebaseRate(RetValue('f64'))
        return value

    @timebase_rate.setter
    def timebase_rate(self, value):
        if value is None:
            err = self.lib.ResetCICtrTimebaseRate()
        else:
            err = self.lib.SetCICtrTimebaseRate(value)


    @Feat(None)
    def terminal_pulse (self, terminal):
        """Terminal to generate pulses.
        """
        self.lib.SetCOPulseTerm(terminal)


    @Feat(None)
    def terminal_count_edges(self, channel, terminal):
        """Input terminal of the signal to measure.
        """
        self.lib.SetCICountEdgesTerm(terminal)
"""

DoneEventCallback_map = dict(AI=ctypes.CFUNCTYPE (int32, AnalogInputTask, int32, void_p),
                             AO=ctypes.CFUNCTYPE (int32, AnalogOutputTask, int32, void_p),
                             DI=ctypes.CFUNCTYPE (int32, DigitalInputTask, int32, void_p),
                             DO=ctypes.CFUNCTYPE (int32, DigitalOutputTask, int32, void_p),
                             CI=ctypes.CFUNCTYPE (int32, CounterInputTask, int32, void_p),
                             CO=ctypes.CFUNCTYPE (int32, CounterOutputTask, int32, void_p),
                             )
EveryNSamplesEventCallback_map = dict(AI=ctypes.CFUNCTYPE (int32, AnalogInputTask, int32, uInt32, void_p),
                                      AO=ctypes.CFUNCTYPE (int32, AnalogOutputTask, int32, uInt32, void_p),
                                      DI=ctypes.CFUNCTYPE (int32, DigitalInputTask, int32, uInt32, void_p),
                                      DO=ctypes.CFUNCTYPE (int32, DigitalOutputTask, int32, uInt32, void_p),
                                      CI=ctypes.CFUNCTYPE (int32, CounterInputTask, int32, uInt32, void_p),
                                      CO=ctypes.CFUNCTYPE (int32, CounterOutputTask, int32, uInt32, void_p),
                                      )
SignalEventCallback_map = dict(AI=ctypes.CFUNCTYPE (int32, AnalogInputTask, int32, void_p),
                               AO=ctypes.CFUNCTYPE (int32, AnalogOutputTask, int32, void_p),
                               DI=ctypes.CFUNCTYPE (int32, DigitalInputTask, int32, void_p),
                               DO=ctypes.CFUNCTYPE (int32, DigitalOutputTask, int32, void_p),
                               CI=ctypes.CFUNCTYPE (int32, CounterInputTask, int32, void_p),
                               CO=ctypes.CFUNCTYPE (int32, CounterOutputTask, int32, void_p),
                               )

"""

if __name__ == '__main__':

    import lantz.log

    lantz.log.log_to_screen(lantz.log.DEBUG)

    inst = System()
    print(inst.version)
    print(inst.device_names)
