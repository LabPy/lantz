# -*- coding: utf-8 -*-
# pylint: disable=E265

"""
    lantz.drivers.andor.ccd
    ~~~~~~~~~~~~~~~~~~~~~~~

    Low level driver wrapping library for CCD and Intensified CCD cameras.
    Only functions for iXon EMCCD cameras were tested.
    Only tested in Windows OS.

    The driver was written for the single-camera scenario. If more than one
    camera is present, some 'read_once=True' should be erased but it
    shouldn't be necessary to make any more changes.

    Sources::

        - Andor SDK 2.96 Manual

    :copyright: 2015 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import numpy as np
import ctypes as ct
from collections import namedtuple

from lantz import Driver, Feat, Action, DictFeat
from lantz.errors import InstrumentError
from lantz.foreign import LibraryDriver
from lantz import Q_

degC = Q_(1, 'degC')
us = Q_(1, 'us')
MHz = Q_(1, 'MHz')
seg = Q_(1, 's')

_ERRORS = {
    20002: 'DRV_SUCCESS',
    20003: 'DRV_VXDNOTINSTALLED',
    20004: 'DRV_ERROR_SCAN',
    20005: 'DRV_ERROR_CHECK_SUM',
    20006: 'DRV_ERROR_FILELOAD',
    20007: 'DRV_UNKNOWN_FUNCTION',
    20008: 'DRV_ERROR_VXD_INIT',
    20009: 'DRV_ERROR_ADDRESS',
    20010: 'DRV_ERROR_PAGELOCK',
    20011: 'DRV_ERROR_PAGE_UNLOCK',
    20012: 'DRV_ERROR_BOARDTEST',
    20013: 'Unable to communicate with card.',
    20014: 'DRV_ERROR_UP_FIFO',
    20015: 'DRV_ERROR_PATTERN',
    20017: 'DRV_ACQUISITION_ERRORS',
    20018: 'Computer unable to read the data via the ISA slot at the required rate.',
    20019: 'DRV_ACQ_DOWNFIFO_FULL',
    20020: 'RV_PROC_UNKNOWN_INSTRUCTION',
    20021: 'DRV_ILLEGAL_OP_CODE',
    20022: 'Unable to meet Kinetic cycle time.',
    20023: 'Unable to meet Accumulate cycle time.',
    20024: 'No acquisition has taken place',
    20026: 'Overflow of the spool buffer.',
    20027: 'DRV_SPOOLSETUPERROR',
    20033: 'DRV_TEMPERATURE_CODES',
    20034: 'Temperature is OFF.',
    20035: 'Temperature reached but not stabilized.',
    20036: 'Temperature has stabilized at set point.',
    20037: 'Temperature has not reached set point.',
    20038: 'DRV_TEMPERATURE_OUT_RANGE',
    20039: 'DRV_TEMPERATURE_NOT_SUPPORTED',
    20040: 'Temperature had stabilized but has since drifted.',
    20049: 'DRV_GENERAL_ERRORS',
    20050: 'DRV_INVALID_AUX',
    20051: 'DRV_COF_NOTLOADED',
    20052: 'DRV_FPGAPROG',
    20053: 'DRV_FLEXERROR',
    20054: 'DRV_GPIBERROR',
    20064: 'DRV_DATATYPE',
    20065: 'DRV_DRIVER_ERRORS',
    20066: 'Invalid parameter 1',
    20067: 'Invalid parameter 2',
    20068: 'Invalid parameter 3',
    20069: 'Invalid parameter 4',
    20070: 'DRV_INIERROR',
    20071: 'DRV_COFERROR',
    20072: 'Acquisition in progress',
    20073: 'The system is not currently acquiring',
    20074: 'DRV_TEMPCYCLE',
    20075: 'System not initialized',
    20076: 'DRV_P5INVALID',
    20077: 'DRV_P6INVALID',
    20078: 'Not a valid mode',
    20079: 'DRV_INVALID_FILTER',
    20080: 'DRV_I2CERRORS',
    20081: 'DRV_DRV_I2CDEVNOTFOUND',
    20082: 'DRV_I2CTIMEOUT',
    20083: 'DRV_P7INVALID',
    20089: 'DRV_USBERROR',
    20090: 'DRV_IOCERROR',
    20091: 'DRV_VRMVERSIONERROR',
    20093: 'DRV_USB_INTERRUPT_ENDPOINT_ERROR',
    20094: 'DRV_RANDOM_TRACK_ERROR',
    20095: 'DRV_INVALID_TRIGGER_MODE',
    20096: 'DRV_LOAD_FIRMWARE_ERROR',
    20097: 'DRV_DIVIDE_BY_ZERO_ERROR',
    20098: 'DRV_INVALID_RINGEXPOSURES',
    20099: 'DRV_BINNING_ERROR',
    20990: 'No camera present',
    20991: 'Feature not supported on this camera.',
    20992: 'Feature is not available at the moment.',
    20115: 'DRV_ERROR_MAP',
    20116: 'DRV_ERROR_UNMAP',
    20117: 'DRV_ERROR_MDL',
    20118: 'DRV_ERROR_UNMDL',
    20119: 'DRV_ERROR_BUFFSIZE',
    20121: 'DRV_ERROR_NOHANDLE',
    20130: 'DRV_GATING_NOT_AVAILABLE',
    20131: 'DRV_FPGA_VOLTAGE_ERROR',
    20100: 'DRV_INVALID_AMPLIFIER',
    20101: 'DRV_INVALID_COUNTCONVERT_MODE'
}


class CCD(LibraryDriver):

    LIBRARY_NAME = 'atmcd64d.dll'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cameraIndex = ct.c_int(0)

    def _patch_functions(self):
        internal = self.lib.internal
        internal.GetCameraSerialNumber.argtypes = [ct.pointer(ct.c_uint)]
        internal.Filter_SetAveragingFactor.argtypes = [ct.c_int]
        internal.Filter_SetThreshold.argtypes = ct.c_float
        internal.Filter_GetThreshold.argtypes = ct.c_float

    def _return_handler(self, func_name, ret_value):
        excl_func = ['GetTemperatureF', 'IsCountConvertModeAvailable',
                     'IsAmplifierAvailable', 'IsTriggerModeAvailable']
        if ret_value != 20002 and func_name not in excl_func:
            raise InstrumentError('{}'.format(_ERRORS[ret_value]))
        return ret_value

    def initialize(self):
        """ This function will initialize the Andor SDK System. As part of the
        initialization procedure on some cameras (i.e. Classic, iStar and
        earlier iXion) the DLL will need access to a DETECTOR.INI which
        contains information relating to the detector head, number pixels,
        readout speeds etc. If your system has multiple cameras then see the
        section Controlling multiple cameras.
        """
        self.lib.Initialize()

        self.triggers = {'Internal': 0, 'External': 1, 'External Start': 6,
                         'External Exposure': 7, 'External FVB EM': 9,
                         'Software Trigger': 10,
                         'External Charge Shifting': 12}
        self.savetypes = {'Signed16bits': 1, 'Signed32bits': 2, 'Float': 3}

        # Initial values

        self.readout_packing_state = False
        self.readout_packing = self.readout_packing_state

        self.readout_mode_mode = 'Image'
        self.readout_mode = self.readout_mode_mode

        self.photon_counting_mode_state = False
        self.photon_counting_mode = self.photon_counting_mode_state

        self.frame_transfer_mode_state = False
        self.frame_transfer_mode = self.frame_transfer_mode_state

        self.fan_mode_index = 'onfull'
        self.fan_mode = self.fan_mode_index

        self.EM_gain_mode_index = 'RealGain'
        self.EM_gain_mode = self.EM_gain_mode_index

        self.cooled_on_shutdown_value = False
        self.cooled_on_shutdown = self.cooled_on_shutdown_value

        self.baseline_offset_value = 100
        self.baseline_offset = self.baseline_offset_value

        self.adv_trigger_mode_state = True
        self.adv_trigger_mode = self.adv_trigger_mode_state

        self.acq_mode = 'Single Scan'
        self.acquisition_mode = self.acq_mode

        self.amp_typ = 0

        self.horiz_shift_speed_index = 0
        self.horiz_shift_speed = self.horiz_shift_speed_index

        self.vert_shift_speed_index = 0
        self.vert_shift_speed = self.vert_shift_speed_index

        self.preamp_index = 0
        self.preamp = self.preamp_index

        self.temperature_sp = 0 * degC
        self.temperature_setpoint = self.temperature_sp

        self.auxout = np.zeros(4, dtype=bool)
        for i in np.arange(1, 5):
            self.out_aux_port[i] = False

        self.trigger_mode_index = 'Internal'
        self.trigger_mode = self.trigger_mode_index

    def finalize(self):
        """Finalize Library. Concluding function.
        """
        if self.status != 'Camera is idle, waiting for instructions.':
            self.abort_acquisition()
        self.cooler_on = False
        self.free_int_mem()
        self.lib.ShutDown()

    ### SYSTEM INFORMATION

    @Feat(read_once=True)
    def ncameras(self):
        """This function returns the total number of Andor cameras currently
        installed. It is possible to call this function before any of the
        cameras are initialized.
        """
        n = ct.c_long()
        self.lib.GetAvailableCameras(ct.pointer(n))
        return n.value

    def camera_handle(self, index):
        """This function returns the handle for the camera specified by
        cameraIndex. When multiple Andor cameras are installed the handle of
        each camera must be retrieved in order to select a camera using the
        SetCurrentCamera function.
        The number of cameras can be obtained using the GetAvailableCameras
        function.

        :param index: index of any of the installed cameras.
                      Valid values: 0 to NumberCameras-1 where NumberCameras
                      is the value returned by the GetAvailableCameras function.
        """
        index = ct.c_long(index)
        handle = ct.c_long()
        self.lib.GetCameraHandle(index, ct.pointer(handle))
        return handle.value

    @Feat()
    def current_camera(self):
        """When multiple Andor cameras are installed this function allows the
        user to select which camera is currently active. Once a camera has been
        selected the other functions can be called as normal but they will only
        apply to the selected camera. If only 1 camera is installed calling
        this function is not required since that camera will be selected by
        default.
        """
        n = ct.c_long()     # current camera handler
        self.lib.GetCurrentCamera(ct.pointer(n))
        return n.value

    @current_camera.setter
    def current_camera(self, value):
        value = ct.c_long(value)
        self.lib.SetCurrentCamera(value.value)    # needs camera handler

    @Feat(read_once=True)
    def idn(self):
        """Identification of the device
        """
        hname = (ct.c_char * 100)()
        self.lib.GetHeadModel(ct.pointer(hname))
        hname = str(hname.value)[2:-1]
        sn = ct.c_uint()
        self.lib.GetCameraSerialNumber(ct.pointer(sn))
        return 'Andor ' + hname + ', serial number ' + str(sn.value)

    @Feat(read_once=True)
    def hardware_version(self):
        pcb, decode = ct.c_uint(), ct.c_uint()
        dummy1, dummy2 = ct.c_uint(), ct.c_uint()
        firmware_ver, firmware_build = ct.c_uint(), ct.c_uint()
        self.lib.GetHardwareVersion(ct.pointer(pcb), ct.pointer(decode),
                                    ct.pointer(dummy1), ct.pointer(dummy2),
                                    ct.pointer(firmware_ver),
                                    ct.pointer(firmware_build))
        results = namedtuple('hardware_versions',
                             'PCB Flex10K CameraFirmware CameraFirmwareBuild')
        return results(pcb.value, decode.value, firmware_ver.value,
                       firmware_build.value)

    @Feat(read_once=True)
    def software_version(self):
        eprom, coffile, vxdrev = ct.c_uint(), ct.c_uint(), ct.c_uint()
        vxdver, dllrev, dllver = ct.c_uint(), ct.c_uint(), ct.c_uint()
        self.lib.GetSoftwareVersion(ct.pointer(eprom), ct.pointer(coffile),
                                    ct.pointer(vxdrev), ct.pointer(vxdver),
                                    ct.pointer(dllrev), ct.pointer(dllver))
        results = namedtuple('software_versions',
                             'EPROM COF DriverRev DriverVer DLLRev DLLVer')
        return results(eprom.value, coffile.value, vxdrev.value,
                       vxdver.value, dllrev.value, dllver.value)

    # TODO: Make sense of this:
    @Feat(read_once=True)
    def capabilities(self):
        """This function will fill in an AndorCapabilities structure with the
        capabilities associated with the connected camera. Individual
        capabilities are determined by examining certain bits and combinations
        of bits in the member variables of the AndorCapabilites structure.
        """

        class Capabilities(ct.Structure):
            _fields_ = [("Size", ct.c_ulong),
                        ("AcqModes", ct.c_ulong),
                        ("ReadModes", ct.c_ulong),
                        ("FTReadModes", ct.c_ulong),
                        ("TriggerModes", ct.c_ulong),
                        ("CameraType", ct.c_ulong),
                        ("PixelModes", ct.c_ulong),
                        ("SetFunctions", ct.c_ulong),
                        ("GetFunctions", ct.c_ulong),
                        ("Features", ct.c_ulong),
                        ("PCICard", ct.c_ulong),
                        ("EMGainCapability", ct.c_ulong)]

        stru = Capabilities()
        stru.Size = ct.sizeof(stru)
        self.lib.GetCapabilities(ct.pointer(stru))

        return stru

    @Feat(read_once=True)
    def controller_card(self):
        """This function will retrieve the type of PCI controller card included
        in your system. This function is not applicable for USB systems. The
        maximum number of characters that can be returned from this function is
        10.
        """

        model = ct.c_wchar_p()
        self.lib.GetControllerCardModel(ct.pointer(model))

        return model.value

    @Feat(read_once=True)
    def count_convert_wavelength_range(self):
        """This function returns the valid wavelength range available in Count
        Convert mode."""
        mini = ct.c_float()
        maxi = ct.c_float()
        self.lib.GetCountConvertWavelengthRange(ct.pointer(mini),
                                                ct.pointer(maxi))
        return (mini.value, maxi.value)

    @Feat(read_once=True)
    def detector_shape(self):
        xp, yp = ct.c_int(), ct.c_int()
        self.lib.GetDetector(ct.pointer(xp), ct.pointer(yp))
        return (xp.value, yp.value)

    @Feat(read_once=True)
    def px_size(self):
        """This function returns the dimension of the pixels in the detector
        in microns.
        """
        xp, yp = ct.c_float(), ct.c_float()

        self.lib.GetPixelSize(ct.pointer(xp), ct.pointer(yp))

        return (xp.value, yp.value)

    def QE(self, wl):
        """Returns the percentage QE for a particular head model at a user
        specified wavelength.
        """
        hname = (ct.c_char * 100)()
        self.lib.GetHeadModel(ct.pointer(hname))

        wl = ct.c_float(wl)
        qe = ct.c_float()

        self.lib.GetQE(ct.pointer(hname), wl, ct.c_uint(0), ct.pointer(qe))

        return qe.value

    def sensitivity(self, ad, amp, i, pa):
        """This function returns the sensitivity for a particular speed.
        """

        sens = ct.c_float()
        ad, amp, i, pa = ct.c_int(ad), ct.c_int(amp), ct.c_int(i), ct.c_int(pa)
        self.lib.GetSensitivity(ad, amp, i, pa, ct.pointer(sens))
        return sens.value

    def count_convert_available(self, mode):
        """This function checks if the hardware and current settings permit
        the use of the specified Count Convert mode.
        """
        mode = ct.c_int(mode)
        ans = self.lib.IsCountConvertModeAvailable(mode)
        if ans == 20002:
            return True
        else:
            return False

    ### SHUTTER     # I couldn't find a better way to do this... sorry
    @Action()
    def shutter(self, typ, mode, ext_closing, ext_opening, ext_mode):
        """This function expands the control offered by SetShutter to allow an
        external shutter and internal shutter to be controlled independently
        (only available on some cameras – please consult your Camera User
        Guide). The typ parameter allows the user to control the TTL signal
        output to an external shutter. The opening and closing times specify
        the length of time required to open and close the shutter (this
        information is required for calculating acquisition timings – see
        SHUTTER TRANSFER TIME).
        The mode and extmode parameters control the behaviour of the internal
        and external shutters. To have an external shutter open and close
        automatically in an experiment, set the mode parameter to “Open” and
        set the extmode parameter to “Auto”. To have an internal shutter open
        and close automatically in an experiment, set the extmode parameter to
        “Open” and set the mode parameter to “Auto”.
        To not use any shutter in the experiment, set both shutter modes to
        permanently open.

        :param typ: 0 (or 1) Output TTL low (or high) signal to open shutter.
        :param mode: Internal shutter: 0 Fully Auto, 1 Permanently Open,
                     2 Permanently Closed, 4 Open for FVB series, 5 Open for any series.
        :param ext_closing: Time shutter takes to close (milliseconds)
        :param ext_opening: Time shutter takes to open (milliseconds)
        :param ext_mode: External shutter: 0 Fully Auto, 1 Permanently Open,
                         2 Permanently Closed, 4 Open for FVB series, 5 Open for any series.
        """
        self.lib.SetShutterEx(ct.c_int(typ), ct.c_int(mode),
                              ct.c_int(ext_closing), ct.c_int(ext_opening),
                              ct.c_int(ext_mode))

    @Feat(read_once=True)
    def shutter_min_times(self):
        """ This function will return the minimum opening and closing times in
        milliseconds for the shutter on the current camera.
        """
        otime, ctime = ct.c_int(), ct.c_int()
        self.lib.GetShutterMinTimes(ct.pointer(ctime), ct.pointer(otime))
        return (otime.value, ctime.value)

    @Feat(read_once=True)
    def has_mechanical_shutter(self):
        state = ct.c_int()
        self.lib.IsInternalMechanicalShutter(ct.pointer(state))
        return bool(state.value)

    ### TEMPERATURE

    @Feat(read_once=True, units='degC')
    def min_temperature(self):
        """This function returns the valid range of temperatures in centigrads
        to which the detector can be cooled.
        """
        mini, maxi = ct.c_int(), ct.c_int()
        self.lib.GetTemperatureRange(ct.pointer(mini), ct.pointer(maxi))
        return mini.value

    @Feat(read_once=True, units='degC')
    def max_temperature(self):
        """This function returns the valid range of temperatures in centigrads
        to which the detector can be cooled.
        """
        mini, maxi = ct.c_int(), ct.c_int()
        self.lib.GetTemperatureRange(ct.pointer(mini), ct.pointer(maxi))
        return maxi.value

    @Feat()
    def temperature_status(self):
        """This function returns the temperature of the detector to the
        nearest degree. It also gives the status of cooling process.
        """
        temp = ct.c_float()
        ans = self.lib.GetTemperatureF(ct.pointer(temp))
        return _ERRORS[ans]

    @Feat(units='degC')
    def temperature(self):
        """This function returns the temperature of the detector to the
        nearest degree. It also gives the status of cooling process.
        """
        temp = ct.c_float()
        self.lib.GetTemperatureF(ct.pointer(temp))
        return temp.value

    @Feat(units='degC')
    def temperature_setpoint(self):
        return self.temperature_sp

    @temperature_setpoint.setter
    def temperature_setpoint(self, value):
        self.temperature_sp = value
        value = ct.c_int(int(value))
        self.lib.SetTemperature(value)

    @Feat(values={True: 1, False: 0})
    def cooler_on(self):
        state = ct.c_int()
        self.lib.IsCoolerOn(ct.pointer(state))
        return state.value

    @cooler_on.setter
    def cooler_on(self, value):
        if value:
            self.lib.CoolerON()
        else:
            self.lib.CoolerOFF()

    @Feat(values={True: 1, False: 0})
    def cooled_on_shutdown(self):
        """This function determines whether the cooler is switched off when
        the camera is shut down.
        """
        return self.cooled_on_shutdown_value

    @cooled_on_shutdown.setter
    def cooled_on_shutdown(self, state):
        ans = self.lib.SetCoolerMode(ct.c_int(state))
        if ans == 20002:
            self.cooled_on_shutdown_value = state

    @Feat(values={'onfull': 0, 'onlow': 1, 'off': 2})
    def fan_mode(self):
        """Allows the user to control the mode of the camera fan. If the
        system is cooled, the fan should only be turned off for short periods
        of time. During this time the body of the camera will warm up which
        could compromise cooling capabilities.
        If the camera body reaches too high a temperature, depends on camera,
        the buzzer will sound. If this happens, turn off the external power
        supply and allow the system to stabilize before continuing.
        """
        return self.fan_mode_index

    @fan_mode.setter
    def fan_mode(self, mode):
        ans = self.lib.SetFanMode(ct.c_int(mode))
        if ans == 20002:
            self.fan_mode_index = mode

    ### FILTERS

    @Feat()
    def averaging_factor(self):
        """Averaging factor to be used with the recursive filter. For
        information on the various data averaging filters available see
        DATA AVERAGING FILTERS in the Special Guides section of the manual.
        """
        af = ct.c_uint()
        self.lib.Filter_GetAveragingFactor(ct.pointer(af))
        return af.value

    @averaging_factor.setter
    def averaging_factor(self, value):
        self.lib.Filter_SetAveragingFactor(ct.c_uint(value))

    @Feat()
    def averaging_frame_count(self):
        """Number of frames to be used when using the frame averaging filter.
        """
        fc = ct.c_uint()
        self.lib.Filter_GetAveragingFrameCount(ct.pointer(fc))
        return fc.value

    @averaging_frame_count.setter
    def averaging_frame_count(self, value):
        self.lib.Filter_SetAveragingFrameCount(ct.c_uint(value))

    @Feat(values={'NAF': 0, 'RAF': 5, 'FAF': 6})
    def averaging_mode(self):
        """Current averaging mode.
        Valid options are:
        0 – No Averaging Filter
        5 – Recursive Averaging Filter
        6 – Frame Averaging Filter
        """
        i = ct.c_int()
        self.lib.Filter_GetDataAveragingMode(ct.pointer(i))
        return i.value

    @averaging_mode.setter
    def averaging_mode(self, value):
        self.lib.Filter_SetDataAveragingMode(ct.c_int(value))

    @Feat(values={'NF': 0, 'MF': 1, 'LAF': 2, 'IRF': 3, 'NTF': 4})
    def noise_filter_mode(self):
        """Set the Noise Filter to use; For information on the various
        spurious noise filters available see SPURIOUS NOISE FILTERS in the
        Special Guides section of the manual.
        Valid options are:
        0 – No Averaging Filter
        1 – Median Filter
        2 – Level Above Filter
        3 – Interquartile Range Filter
        4 – Noise Threshold Filter
        """
        i = ct.c_uint()
        self.lib.Filter_GetMode(ct.pointer(i))
        return i.value

    @noise_filter_mode.setter
    def noise_filter_mode(self, value):
        self.lib.Filter_SetMode(ct.c_uint(value))

    @Feat()
    def filter_threshold(self):
        """Sets the threshold value for the Noise Filter. For information on
        the various spurious noise filters available see SPURIOUS NOISE FILTERS
        in the Special Guides section of the manual.
        Valid values are:
        0 – 65535 for Level Above filte
        0 – 10 for all other filters.
        """
        f = ct.c_float()
        self.lib.Filter_GetThreshold(ct.pointer(f))
        return f.value

    @filter_threshold.setter
    def filter_threshold(self, value):
        self.lib.Filter_SetThreshold(ct.c_float(value))

    @Feat(values={True: 2, False: 0})
    def cr_filter_enabled(self):
        """This function will set the state of the cosmic ray filter mode for
        future acquisitions. If the filter mode is on, consecutive scans in an
        accumulation will be compared and any cosmic ray-like features that are
        only present in one scan will be replaced with a scaled version of the
        corresponding pixel value in the correct scan.
        """
        i = ct.c_int()
        self.lib.GetFilterMode(ct.pointer(i))
        return i.value

    @cr_filter_enabled.setter
    def cr_filter_enabled(self, value):
        self.lib.SetFilterMode(ct.c_int(value))

    ### PHOTON COUNTING MODE

    @Feat(values={True: 1, False: 0})   # FIXME: untested
    def photon_counting_mode(self):
        """This function activates the photon counting option.
        """
        return self.photon_counting_mode_state

    @photon_counting_mode.setter
    def photon_counting_mode(self, state):
        ans = self.lib.SetPhotonCounting(ct.c_int(state))
        if ans == 20002:
            self.photon_counting_mode_state = state

    @Feat(read_once=True)
    def n_photon_counting_div(self):
        """Available in some systems is photon counting mode. This function
        gets the number of photon counting divisions available. The functions
        SetPhotonCounting and SetPhotonCountingThreshold can be used to specify
        which of these divisions is to be used.
        """
        inti = ct.c_ulong()
        self.lib.GetNumberPhotonCountingDivisions(ct.pointer(inti))
        return inti.value

    @Action()       # untested
    def set_photon_counting_divs(self, n, thres):
        """This function sets the thresholds for the photon counting option.
        """
        thres = ct.c_long(thres)
        self.lib.SetPhotonCountingDivisions(ct.c_ulong(n), ct.pointer(thres))

    @Action()
    def set_photon_counting_thres(self, mini, maxi):
        """This function sets the minimum and maximum threshold in counts
        (1-65535) for the photon counting option.
        """
        self.lib.SetPhotonCountingThreshold(ct.c_long(mini), ct.c_long(maxi))

    ### FAST KINETICS MODE

    @Feat(units='s')
    def FK_exposure_time(self):
        """This function will return the current “valid” exposure time for a
        fast kinetics acquisition. This function should be used after all the
        acquisitions settings have been set, i.e. SetFastKinetics and
        SetFKVShiftSpeed. The value returned is the actual time used in
        subsequent acquisitions.
        """
        f = ct.c_float()
        self.lib.GetFKExposureTime(ct.pointer(f))
        return f.value

    ### ACQUISITION HANDLING

    @Feat(values={'Single Scan': 1, 'Accumulate': 2, 'Kinetics': 3,
                  'Fast Kinetics': 4, 'Run till abort': 5})
    def acquisition_mode(self):
        """This function will set the acquisition mode to be used on the next
        StartAcquisition.
        NOTE: In Mode 5 the system uses a “Run Till Abort” acquisition mode. In
        Mode 5 only, the camera continually acquires data until the
        AbortAcquisition function is called. By using the SetDriverEvent
        function you will be notified as each acquisition is completed.
        """
        return self.acq_mode

    @acquisition_mode.setter
    def acquisition_mode(self, mode):
        ans = self.lib.SetAcquisitionMode(ct.c_int(mode))
        if ans == 20002:
            self.acq_mode = mode

    @Action()
    def prepare_acquisition(self):
        """This function reads the current acquisition setup and allocates and
        configures any memory that will be used during the acquisition. The
        function call is not required as it will be called automatically by the
        StartAcquisition function if it has not already been called externally.
        However for long kinetic series acquisitions the time to allocate and
        configure any memory can be quite long which can result in a long delay
        between calling StartAcquisition and the acquisition actually
        commencing. For iDus, there is an additional delay caused by the camera
        being set-up with any new acquisition parameters. Calling
        PrepareAcquisition first will reduce this delay in the StartAcquisition
        call.
        """
        self.lib.PrepareAcquisition()

    @Action()
    def start_acquisition(self):
        """This function starts an acquisition. The status of the acquisition
        can be monitored via GetStatus().
        """
        self.lib.StartAcquisition()

    @Action()
    def abort_acquisition(self):
        """This function aborts the current acquisition if one is active
        """
        self.lib.AbortAcquisition()

    @Action()
    def wait_for_acquisition(self):
        """WaitForAcquisition can be called after an acquisition is started
        using StartAcquisition to put the calling thread to sleep until an
        Acquisition Event occurs. This can be used as a simple alternative to
        the functionality provided by the SetDriverEvent function, as all Event
        creation and handling is performed internally by the SDK library.
        Like the SetDriverEvent functionality it will use less processor
        resources than continuously polling with the GetStatus function. If you
        wish to restart the calling thread without waiting for an Acquisition
        event, call the function CancelWait.
        An Acquisition Event occurs each time a new image is acquired during an
        Accumulation, Kinetic Series or Run-Till-Abort acquisition or at the
        end of a Single Scan Acquisition.
        If a second event occurs before the first one has been acknowledged,
        the first one will be ignored. Care should be taken in this case, as
        you may have to use CancelWait to exit the function.
        """
        self.lib.WaitForAcquisition()

    @Action()
    def cancel_wait(self):
        """This function restarts a thread which is sleeping within the
        WaitForAcquisition  function. The  sleeping  thread  will  return  from
        WaitForAcquisition  with  a  value  not  equal  to DRV_SUCCESS.
        """
        self.lib.CancelWait()

    @Feat()
    def acquisition_progress(self):
        """This function will return information on the progress of the
        current acquisition. It can be called at any time but is best used in
        conjunction with SetDriverEvent.
        The values returned show the number of completed scans in the current
        acquisition. If 0 is returned for both accum and series then either:
        - No acquisition is currently running
        - The acquisition has just completed
        - The very first scan of an acquisition has just started and not yet
        completed.
        GetStatus can be used to confirm if the first scan has just started,
        returning DRV_ACQUIRING, otherwise it will return DRV_IDLE.
        For example, if accum=2 and series=3 then the acquisition has completed
        3 in the series and 2 accumulations in the 4 scan of the series
        """
        acc = ct.c_long()
        series = ct.c_long()
        self.lib.GetAcquisitionProgress(ct.pointer(acc), ct.pointer(series))
        return acc.value, series.value

    @Feat()
    def status(self):
        """This function will return the current status of the Andor SDK
        system. This function should be called before an acquisition is started
        to ensure that it is IDLE and during an acquisition to monitor the
        process.
        """
        st = ct.c_int()
        self.lib.GetStatus(ct.pointer(st))
        if st.value == 20073:
            return 'Camera is idle, waiting for instructions.'
        elif st.value == 20074:
            return 'Camera is executing the temperature cycle.'
        elif st.value == 20072:
            return 'Acquisition in progress.'
        elif st.value == 20023:
            return 'Unable to meet accumulate cycle time.'
        elif st.value == 20022:
            return 'Unable to meet kinetic cycle time.'
        elif st.value == 20013:
            return 'Unable to communicate with card.'
        elif st.value == 20018:
            return ('Computer unable to read the data via the ISA slot at the '
                    'required rate.')
        elif st.value == 20026:
            return 'Overflow of the spool buffer.'

    @Feat()
    def n_exposures_in_ring(self):
        """Gets the number of exposures in the ring at this moment."""
        n = ct.c_int()
        self.lib.GetNumberRingExposureTimes(ct.pointer(n))
        return n.value

    @Feat()
    def buffer_size(self):
        """This function will return the maximum number of images the circular
        buffer can store based on the current acquisition settings.
        """
        n = ct.c_long()
        self.lib.GetSizeOfCircularBuffer(ct.pointer(n))
        return n.value

    @Feat(values={True: 1, False: 0})
    def exposing(self):
        """This function will return if the system is exposing or not. The
        status of the firepulse will be returned.
        NOTE  This is only supported by the CCI23 card.
        """
        i = ct.c_int()
        self.lib.GetCameraEventStatus(ct.pointer(i))
        return i.value

    @Feat()
    def n_images_acquired(self):
        """This function will return the total number of images acquired since
        the current acquisition started. If the camera is idle the value
        returned is the number of images acquired during the last acquisition.
        """
        n = ct.c_long()
        self.lib.GetTotalNumberImagesAcquired(ct.pointer(n))
        return n.value

    @Action()
    def set_image(self, shape=None, binned=(1, 1), p_0=(1, 1)):
        """This function will set the horizontal and vertical binning to be
        used when taking a full resolution image.

        :param hbin: number of pixels to bin horizontally.
        :param vbin: number of pixels to bin vertically.
        :param hstart: Start column (inclusive).
        :param hend: End column (inclusive).
        :param vstart: Start row (inclusive).
        :param vend: End row (inclusive).
        """

        if shape is None:
            shape = self.detector_shape

        (hbin, vbin) = binned
        (hstart, vstart) = p_0
        (hend, vend) = (p_0[0] + shape[0] - 1, p_0[1] + shape[1] - 1)

        self.lib.SetImage(ct.c_int(hbin), ct.c_int(vbin),
                          ct.c_int(hstart), ct.c_int(hend),
                          ct.c_int(vstart), ct.c_int(vend))

    @Feat(values={'FVB': 0, 'Multi-Track': 1, 'Random-Track': 2,
                  'Single-Track': 3, 'Image': 4})
    def readout_mode(self):
        """This function will set the readout mode to be used on the subsequent
        acquisitions.
        """
        return self.readout_mode_mode

    @readout_mode.setter
    def readout_mode(self, mode):
        ans = self.lib.SetReadMode(ct.c_int(mode))
        if ans == 20002:
            self.readout_mode_mode = mode

    @Feat(values={True: 1, False: 0})
    def readout_packing(self):
        """This function will configure whether data is packed into the readout
        register to improve frame rates for sub-images.
        Note: It is important to ensure that no light falls outside of the
        sub-image area otherwise the acquired data will be corrupted. Only
        currently available on iXon+ and iXon3.
        """
        return self.readout_packing_state

    @readout_packing.setter
    def readout_packing(self, state):
        ans = self.lib.SetReadoutRegisterPacking(ct.c_int(state))
        if ans == 20002:
            self.readout_packing_state = state

    ### DATA HANDLING

    @Feat(read_once=True)
    def min_image_length(self):
        """This function will return the minimum number of pixels that can be
        read out from the chip at each exposure. This minimum value arises due
        the way in which the chip is read out and will limit the possible sub
        image dimensions and binning sizes that can be applied.
        """

        # Will contain the minimum number of super pixels on return.
        px = ct.c_int()
        self.lib.GetMinimumImageLength(ct.pointer(px))

        return px.value

    @Action()
    def free_int_mem(self):
        """The FreeInternalMemory function will deallocate any memory used
        internally to store the previously acquired data. Note that once this
        function has been called, data from last acquisition cannot be
        retrived.
        """
        self.lib.FreeInternalMemory()

    def acquired_data(self, shape):
        """This function will return the data from the last acquisition. The
        data are returned as long integers (32-bit signed integers). The
        “array” must be large enough to hold the complete data set.
        """
        size = np.array(shape).prod()
        arr = np.ascontiguousarray(np.zeros(size, dtype=np.int32))
        self.lib.GetAcquiredData(arr.ctypes.data_as(ct.POINTER(ct.c_int32)),
                                 ct.c_ulong(size))
        arr = arr.reshape(shape)
        return arr

    def acquired_data16(self, shape):
        """16-bit version of the GetAcquiredData function. The “array” must be
        large enough to hold the complete data set.
        """
        size = np.array(shape).prod()
        arr = np.ascontiguousarray(np.zeros(size, dtype=np.int16))
        self.lib.GetAcquiredData16(arr.ctypes.data_as(ct.POINTER(ct.c_int16)),
                                   ct.c_ulong(size))
        return arr.reshape(shape)

    def oldest_image(self, shape):
        """This function will update the data array with the oldest image in
        the circular buffer. Once the oldest image has been retrieved it no
        longer is available. The data are returned as long integers (32-bit
        signed integers). The "array" must be exactly the same size as the full
        image.
        """
        size = np.array(shape).prod()
        array = np.ascontiguousarray(np.zeros(size, dtype=np.int32))
        self.lib.GetOldestImage(array.ctypes.data_as(ct.POINTER(ct.c_int32)),
                                ct.c_ulong(size))
        return array.reshape(shape)

    def oldest_image16(self, shape):
        """16-bit version of the GetOldestImage function.
        """
        size = np.array(shape).prod()
        array = np.ascontiguousarray(np.zeros(size, dtype=np.int16))
        self.lib.GetOldestImage16(array.ctypes.data_as(ct.POINTER(ct.c_int16)),
                                  ct.c_ulong(size))
        return array.reshape(shape)

    def most_recent_image(self, shape):
        """This function will update the data array with the most recently
        acquired image in any acquisition mode. The data are returned as long
        integers (32-bit signed integers). The "array" must be exactly the same
        size as the complete image.
        """
        size = np.array(shape).prod()
        arr = np.ascontiguousarray(np.zeros(size, dtype=np.int32))
        self.lib.GetMostRecentImage(arr.ctypes.data_as(ct.POINTER(ct.c_int32)),
                                    ct.c_ulong(size))
        return arr.reshape(shape)

    def most_recent_image16(self, shape):
        """16-bit version of the GetMostRecentImage function.
        """
        size = np.array(shape).prod()
        arr = np.ascontiguousarray(np.zeros(size, dtype=np.int16))
        pt = ct.POINTER(ct.c_int16)
        self.lib.GetMostRecentImage16(arr.ctypes.data_as(pt), ct.c_ulong(size))
        return arr.reshape(shape)

    def images(self, first, last, shape, validfirst, validlast):
        """This function will update the data array with the specified series
        of images from the circular buffer. If the specified series is out of
        range (i.e. the images have been overwritten or have not yet been
        acquired) then an error will be returned.

        :param first: index of first image in buffer to retrieve.
        :param flast: index of last image in buffer to retrieve.
        :param farr: pointer to data storage allocated by the user.
        :param size: total number of pixels.
        :param fvalidfirst: index of the first valid image.
        :param fvalidlast: index of the last valid image.
        """
        size = shape[0] * shape[1] * (1 + last - first)
        array = np.ascontiguousarray(np.zeros(size, dtype=np.int32))
        self.lib.GetImages(ct.c_long(first), ct.c_long(last),
                           array.ctypes.data_as(ct.POINTER(ct.c_int32)),
                           ct.c_ulong(size), ct.pointer(ct.c_long(validfirst)),
                           ct.pointer(ct.c_long(validlast)))

        return array.reshape(-1, shape[0], shape[1])

    def images16(self, first, last, shape, validfirst, validlast):
        """16-bit version of the GetImages function.
        """
        size = shape[0] * shape[1] * (1 + last - first)
        array = np.ascontiguousarray(np.zeros(size, dtype=np.int16))
        self.lib.GetImages16(ct.c_long(first), ct.c_long(last),
                             array.ctypes.data_as(ct.POINTER(ct.c_int16)),
                             ct.c_ulong(size),
                             ct.pointer(ct.c_long(validfirst)),
                             ct.pointer(ct.c_long(validlast)))

        return array.reshape(-1, shape[0], shape[1])

    @Feat()
    def new_images_index(self):
        """This function will return information on the number of new images
        (i.e. images which have not yet been retrieved) in the circular buffer.
        This information can be used with GetImages to retrieve a series of the
        latest images. If any images are overwritten in the circular buffer
        they can no longer be retrieved and the information returned will treat
        overwritten images as having been retrieved.
        """
        first = ct.c_long()
        last = ct.c_long()
        self.lib.GetNumberNewImages(ct.pointer(first), ct.pointer(last))

        return (first.value, last.value)

    @Feat()     # TODO: test this
    def available_images_index(self):
        """This function will return information on the number of available
        images in the circular buffer. This information can be used with
        GetImages to retrieve a series of images. If any images are overwritten
        in the circular buffer they no longer can be retrieved and the
        information returned will treat overwritten images as not available.
        """
        first = ct.c_long()
        last = ct.c_long()
        self.lib.GetNumberAvailableImages(ct.pointer(first), ct.pointer(last))

        return (first.value, last.value)

    def set_dma_parameters(self, n_max_images, s_per_dma):
        """In order to facilitate high image readout rates the controller card
        may wait for multiple images to be acquired before notifying the SDK
        that new data is available. Without this facility, there is a chance
        that hardware interrupts may be lost as the operating system does not
        have enough time to respond to each interrupt. The drawback to this is
        that you will not get the data for an image until all images for that
        interrupt have been acquired.
        There are 3 settings involved in determining how many images will be
        acquired for each notification (DMA Interrupt) of the controller card
        and they are as follows:

        1. The size of the DMA buffer gives an upper limit on the number of
        images that can be stored within it and is usually set to the size
        of one full image when installing the software. This will usually
        mean that if you acquire full frames there will never be more than
        one image per DMA.

        2. A second setting that is used is the minimum amount of time
        (SecondsPerDMA) that should expire between interrupts. This can be
        used to give an indication of the reponsiveness of the operating
        system to interrupts. Decreasing this value will allow more
        interrupts per second and should only be done for faster pcs. The
        default value is 0.03s (30ms), finding the optimal value for your
        pc can only be done through experimentation.

        3. The third setting is an overide to the number of images
        calculated using the previous settings. If the number of images per
        dma is calculated to be greater than MaxImagesPerDMA then it will
        be reduced to MaxImagesPerDMA. This can be used to, for example,
        ensure that there is never more than 1 image per DMA by setting
        MaxImagesPerDMA to 1. Setting MaxImagesPerDMA to zero removes this
        limit. Care should be taken when modifying these parameters as
        missed interrupts may prevent the acquisition from completing.
        """
        self.lib.SetDMAParameters(ct.c_int(n_max_images),
                                  ct.c_float(s_per_dma))

    @Feat()
    def max_images_per_dma(self):
        """This function will return the maximum number of images that can be
        transferred during a single DMA transaction.
        """
        n = ct.c_ulong()
        self.lib.GetImagesPerDMA(ct.pointer(n))
        return n.value

    @Action()
    def save_raw(self, filename, typ):
        """This function saves the last acquisition as a raw data file.
        See self.savetypes for the file type keys.
        """
        self.lib.SaveAsRaw(ct.c_char_p(str.encode(filename)),
                           ct.c_int(self.savetypes[typ]))

    ### EXPOSURE SETTINGS

    @Feat()
    def acquisition_timings(self):
        """This function will return the current “valid” acquisition timing
        information. This  function should be used after all the acquisitions
        settings have been set, e.g. SetExposureTime, SetKineticCycleTime and
        SetReadMode etc. The values returned are the actual times used in
        subsequent acquisitions.
        This function is required as it is possible to set the exposure time to
        20ms, accumulate cycle time to 30ms and then set the readout mode to
        full image. As it can take 250ms to read out an image it is not
        possible to have a cycle time of 30ms.
        All data is measured in seconds.
        """
        exp = ct.c_float()
        accum = ct.c_float()
        kine = ct.c_float()
        self.lib.GetAcquisitionTimings(ct.pointer(exp), ct.pointer(accum),
                                       ct.pointer(kine))
        return exp.value * seg, accum.value * seg, kine.value * seg

    @Action()
    def set_exposure_time(self, time):
        """This function will set the exposure time to the nearest valid value
        not less than the given value, in seconds. The actual exposure time
        used is obtained by GetAcquisitionTimings. Please refer to
        SECTION 5 – ACQUISITION MODES for further information.
        """
        try:
            time.magnitude
        except AttributeError:
            time = time * seg

        self.lib.SetExposureTime(ct.c_float(time.magnitude))

    @Action()
    def set_accum_time(self, time):
        """This function will set the accumulation cycle time to the nearest
        valid value not less than the given value. The actual cycle time used
        is obtained by GetAcquisitionTimings. Please refer to
        SECTION 5 – ACQUISITION MODES for further information.
        """
        try:
            time.magnitude
        except AttributeError:
            time = time * seg

        self.lib.SetAccumulationCycleTime(ct.c_float(time.magnitude))

    @Action()
    def set_kinetic_cycle_time(self, time):
        """This function will set the kinetic cycle time to the nearest valid
        value not less than the given value. The actual time used is obtained
        by GetAcquisitionTimings. . Please refer to
        SECTION 5 – ACQUISITION MODES for further information.
        float time: the kinetic cycle time in seconds.
        """
        try:
            time.magnitude
        except AttributeError:
            time = time * seg

        self.lib.SetKineticCycleTime(ct.c_float(time.magnitude))

    @Action()
    def set_n_kinetics(self, n):
        """This function will set the number of scans (possibly accumulated
        scans) to be taken during a single acquisition sequence. This will only
        take effect if the acquisition mode is Kinetic Series.
        """
        self.lib.SetNumberKinetics(ct.c_int(n))

    @Action()
    def set_n_accum(self, n):
        """This function will set the number of scans accumulated in memory.
        This will only take effect if the acquisition mode is either Accumulate
        or Kinetic Series.
        """
        self.lib.SetNumberAccumulations(ct.c_int(n))

    @Feat(units='s')
    def keep_clean_time(self):
        """This function will return the time to perform a keep clean cycle.
        This function should be used after all the acquisitions settings have
        been set, e.g. SetExposureTime, SetKineticCycleTime and SetReadMode
        etc. The value returned is the actual times used in subsequent
        acquisitions.
        """
        time = ct.c_float()
        self.lib.GetKeepCleanTime(ct.pointer(time))
        return time.value

    @Feat(units='s')
    def readout_time(self):
        """This function will return the time to readout data from a sensor.
        This function should be used after all the acquisitions settings have
        been set, e.g. SetExposureTime, SetKineticCycleTime and SetReadMode
        etc. The value returned is the actual times used in subsequent
        acquisitions.
        """
        time = ct.c_float()
        self.lib.GetReadOutTime(ct.pointer(time))
        return time.value

    @Feat(read_once=True, units='s')
    def max_exposure(self):
        """This function will return the maximum Exposure Time in seconds that
        is settable by the SetExposureTime function.
        """
        exp = ct.c_float()
        self.lib.GetMaximumExposure(ct.pointer(exp))
        return exp.value

    @Feat(read_once=True)
    def n_max_nexposure(self):
        """This function will return the maximum number of exposures that can
        be configured in the SetRingExposureTimes SDK function.
        """
        n = ct.c_int()
        self.lib.GetMaximumNumberRingExposureTimes(ct.pointer(n))
        return n.value

    def true_exposure_times(self, n):       # FIXME: bit order? something
        """This function will return the actual exposure times that the camera
        will use. There may be differences between requested exposures and the
        actual exposures.
        ntimes:  Numbers of times requested.
        """
        times = np.ascontiguousarray(np.zeros(n, dtype=np.float))
        outtimes = times.ctypes.data_as(ct.POINTER(ct.c_float))
        self.lib.GetAdjustedRingExposureTimes(ct.c_int(n), outtimes)
        return times

    def exposure_times(self, value):
        n = ct.c_int(len(value))
        value = np.ascontiguousarray(value.astype(np.float))
        outvalue = value.ctypes.data_as(ct.POINTER(ct.c_float))
        self.lib.SetRingExposureTimes(n, outvalue)

    @Feat(values={True: 1, False: 0})
    def frame_transfer_mode(self):
        """This function will set whether an acquisition will readout in Frame
        Transfer Mode. If the acquisition mode is Single Scan or Fast Kinetics
        this call will have no affect.
        """
        return self.frame_transfer_mode_state

    @frame_transfer_mode.setter
    def frame_transfer_mode(self, state):
        ans = self.lib.SetFrameTransferMode(ct.c_int(state))
        if ans == 20002:
            self.frame_transfer_mode_state = state

    ### AMPLIFIERS, GAIN, SPEEDS

    @Feat(read_once=True)
    def n_preamps(self):
        """Available in some systems are a number of pre amp gains that can be
        applied to the data as it is read out. This function gets the number of
        these pre amp gains available. The functions GetPreAmpGain and
        SetPreAmpGain can be used to specify which of these gains is to be
        used.
        """
        n = ct.c_int()
        self.lib.GetNumberPreAmpGains(ct.pointer(n))
        return n.value

    def preamp_available(self, channel, amp, index, preamp):
        """This function checks that the AD channel exists, and that the
        amplifier, speed and gain are available for the AD channel.
        """
        channel = ct.c_int(channel)
        amp = ct.c_int(amp)
        index = ct.c_int(index)
        preamp = ct.c_int(preamp)
        status = ct.c_int()
        self.lib.IsPreAmpGainAvailable(channel, amp, index, preamp,
                                       ct.pointer(status))

        return bool(status.value)

    def preamp_descr(self, index):
        """This function will return a string with a pre amp gain description.
        The pre amp gain is selected using the index. The SDK has a string
        associated with each of its pre amp gains. The maximum number of
        characters needed to store the pre amp gain descriptions is 30. The
        user has to specify the number of characters they wish to have returned
        to them from this function.
        """
        index = ct.c_int(index)
        descr = (ct.c_char * 30)()
        leng = ct.c_int(30)
        self.lib.GetAmpDesc(index, ct.pointer(descr), leng)
        return str(descr.value)[2:-1]

    def true_preamp(self, index):
        """For those systems that provide a number of pre amp gains to apply
        to the data as it is read out; this function retrieves the amount of
        gain that is stored for a particular index. The number of gains
        available can be obtained by calling the GetNumberPreAmpGains function
        and a specific Gain can be selected using the function SetPreAmpGain.
        """
        index = ct.c_int(index)
        gain = ct.c_float()
        self.lib.GetPreAmpGain(index, ct.pointer(gain))
        return gain.value

    @Feat()
    def preamp(self):
        """This function will set the pre amp gain to be used for subsequent
        acquisitions. The actual gain factor that will be applied can be found
        through a call to the GetPreAmpGain function.
        The number of Pre Amp Gains available is found by calling the
        GetNumberPreAmpGains function.
        """
        return self.preamp_index

    @preamp.setter
    def preamp(self, index):
        self.preamp_index = index
        self.lib.SetPreAmpGain(ct.c_int(index))

    @Feat(values={True: 1, False: 0})
    def EM_advanced_enabled(self):
        """This function turns on and off access to higher EM gain levels
        within the SDK. Typically, optimal signal to noise ratio and dynamic
        range is achieved between x1 to x300 EM Gain.
        Higher gains of > x300 are recommended for single photon counting only.
        Before using higher levels, you should ensure that light levels do not
        exceed the regime of tens of photons per pixel, otherwise accelerated
        ageing of the sensor can occur.
        This is set to False upon initialization of the camera.
        """

        state = ct.c_int()
        self.lib.GetEMAdvanced(ct.pointer(state))
        return state.value

    @EM_advanced_enabled.setter
    def EM_advanced_enabled(self, value):
        self.lib.SetEMAdvanced(ct.c_int(value))

    @Feat(values={'DAC255': 0, 'DAC4095': 1, 'Linear': 2, 'RealGain': 3})
    def EM_gain_mode(self):
        """Set the EM Gain mode to one of the following possible settings.
            Mode 0: The EM Gain is controlled by DAC settings in the range
            0-255. Default mode.
            1: The EM Gain is controlled by DAC settings in the range 0-4095.
            2: Linear mode.
            3: Real EM gain
        """
        return self.EM_gain_mode_index

    @EM_gain_mode.setter
    def EM_gain_mode(self, mode):
        ans = self.lib.SetEMGainMode(ct.c_int(mode))
        if ans == 20002:
            self.EM_gain_mode_index = mode

    @Feat()
    def EM_gain(self):
        """Allows the user to change the gain value. The valid range for the
        gain depends on what gain mode the camera is operating in. See
        SetEMGainMode to set the mode and GetEMGainRange to get the valid range
        to work with. To access higher gain values (>x300) see SetEMAdvanced.
        """
        gain = ct.c_int()
        self.lib.GetEMCCDGain(ct.pointer(gain))

        return gain.value

    @EM_gain.setter
    def EM_gain(self, value):
        self.lib.SetEMCCDGain(ct.c_int(value))

    @Feat()
    def EM_gain_range(self):
        """Returns the minimum and maximum values of the current selected EM
        Gain mode and temperature of the sensor.
        """
        mini, maxi = ct.c_int(), ct.c_int()
        self.lib.GetEMGainRange(ct.pointer(mini), ct.pointer(maxi))

        return (mini.value, maxi.value)

    @Feat(read_once=True)
    def n_ad_channels(self):
        n = ct.c_int()
        self.lib.GetNumberADChannels(ct.pointer(n))
        return n.value

    @Feat(read_once=True)
    def n_amps(self):
        n = ct.c_int()
        self.lib.GetNumberAmp(ct.pointer(n))
        return n.value

    def amp_available(self, iamp):
        """This function checks if the hardware and current settings permit
        the use of the specified amplifier."""
        ans = self.lib.IsAmplifierAvailable(ct.c_int(iamp))
        if ans == 20002:
            return True
        else:
            return False

    def amp_descr(self, index):
        """This function will return a string with an amplifier description.
        The amplifier is selected using the index. The SDK has a string
        associated with each of its amplifiers. The maximum number of
        characters needed to store the amplifier descriptions is 21. The user
        has to specify the number of characters they wish to have returned to
        them from this function.
        """
        index = ct.c_int(index)
        descr = (ct.c_char * 21)()
        leng = ct.c_int(21)
        self.lib.GetAmpDesc(index, ct.pointer(descr), leng)
        return str(descr.value)[2:-1]

    def readout_flipped(self, iamp):
        """On cameras with multiple amplifiers the frame readout may be
        flipped. This function can be used to determine if this is the case.
        """
        flipped = ct.c_int()
        self.lib.IsReadoutFlippedByAmplifier(ct.c_int(iamp),
                                             ct.pointer(flipped))
        return bool(flipped.value)

    def amp_max_hspeed(self, index):
        """This function will return the maximum available horizontal shift
        speed for the amplifier selected by the index parameter.
        """
        hspeed = ct.c_float()
        self.lib.GetAmpMaxSpeed(ct.c_int(index), ct.pointer(hspeed))
        return hspeed.value

    def n_horiz_shift_speeds(self, channel=0, typ=None):
        """As your Andor SDK system is capable of operating at more than one
        horizontal shift speed this function will return the actual number of
        speeds available.

        :param channel: the AD channel.
        :param typ: output amplification. 0 electron multiplication. 1 conventional.
        """
        if typ is None:
            typ = self.amp_typ

        n = ct.c_int()

        self.lib.GetNumberHSSpeeds(ct.c_int(channel),
                                   ct.c_int(typ), ct.pointer(n))

        return n.value

    def true_horiz_shift_speed(self, index=0, typ=None, ad=0):
        """As your Andor system is capable of operating at more than one
        horizontal shift speed this function will return the actual speeds
        available. The value returned is in MHz.

        GetHSSpeed(int channel, int typ, int index, float* speed)

        :param typ: output amplification.
                    0 electron multiplication/Conventional(clara)
                    1 conventional/Extended NIR Mode(clara).
        :param index: speed required
                      0 to NumberSpeeds-1 where NumberSpeeds is value returned in
                      first parameter after a call to GetNumberHSSpeeds().
        :param ad: the AD channel.
        """

        if typ is None:
            typ = self.amp_typ

        speed = ct.c_float()

        self.lib.GetHSSpeed(ct.c_int(ad), ct.c_int(typ), ct.c_int(index),
                            ct.pointer(speed))

        return speed.value * MHz

    @Feat()
    def horiz_shift_speed(self):
        return self.horiz_shift_speed_index

    @horiz_shift_speed.setter
    def horiz_shift_speed(self, index):
        """This function will set the speed at which the pixels are shifted
        into the output node during the readout phase of an acquisition.
        Typically your camera will be capable of operating at several
        horizontal shift speeds. To get the actual speed that an index
        corresponds to use the GetHSSpeed function.

        :param typ: output amplification.
                    0 electron multiplication/Conventional(clara).
                    1 conventional/Extended NIR mode(clara).
        :param index: the horizontal speed to be used
                      0 to GetNumberHSSpeeds() - 1
        """
        ans = self.lib.SetHSSpeed(ct.c_int(self.amp_typ), ct.c_int(index))
        if ans == 20002:
            self.horiz_shift_speed_index = index

    @Feat()
    def fastest_recommended_vsspeed(self):
        """As your Andor SDK system may be capable of operating at more than
        one vertical shift speed this function will return the fastest
        recommended speed available. The very high readout speeds, may require
        an increase in the amplitude of the Vertical Clock Voltage using
        SetVSAmplitude. This function returns the fastest speed which does not
        require the Vertical Clock Voltage to be adjusted. The values returned
        are the vertical shift speed index and the actual speed in microseconds
        per pixel shift.
        """
        inti, f2 = ct.c_int(), ct.c_float()
        self.lib.GetFastestRecommendedVSSpeed(ct.pointer(inti), ct.pointer(f2))
        return (inti.value, f2.value)

    @Feat(read_once=True)
    def n_vert_clock_amps(self):
        """This function will normally return the number of vertical clock
        voltage amplitudes that the camera has.
        """
        n = ct.c_int()
        self.lib.GetNumberVSAmplitudes(ct.pointer(n))
        return n.value

    def vert_amp_index(self, string):
        """This Function is used to get the index of the Vertical Clock
        Amplitude that corresponds to the string passed in.

        :param string: "Normal" , "+1" , "+2" , "+3" , "+4"
        """
        index = ct.c_int()
        string = ct.c_char_p(str.encode(string))
        self.lib.GetVSAmplitudeFromString(string, ct.pointer(index))
        return index.value

    def vert_amp_string(self, index):
        """This Function is used to get the Vertical Clock Amplitude string
        that corresponds to the index passed in.

        :param index: Index of VS amplitude required
                      Valid values 0 to GetNumberVSAmplitudes() - 1
        """
        index = ct.c_int(index)
        string = (ct.c_char * 6)()
        self.lib.GetVSAmplitudeString(index, ct.pointer(string))
        return str(string.value)[2:-1]

    def true_vert_amp(self, index):
        """This Function is used to get the value of the Vertical Clock
        Amplitude found at the index passed in.

        :param index: Index of VS amplitude required
                      Valid values 0 to GetNumberVSAmplitudes() - 1
        """
        index = ct.c_int(index)
        amp = ct.c_int()
        self.lib.GetVSAmplitudeValue(index, ct.pointer(amp))
        return amp.value

    @Action()
    def set_vert_clock(self, index):
        """If you choose a high readout speed (a low readout time), then you
        should also consider increasing the amplitude of the Vertical Clock
        Voltage.
        There are five levels of amplitude available for you to choose from:
        - Normal, +1, +2, +3, +4
        Exercise caution when increasing the amplitude of the vertical clock
        voltage, since higher clocking voltages may result in increased
        clock-induced charge (noise) in your signal. In general, only the very
        highest vertical clocking speeds are likely to benefit from an
        increased vertical clock voltage amplitude.
        """
        self.lib.SetVSAmplitude(ct.c_int(index))

    @Feat(read_once=True)
    def n_vert_shift_speeds(self):
        """As your Andor system may be capable of operating at more than one
        vertical shift speed this function will return the actual number of
        speeds available.
        """
        n = ct.c_int()
        self.lib.GetNumberVSSpeeds(ct.pointer(n))
        return n.value

    def true_vert_shift_speed(self, index=0):
        """As your Andor SDK system may be capable of operating at more than
        one vertical shift speed this function will return the actual speeds
        available. The value returned is in microseconds.
        """
        speed = ct.c_float()
        self.lib.GetVSSpeed(ct.c_int(index), ct.pointer(speed))
        return speed.value * us

    @Feat()
    def vert_shift_speed(self):
        return self.vert_shift_speed_index

    @vert_shift_speed.setter
    def vert_shift_speed(self, index):
        """This function will set the vertical speed to be used for subsequent
        acquisitions.
        """
        self.vert_shift_speed_index = index
        self.lib.SetVSSpeed(ct.c_int(index))

    ### BASELINE

    @Feat(values={True: 1, False: 0})
    def baseline_clamp(self):
        """This function returns the status of the baseline clamp
        functionality. With this feature enabled the baseline level of each
        scan in a kinetic series will be more consistent across the sequence.
        """
        i = ct.c_int()
        self.lib.GetBaselineClamp(ct.pointer(i))
        return i.value

    @baseline_clamp.setter
    def baseline_clamp(self, value):
        value = ct.c_int(value)
        self.lib.SetBaselineClamp(value)

    @Feat(limits=(-1000, 1100, 100))
    def baseline_offset(self):
        """This function allows the user to move the baseline level by the
        amount selected. For example “+100” will add approximately 100 counts
        to the default baseline value. The value entered should be a multiple
        of 100 between -1000 and +1000 inclusively.
        """
        return self.baseline_offset_value

    @baseline_offset.setter
    def baseline_offset(self, value):
        ans = self.lib.SetBaselineOffset(ct.c_int(value))
        if ans == 20002:
            self.baseline_offset_value = value

    ### BIT DEPTH

    def bit_depth(self, ch):
        """This function will retrieve the size in bits of the dynamic range
        for any available AD channel.
        """
        ch = ct.c_int(ch)
        depth = ct.c_uint()
        self.lib.GetBitDepth(ch, ct.pointer(depth))
        return depth.value

    ### TRIGGER

    @Feat(values={True: 1, False: 0})
    def adv_trigger_mode(self):
        """This function will set the state for the iCam functionality that
        some cameras are capable of. There may be some cases where we wish to
        prevent the software using the new functionality and just do it the way
        it was previously done.
        """
        return self.adv_trigger_mode_state

    @adv_trigger_mode.setter
    def adv_trigger_mode(self, state):
        ans = self.lib.SetAdvancedTriggerModeState(ct.c_int(state))
        if ans == 20002:
            self.adv_trigger_mode_state = state

    def trigger_mode_available(self, modestr):
        """This function checks if the hardware and current settings permit
        the use of the specified trigger mode.
        """
        index = self.triggers[modestr]
        ans = self.lib.IsTriggerModeAvailable(ct.c_int(index))
        if ans == 20002:
            return True
        else:
            return False

    @Feat(values={'Internal': 0, 'External': 1, 'External Start': 6,
                  'External Exposure': 7, 'External FVB EM': 9,
                  'Software Trigger': 10, 'External Charge Shifting': 12})
    def trigger_mode(self):
        """This function will set the trigger mode that the camera will
        operate in.
        """
        return self.trigger_mode_index

    @trigger_mode.setter
    def trigger_mode(self, mode):
        ans = self.lib.SetTriggerMode(ct.c_int(mode))
        if ans == 20002:
            self.trigger_mode_index = mode

    @Action()
    def send_software_trigger(self):
        """This function sends an event to the camera to take an acquisition
        when in Software Trigger mode. Not all cameras have this mode available
        to them. To check if your camera can operate in this mode check the
        GetCapabilities function for the Trigger Mode
        AC_TRIGGERMODE_CONTINUOUS. If this mode is physically possible and
        other settings are suitable (IsTriggerModeAvailable) and the camera is
        acquiring then this command will take an acquisition.

        NOTES:
        The settings of the camera must be as follows:
        - ReadOut mode is full image
        - RunMode is Run Till Abort
        - TriggerMode is 10
        """
        self.lib.SendSoftwareTrigger()

    @Action()
    def trigger_level(self, value):
        """This function sets the trigger voltage which the system will use.
        """
        self.lib.SetTriggerLevel(ct.c_float(value))

    ### AUXPORT

    @DictFeat(values={True: not(0), False: 0}, keys=list(range(1, 5)))
    def in_aux_port(self, port):
        """This function returns the state of the TTL Auxiliary Input Port on
        the Andor plug-in card.
        """
        port = ct.c_int(port)
        state = ct.c_int()
        self.lib.InAuxPort(port, ct.pointer(state))
        return state.value

    @DictFeat(values={True: 1, False: 0}, keys=list(range(1, 5)))
    def out_aux_port(self, port):
        """This function sets the TTL Auxiliary Output port (P) on the Andor
        plug-in card to either ON/HIGH or OFF/LOW.
        """
        return self.auxout[port - 1]

    @out_aux_port.setter
    def out_aux_port(self, port, state):
        self.auxout[port - 1] = bool(state)
        port = ct.c_int(port)
        state = ct.c_int(state)
        self.lib.OutAuxPort(port, ct.pointer(state))

    def is_implemented(self, strcommand):
        """Checks if command is implemented.
        """
        result = ct.c_bool()
        command = ct.c_wchar_p(strcommand)
        self.lib.AT_IsImplemented(self.AT_H, command, ct.addressof(result))
        return result.value

    def is_writable(self, strcommand):
        """Checks if command is writable.
        """
        result = ct.c_bool()
        command = ct.c_wchar_p(strcommand)
        self.lib.AT_IsWritable(self.AT_H, command, ct.addressof(result))
        return result.value

    def queuebuffer(self, bufptr, value):
        """Put buffer in queue.
        """
        value = ct.c_int(value)
        self.lib.AT_QueueBuffer(self.AT_H, ct.byref(bufptr), value)

    def waitbuffer(self, ptr, bufsize):
        """Wait for next buffer ready.
        """
        timeout = ct.c_int(20000)
        self.lib.AT_WaitBuffer(self.AT_H, ct.byref(ptr), ct.byref(bufsize),
                               timeout)

    def command(self, strcommand):
        """Run command.
        """
        command = ct.c_wchar_p(strcommand)
        self.lib.AT_Command(self.AT_H, command)

    def getint(self, strcommand):
        """Run command and get Int return value.
        """
        result = ct.c_longlong()
        command = ct.c_wchar_p(strcommand)
        self.lib.AT_GetInt(self.AT_H, command, ct.addressof(result))
        return result.value

    def setint(self, strcommand, value):
        """SetInt function.
        """
        command = ct.c_wchar_p(strcommand)
        value = ct.c_longlong(value)
        self.lib.AT_SetInt(self.AT_H, command, value)

    def getfloat(self, strcommand):
        """Run command and get Int return value.
        """
        result = ct.c_double()
        command = ct.c_wchar_p(strcommand)
        self.lib.AT_GetFloat(self.AT_H, command, ct.addressof(result))
        return result.value

    def setfloat(self, strcommand, value):
        """Set command with Float value parameter.
        """
        command = ct.c_wchar_p(strcommand)
        value = ct.c_double(value)
        self.lib.AT_SetFloat(self.AT_H, command, value)

    def getbool(self, strcommand):
        """Run command and get Bool return value.
        """
        result = ct.c_bool()
        command = ct.c_wchar_p(strcommand)
        self.lib.AT_GetBool(self.AT_H, command, ct.addressof(result))
        return result.value

    def setbool(self, strcommand, value):
        """Set command with Bool value parameter.
        """
        command = ct.c_wchar_p(strcommand)
        value = ct.c_bool(value)
        self.lib.AT_SetBool(self.AT_H, command, value)

    def getenumerated(self, strcommand):
        """Run command and set Enumerated return value.
        """
        result = ct.c_int()
        command = ct.c_wchar_p(strcommand)
        self.lib.AT_GetEnumerated(self.AT_H, command, ct.addressof(result))

    def setenumerated(self, strcommand, value):
        """Set command with Enumerated value parameter.
        """
        command = ct.c_wchar_p(strcommand)
        value = ct.c_bool(value)
        self.lib.AT_SetEnumerated(self.AT_H, command, value)

    def setenumstring(self, strcommand, item):
        """Set command with EnumeratedString value parameter.
        """
        command = ct.c_wchar_p(strcommand)
        item = ct.c_wchar_p(item)
        self.lib.AT_SetEnumString(self.AT_H, command, item)

    def flush(self):
        self.lib.AT_Flush(self.AT_H)

if __name__ == '__main__':
    from matplotlib import pyplot as plt
    from lantz import Q_
    import time

    degC = Q_(1, 'degC')
    us = Q_(1, 'us')
    MHz = Q_(1, 'MHz')
    s = Q_(1, 's')

    with CCD() as andor:

        print(andor.idn)
        andor.free_int_mem()

        # Acquisition settings
        andor.readout_mode = 'Image'
        andor.set_image()
#        andor.acquisition_mode = 'Single Scan'
        andor.acquisition_mode = 'Run till abort'
        andor.set_exposure_time(0.03 * s)
        andor.trigger_mode = 'Internal'
        andor.amp_typ = 0
        andor.horiz_shift_speed = 0
        andor.vert_shift_speed = 0
        andor.shutter(0, 0, 0, 0, 0)

#        # Temperature stabilization
#        andor.temperature_setpoint = -30 * degC
#        andor.cooler_on = True
#        stable = 'Temperature has stabilized at set point.'
#        print('Temperature set point =', andor.temperature_setpoint)
#        while andor.temperature_status != stable:
#            print("Current temperature:", np.round(andor.temperature, 1))
#            time.sleep(30)
#        print('Temperature has stabilized at set point')

        # Acquisition
        andor.start_acquisition()
        time.sleep(2)
        data = andor.most_recent_image(shape=andor.detector_shape)
        andor.abort_acquisition()

        plt.imshow(data, cmap='gray', interpolation='None')
        plt.colorbar()
        plt.show()

        print(data.min(), data.max(), data.mean())
