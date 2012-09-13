# -*- coding: utf-8 -*-
"""
    lantz.visalib
    ~~~~~~~~~~~~~

    Wraps Visa Library in a Python friendly way.


    This wrapper originated while porting pyvisa to Python 3 and therefore is
    heavily influenced by it. There are a few important differences:

    - There is no visa_library singleton object and the library path can
      be specified.

    - Similar functions for different data width (In8, In16, etc) have been
      grouped within the same function. The extended versions are also grouped.

    - VISA functions dealing with strings have been dropped as can be easily
      replaced by Python functions.

    - types, status codes, attributes, events and constants are defined within
      a class (not a module).

    - Prefixes in types (`vi`), status codes (`VI_`), attributes (`VI_ATTR`),
      events (`VI_EVENT`) and constants (`VI_`) have been dropped for clarity.
      As this constants are defined within a RichEnum class, prefixed names are
      still usable.


    :copyright: 2012 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

import os
import logging
import ctypes as ct
from ctypes.util import find_library
import warnings
import threading

from collections import namedtuple

logger = logging.getLogger('lantz.visalib')
logger.addHandler(logging.NullHandler())

if os.name == 'nt':
    LIBTYPE = ct.WinDLL
    FUNCTYPE = ct.WINFUNCTYPE
else:
    LIBTYPE = ct.CDLL
    FUNCTYPE = ct.CFUNCTYPE

#: Default library path, used when none is provided to VisaLibrary.
for library_path in ('visa', 'visa32'):
    LIBRARY_PATH = find_library(library_path)
    if LIBRARY_PATH is not None:
        break

#: Resource extended information
ResourceInfo = namedtuple('ResourceInfo', 'interface_type interface_board_number resource_class resource_name alias')


class RichEnum(type):
    """Type for rich enumerations.
    """

    def __new__(mcs, name, bases, dct):
        ndct = {}
        ntuple = dct.get('_TUPLE', None)
        for key, value in dct.items():
            if key.startswith('_'):
                continue
            if ntuple:
                if isinstance(value, tuple):
                    value = ntuple(key, *value)
                else:
                    value = ntuple(key, value)

                ndct[value.code] = value

            dct[key] = value

        obj = super().__new__(mcs, name, bases, dct)
        obj._codes = ndct
        obj.__new__ = None
        return obj

    def __getitem__(cls, key):
        if isinstance(key, str):
            return getattr(cls, key)

        if isinstance(key, int):
            return cls._codes[key]
        return cls.__dict__[key]

    def __getattr__(cls, item):
        if item.startswith('__'):
            raise AttributeError("'{}' object has no attribute '{}'".format(cls, item))

        if item.startswith(cls._PREFIX):
            item = item[len(cls._PREFIX):]

        if item[0].isdigit():
            item = '_' + item

        return getattr(cls, item)

    def __contains__(cls, item):
        return item in cls.doc


def _type_pair(ctypes_type):
    return ctypes_type, ct.POINTER(ctypes_type)


def _type_triplet(ctypes_type):
    return _type_pair(ctypes_type) + (ct.POINTER(ctypes_type),)


class Types(metaclass=RichEnum):
    """Enumeration of VISA types mapped to ctypes.
    """

    _PREFIX = 'Vi'

    UInt64, PUInt64, AUInt74    = _type_triplet(ct.c_ulonglong)
    Int64, PInt64, AInt74       = _type_triplet(ct.c_longlong)
    UInt32, PUInt32, AUInt32    = _type_triplet(ct.c_ulong)
    Int32, PInt32, AInt32       = _type_triplet(ct.c_long)
    UInt16, PUInt16, AUInt16    = _type_triplet(ct.c_ushort)
    Int16, PInt16, AInt16       = _type_triplet(ct.c_short)
    UInt8, PUInt8, AUInt8       = _type_triplet(ct.c_ubyte)
    Int8, PInt8, AInt8          = _type_triplet(ct.c_byte)
    Addr, PAddr, AAddr          = _type_triplet(ct.c_void_p)
    Char, PChar, AChar          = _type_triplet(ct.c_char)
    Byte, PByte, AByte          = _type_triplet(ct.c_ubyte)
    Boolean, PBoolean, ABoolean = _type_triplet(UInt16)
    Real32, PReal32, AReal32    = _type_triplet(ct.c_float)
    Real64, PReal64, AReal64    = _type_triplet(ct.c_double)

    class String(object):

        @classmethod
        def from_param(cls, obj):
            if isinstance(obj, str):
                return bytes(obj, 'ascii')
            return obj

    PString = String

    class AString(object):

        @classmethod
        def from_param(cls, obj):
            return ct.POINTER(obj)

    Buf = PBuf = String
    ABuf        = AString #ct.POINTER(Buf)

    Rsrc        = String
    PRsrc       = String
    ARsrc       = AString #ct.POINTER(Rsrc)

    Status, PStatus, AStatus    = _type_triplet(Int32)
    Version, PVersion, AVersion = _type_triplet(UInt32)
    Object, PObject, AObject    = _type_triplet(UInt32)
    Session, PSession, ASession = _type_triplet(Object)

    Attr        = UInt32
    ConstString = ct.POINTER(Char)

    AccessMode, PAccessMode = _type_pair(UInt32)
    BusAddress, PBusAddress = _type_pair(UInt32)

    BusSize     = UInt32

    AttrState, PAttrState   = _type_pair(UInt32)

    VAList      = ct.POINTER(ct.c_char)

    EventType, PEventType, AEventType = _type_triplet(UInt32)

    PAttr       = ct.POINTER(Attr)
    AAttr       = PAttr

    EventFilter = UInt32

    FindList, PFindList     = _type_pair(Object)
    Event, PEvent           = _type_pair(Object)
    KeyId, PKeyId           = String, AString
    JobId, PJobId           = _type_pair(UInt32)

    Hndlr = FUNCTYPE(Status, Session, EventType, Event, Addr)


class StatusCode(metaclass=RichEnum):
    """Enumeration of VISA status codes with their corresponding value and docstring.
    """

    _PREFIX = 'VI_'
    _TUPLE = namedtuple('Status', 'name code doc')

    ERROR_ABORT              = -0x4000ffd0, 'User abort occurred during transfer.'
    ERROR_ALLOC              = -0x4000ffc4, 'Insufficient system resources to perform necessary memory allocation.'
    ERROR_ASRL_FRAMING       = -0x4000ff95, 'A framing error occurred during transfer.'
    ERROR_ASRL_OVERRUN       = -0x4000ff94, 'An overrun error occurred during transfer. A character was not read from the hardware before the next character arrived.'
    ERROR_ASRL_PARITY        = -0x4000ff96, 'A parity error occurred during transfer.'
    ERROR_ATTR_READONLY      = -0x4000ffe1, 'The specified attribute is read-only.'
    ERROR_BERR               = -0x4000ffc8, 'Bus error occurred during transfer.'
    ERROR_CLOSING_FAILED     = -0x4000ffea, 'The VISA driver failed to properly close the session or object reference. This might be due to an error freeing internal or OS resources, a failed network connection, or a lower-level driver or OS error.'
    ERROR_CONN_LOST          = -0x4000ff5a, 'The connection for the given session has been lost.'
    ERROR_FILE_ACCESS        = -0x4000ff5f, 'An error occurred while trying to open the specified file. Possible reasons include an invalid path or lack of access rights.'
    ERROR_FILE_IO            = -0x4000ff5e, 'An error occurred while performing I/O on the specified file.'
    ERROR_HNDLR_NINSTALLED   = -0x4000ffd8, 'A handler was not installed.'
    ERROR_INP_PROT_VIOL      = -0x4000ffc9, 'Device reported an input protocol error during transfer.'
    ERROR_INTF_NUM_NCONFIG   = -0x4000ff5b, 'The interface type is valid but the specified interface number is not configured.'
    ERROR_INTR_PENDING       = -0x4000ff98, 'An interrupt is still pending from a previous call.'
    ERROR_INV_ACCESS_KEY     = -0x4000ffdf, 'The access key to the resource associated with the specified session is invalid.'
    ERROR_INV_ACC_MODE       = -0x4000ffed, 'Invalid access mode.'
    ERROR_INV_CONTEXT        = -0x4000ffd6, 'Specified event context is invalid.'
    ERROR_INV_DEGREE         = -0x4000ffe5, 'Specified degree is invalid.'
    ERROR_INV_EVENT          = -0x4000ffda, 'Specified event type is not supported by the resource.'
    ERROR_INV_EXPR           = -0x4000fff0, 'Invalid expression specified for search.'
    ERROR_INV_FMT            = -0x4000ffc1, 'A format specifier in the format string is invalid.'
    ERROR_INV_HNDLR_REF      = -0x4000ffd7, 'The given handler reference is either invalid or was not installed.'
    ERROR_INV_JOB_ID         = -0x4000ffe4, 'Specified job identifier is invalid.'
    ERROR_INV_LENGTH         = -0x4000ff7d, 'Invalid length specified.'
    ERROR_INV_LINE           = -0x4000ff60, 'The value specified by the line parameter is invalid.'
    ERROR_INV_LOCK_TYPE      = -0x4000ffe0, 'The specified type of lock is not supported by this resource.'
    ERROR_INV_MASK           = -0x4000ffc3, 'Invalid buffer mask specified.'
    ERROR_INV_MECH           = -0x4000ffd9, 'Invalid mechanism specified.'
    ERROR_INV_MODE           = -0x4000ff6f, 'Invalid mode specified.'
    ERROR_INV_OBJECT         = -0x4000fff2, 'The given session or object reference is invalid.'
    ERROR_INV_OFFSET         = -0x4000ffaf, 'Invalid offset specified.'
    ERROR_INV_PARAMETER      = -0x4000ff88, 'The value of some parameter (which parameter is not known) is invalid.'
    ERROR_INV_PROT           = -0x4000ff87, 'The protocol specified is invalid.'
    ERROR_INV_RSRC_NAME      = -0x4000ffee, 'Invalid resource reference specified. Parsing error.'
    ERROR_INV_SETUP          = -0x4000ffc6, 'Unable to start operation because setup is invalid (usually due to attributes being set to an inconsistent state).'
    ERROR_INV_SIZE           = -0x4000ff85, 'Invalid size of window specified.'
    ERROR_INV_SPACE          = -0x4000ffb2, 'Invalid address space specified.'
    ERROR_INV_WIDTH          = -0x4000ffae, 'Invalid access width specified.'
    ERROR_IN_PROGRESS        = -0x4000ffc7, 'Unable to queue the asynchronous operation because there is already an operation in progress.'
    ERROR_IO                 = -0x4000ffc2, 'Could not perform operation because of I/O error.'
    ERROR_LIBRARY_NFOUND     = -0x4000ff62, 'A code library required by VISA could not be located or loaded.'
    ERROR_LINE_IN_USE        = -0x4000ffbe, 'The specified trigger line is currently in use.'
    ERROR_MACHINE_NAVAIL     = -0x4000ff59, 'The remote machine does not exist or is not accepting any connections. If the NI-VISA server is installed and running on the remote machine, it may have an incompatible version or may be listening on a different port.'
    ERROR_MEM_NSHARED        = -0x4000ff63, 'The device does not export any memory.'
    ERROR_NCIC               = -0x4000ffa0, 'The interface associated with this session is not currently the controller in charge.'
    ERROR_NENABLED           = -0x4000ffd1, 'You must be enabled for events of the specified type in order to receive them.'
    ERROR_NIMPL_OPER         = -0x4000ff7f, 'The given operation is not implemented.'
    ERROR_NLISTENERS         = -0x4000ffa1, 'No listeners condition is detected (both NRFD and NDAC are deasserted).'
    ERROR_NPERMISSION        = -0x4000ff58, 'Access to the resource or remote machine is denied. This is due to lack of sufficient privileges for the current user or machine'
    ERROR_NSUP_ALIGN_OFFSET  = -0x4000ff90, 'The specified offset is not properly aligned for the access width of the operation.'
    ERROR_NSUP_ATTR          = -0x4000ffe3, 'The specified attribute is not defined or supported by the referenced object.'
    ERROR_NSUP_ATTR_STATE    = -0x4000ffe2, 'The specified state of the attribute is not valid, or is not supported as defined by the object.'
    ERROR_NSUP_FMT           = -0x4000ffbf, 'A format specifier in the format string is not supported.'
    ERROR_NSUP_INTR          = -0x4000ff61, 'The interface cannot generate an interrupt on the requested level or with the requested statusID value.'
    ERROR_NSUP_LINE          = -0x4000ff5d, 'One of the specified lines (trigSrc or trigDest) is not supported by this VISA implementation, or the combination of lines is not a valid mapping.'
    ERROR_NSUP_MECH          = -0x4000ff5c, 'The specified mechanism is not supported for the given event type.'
    ERROR_NSUP_MODE          = -0x4000ffba, 'The specified mode is not supported by this VISA implementation.'
    ERROR_NSUP_OFFSET        = -0x4000ffac, 'Specified offset is not accessible from this hardware.'
    ERROR_NSUP_OPER          = -0x4000ff99, 'The given session or object reference does not support this operation.'
    ERROR_NSUP_VAR_WIDTH     = -0x4000ffab, 'Cannot support source and destination widths that are different.'
    ERROR_NSUP_WIDTH         = -0x4000ff8a, 'Specified width is not supported by this hardware.'
    ERROR_NSYS_CNTLR         = -0x4000ff9f, 'The interface associated with this session is not the system controller.'
    ERROR_OUTP_PROT_VIOL     = -0x4000ffca, 'Device reported an output protocol error during transfer.'
    ERROR_QUEUE_ERROR        = -0x4000ffc5, 'Unable to queue the asynchronous operation (usually due to the I/O completion event not being enabled or insufficient space in the session\'s queue).'
    ERROR_QUEUE_OVERFLOW     = -0x4000ffd3, 'The event queue for the specified type has overflowed (usually due to previous events not having been closed).'
    ERROR_RAW_RD_PROT_VIOL   = -0x4000ffcb, 'Violation of raw read protocol occurred during transfer.'
    ERROR_RAW_WR_PROT_VIOL   = -0x4000ffcc, 'Violation of raw write protocol occurred during transfer.'
    ERROR_RESP_PENDING       = -0x4000ffa7, 'A previous response is still pending, causing a multiple query error.'
    ERROR_RSRC_BUSY          = -0x4000ff8e, 'The resource is valid, but VISA cannot currently access it.'
    ERROR_RSRC_LOCKED        = -0x4000fff1, 'Specified type of lock cannot be obtained, or specified operation cannot be performed, because the resource is locked.'
    ERROR_RSRC_NFOUND        = -0x4000ffef, 'Insufficient location information or the requested device or resource is not present in the system.'
    ERROR_SESN_NLOCKED       = -0x4000ff64, 'The current session did not have a lock on the resource.'
    ERROR_SRQ_NOCCURRED      = -0x4000ffb6, 'Service request has not been received for the session.'
    ERROR_SYSTEM_ERROR       = -0x40010000, 'Unknown system error (miscellaneous error).'
    ERROR_TMO                = -0x4000ffeb, 'Timeout expired before operation completed.'
    ERROR_TRIG_NMAPPED       = -0x4000ff92, 'The path from trigSrc to trigDest is not currently mapped.'
    ERROR_USER_BUF           = -0x4000ff8f, 'A specified user buffer is not valid or cannot be accessed for the required size.'
    ERROR_WINDOW_MAPPED      = -0x4000ff80, 'The specified session currently contains a mapped window.'
    ERROR_WINDOW_NMAPPED     = -0x4000ffa9, 'The specified session is not currently mapped.'
    SUCCESS                  = 0x0, 'Operation completed successfully.'
    SUCCESS_DEV_NPRESENT     = 0x3fff007d, 'Session opened successfully, but the device at the specified address is not responding.'
    SUCCESS_EVENT_DIS        = 0x3fff0003, 'Specified event is already disabled for at least one of the specified mechanisms.'
    SUCCESS_EVENT_EN         = 0x3fff0002, 'Specified event is already enabled for at least one of the specified mechanisms.'
    SUCCESS_MAX_CNT          = 0x3fff0006, 'The number of bytes transferred is equal to the requested input count. More data may be available.'
    SUCCESS_NCHAIN           = 0x3fff0098, 'Event handled successfully. Do not invoke any other handlers on this session for this event.'
    SUCCESS_NESTED_EXCLUSIVE = 0x3fff009a, 'Operation completed successfully, and this session has nested exclusive locks.'
    SUCCESS_NESTED_SHARED    = 0x3fff0099, 'Operation completed successfully, and this session has nested shared locks.'
    SUCCESS_QUEUE_EMPTY      = 0x3fff0004, 'Operation completed successfully, but queue was already empty.'
    SUCCESS_QUEUE_NEMPTY     = 0x3fff0080, 'Wait terminated successfully on receipt of an event notification. There is at least one more event object of the requested type(s) available for this session.'
    SUCCESS_SYNC             = 0x3fff009b, 'Operation completed successfully, but the operation was actually synchronous rather than asynchronous.'
    SUCCESS_TERM_CHAR        = 0x3fff0005, 'The specified termination character was read.'
    SUCCESS_TRIG_MAPPED      = 0x3fff007e, 'The path from trigSrc to trigDest is already mapped.'
    WARN_CONFIG_NLOADED      = 0x3fff0077, 'The specified configuration either does not exist or could not be loaded. VISA-specified defaults will be used.'
    WARN_EXT_FUNC_NIMPL      = 0x3fff00a9, 'The operation succeeded, but a lower level driver did not implement the extended functionality.'
    WARN_NSUP_ATTR_STATE     = 0x3fff0084, 'Although the specified state of the attribute is valid, it is not supported by this implementation.'
    WARN_NSUP_BUF            = 0x3fff0088, 'The specified I/O buffer type is not supported.'
    WARN_NULL_OBJECT         = 0x3fff0082, 'The specified object reference is uninitialized.'
    WARN_QUEUE_OVERFLOW      = 0x3fff000c, 'VISA received more event information of the specified type than the configured queue size could hold.'
    WARN_UNKNOWN_STATUS      = 0x3fff0085, 'The status code passed to the operation could not be interpreted.'


class Attributes(metaclass=RichEnum):
    """Enumeration of VISA Attributes with their corresponding value, VISA TYPE and docstring
    """

    _PREFIX = 'VI_ATTR'
    _TUPLE = namedtuple('Attribute', 'name code ctype doc')

    _4882_COMPLIANT          = 0x3fff019f, Types.Boolean, ''
    #ASRL_ALLOW_TRANSMIT      = XXXX, Types.Boolean, ''
    ASRL_AVAIL_NUM           = 0x3fff00ac, Types.UInt32, ''
    ASRL_BAUD                = 0x3fff0021, Types.UInt32, ''
    #VI_ATTR_ASRL_BREAK_LEN   = XXXX, Types.Int16, ''
    #VI_ATTR_ASRL_BREAK_STATE = XXXX, Types.Int16, ''
    #VI_ATTR_ASRL_CONNECTED   = XXXX, Types.Boolean, ''
    ASRL_CTS_STATE           = 0x3fff00ae, Types.Int16, ''
    ASRL_DATA_BITS           = 0x3fff0022, Types.UInt16, ''
    ASRL_DCD_STATE           = 0x3fff00af, Types.Int16, ''
    #VI_ATTR_ASRL_DISCARD_NULL = XXX, Types.Boolean, ''
    ASRL_DSR_STATE           = 0x3fff00b1, Types.Int16, ''
    ASRL_DTR_STATE           = 0x3fff00b2, Types.Int16, ''
    ASRL_END_IN              = 0x3fff00b3, Types.UInt16, ''
    ASRL_END_OUT             = 0x3fff00b4, Types.UInt16, ''
    ASRL_FLOW_CNTRL          = 0x3fff0025, Types.UInt16, ''
    ASRL_PARITY              = 0x3fff0023, Types.UInt16, ''
    ASRL_REPLACE_CHAR        = 0x3fff00be, Types.UInt8, ''
    ASRL_RI_STATE            = 0x3fff00bf, Types.Int16, ''
    ASRL_RTS_STATE           = 0x3fff00c0, Types.Int16, ''
    ASRL_STOP_BITS           = 0x3fff0024, Types.UInt16, ''
    #VI_ATTR_ASRL_WIRE_MODE   = XXX, Types.Int16, ''
    ASRL_XOFF_CHAR           = 0x3fff00c2, Types.UInt8, ''
    ASRL_XON_CHAR            = 0x3fff00c1, Types.UInt8, ''
    BUFFER                   = 0x3fff4027, Types.Buf, ''
    CMDR_LA                  = 0x3fff006b, Types.Int16, ''
    DEST_ACCESS_PRIV         = 0x3fff0039, Types.UInt16, ''
    DEST_BYTE_ORDER          = 0x3fff003a, Types.UInt16, ''
    DEST_INCREMENT           = 0x3fff0041, Types.Int32, ''
    DEV_STATUS_BYTE          = 0x3fff0189, Types.UInt8, ''
    DMA_ALLOW_EN             = 0x3fff001e, Types.Boolean, ''
    EVENT_TYPE               = 0x3fff4010, Types.EventType, ''
    FDC_CHNL                 = 0x3fff000d, Types.UInt16, ''
    #FDC_GEN_SIGNAL_EN        = 0x3fff0011, None, ''
    FDC_MODE                 = 0x3fff000f, Types.UInt16, ''
    FDC_USE_PAIR             = 0x3fff0013, Types.Boolean, ''
    FILE_APPEND_EN           = 0x3fff0192, Types.Boolean, ''
    GPIB_ADDR_STATE          = 0x3fff005c, Types.Int16, ''
    GPIB_ATN_STATE           = 0x3fff0057, Types.Int16, ''
    GPIB_CIC_STATE           = 0x3fff005e, Types.Boolean, ''
    GPIB_HS488_CBL_LEN       = 0x3fff0069, Types.Int16, ''
    GPIB_NDAC_STATE          = 0x3fff0062, Types.Int16, ''
    GPIB_PRIMARY_ADDR        = 0x3fff0172, Types.UInt16, ''
    GPIB_READDR_EN           = 0x3fff001b, Types.Boolean, ''
    GPIB_RECV_CIC_STATE      = 0x3fff4193, Types.Boolean, ''
    GPIB_REN_STATE           = 0x3fff0181, Types.Int16, ''
    GPIB_SECONDARY_ADDR      = 0x3fff0173, Types.UInt16, ''
    GPIB_SRQ_STATE           = 0x3fff0067, Types.Int16, ''
    GPIB_SYS_CNTRL_STATE     = 0x3fff0068, Types.Boolean, ''
    GPIB_UNADDR_EN           = 0x3fff0184, Types.Boolean, ''
    IMMEDIATE_SERV           = 0x3fff0100, Types.Boolean, ''
    INTF_INST_NAME           = 0xbfff00e9, Types.String, ''
    INTF_NUM                 = 0x3fff0176, Types.UInt16, ''
    #INTF_PARENT_NUM          = 0x3fff0101, ct.c_ushort, ''
    INTF_TYPE                = 0x3fff0171, Types.UInt16, ''
    INTR_STATUS_ID           = 0x3fff4023, Types.UInt32, ''
    IO_PROT                  = 0x3fff001c, Types.UInt32, ''
    JOB_ID                   = 0x3fff4006, Types.JobId, ''
    MAINFRAME_LA             = 0x3fff0070, Types.Int16, ''
    MANF_ID                  = 0x3fff00d9, Types.UInt16, ''
    MANF_NAME                = 0xbfff0072, Types.UInt16, ''
    MAX_QUEUE_LENGTH         = 0x3fff0005, Types.UInt32, ''
    MEM_BASE                 = 0x3fff00ad, Types.BusAddress, ''
    #MEM_BASE_32              = XXXX, Types.UInt32, ''
    #MEM_BASE_64              = XXXX, Types.UInt64, ''
    MEM_SIZE                 = 0x3fff00dd, Types.BusSize, ''
    #MEM_SIZE_32              = XXXX, Types.UInt32, ''
    #MEM_SIZE_64              = XXXX, Types.UInt64, ''
    MEM_SPACE                = 0x3fff00de, Types.UInt16, ''
    MODEL_CODE               = 0x3fff00df, Types.UInt16, ''
    MODEL_NAME               = 0xbfff0077, Types.String, ''
    OPER_NAME                = 0xbfff4042, Types.String, ''
    #PXI MISSING
    RD_BUF_OPER_MODE         = 0x3fff002a, Types.UInt16, ''
    RD_BUF_SIZE              = 0x3fff002b, Types.UInt32, ''
    RECV_INTR_LEVEL          = 0x3fff4041, Types.Int16, ''
    #RECV_TCPIP_ADDR          = 0xbfff4198, None, ''
    RECV_TRIG_ID             = 0x3fff4012, Types.Int16, ''
    RET_COUNT                = 0x3fff4026, Types.UInt64 or Types.UInt64, ''
    #RET_COUNT_32             = XXX, Types.UInt32, ''
    #RET_COUNT_64             = XXX, Types.UInt64, ''
    RM_SESSION               = 0x3fff00c4, Types.Session, ''
    RSRC_CLASS               = 0xbfff0001, Types.String, ''
    RSRC_IMPL_VERSION        = 0x3fff0003, Types.Version, ''
    RSRC_LOCK_STATE          = 0x3fff0004, Types.AccessMode, ''
    RSRC_MANF_ID             = 0x3fff0175, Types.UInt16, ''
    RSRC_MANF_NAME           = 0xbfff0174, Types.String, ''
    RSRC_NAME                = 0xbfff0002, Types.Rsrc, ''
    RSRC_SPEC_VERSION        = 0x3fff0170, Types.Version, ''
    SEND_END_EN              = 0x3fff0016, Types.Boolean, ''
    SIGP_STATUS_ID           = 0x3fff4011, Types.UInt16, ''
    SLOT                     = 0x3fff00e8, Types.Int16, ''
    SRC_ACCESS_PRIV          = 0x3fff003c, Types.UInt16, ''
    SRC_BYTE_ORDER           = 0x3fff003d, Types.UInt16, ''
    SRC_INCREMENT            = 0x3fff0040, Types.Int32, ''
    STATUS                   = 0x3fff4025, Types.Status, ''
    SUPPRESS_END_EN          = 0x3fff0036, Types.Status, ''
    TCPIP_ADDR               = 0xbfff0195, Types.String, ''
    TCPIP_DEVICE_NAME        = 0xbfff0199, Types.String, ''
    TCPIP_HOSTNAME           = 0xbfff0196, Types.String, ''
    TCPIP_KEEPALIVE          = 0x3fff019b, Types.Boolean, ''
    TCPIP_NODELAY            = 0x3fff019a, Types.Boolean, ''
    TCPIP_PORT               = 0x3fff0197, Types.UInt16, ''
    TERMCHAR                 = 0x3fff0018, Types.UInt8, ''
    TERMCHAR_EN              = 0x3fff0038, Types.Boolean, ''
    TMO_VALUE                = 0x3fff001a, Types.UInt32, ''
    TRIG_ID                  = 0x3fff0177, Types.Int16, ''
    #MIssing some USB interleaved
    USB_INTFC_NUM            = 0x3fff01a1, Types.Int16, ''
    USB_MAX_INTR_SIZE        = 0x3fff01af, Types.UInt16, ''
    USB_PROTOCOL             = 0x3fff01a7, Types.Int16, ''
    USB_RECV_INTR_DATA       = 0xbfff41b1, Types.AUInt8, ''
    USB_RECV_INTR_SIZE       = 0x3fff41b0, Types.UInt16, ''
    USB_SERIAL_NUM           = 0xbfff01a0, Types.String, ''
    USER_DATA                = 0x3fff0007, Types.Addr, ''
    #USER_DATA_32             = XXXX, Types.UInt32, ''
    #USER_DATA_64             = XXX, Types.UInt64, ''
    # Missing VXI interleaved
    VXI_DEV_CLASS            = 0x3fff006c, Types.UInt16, ''
    VXI_LA                   = 0x3fff00d5, Types.Int16, ''
    VXI_TRIG_STATUS          = 0x3fff008d, Types.UInt32, ''
    VXI_TRIG_SUPPORT         = 0x3fff0194, Types.UInt32, ''
    VXI_VME_INTR_STATUS      = 0x3fff008b, Types.UInt16, ''
    VXI_VME_SYSFAIL_STATE    = 0x3fff0094, Types.Int16, ''
    WIN_ACCESS               = 0x3fff00c3, Types.UInt16, ''
    WIN_ACCESS_PRIV          = 0x3fff0045, Types.UInt16, ''
    WIN_BASE_ADDR            = 0x3fff0098, Types.BusAddress, ''
    #WIN_BASE_ADDR_32         = XXXX, Types.UInt32, ''
    #WIN_BASE_ADDR_64         = XXXX, Types.UInt64, ''
    WIN_BYTE_ORDER           = 0x3fff0047, Types.UInt16, ''
    WIN_SIZE                 = 0x3fff009a, Types.BusSize, ''
    #WIN_SIZE_32              = XXXx, Types.UInt32, ''
    #WIN_SIZE_64              = XXXx, Types.UInt64, ''
    WR_BUF_OPER_MODE         = 0x3fff002d, Types.UInt16, ''
    WR_BUF_SIZE              = 0x3fff002e, Types.UInt32, ''


class Events(metaclass=RichEnum):
    """Enumeration of VISA Events with their corresponding value and docstring
    """

    _PREFIX = 'VI_EVENT'
    _TUPLE = namedtuple('Attribute', 'name code doc')

    IO_COMPLETION    = 0x3FFF2009, 'This event notifies the application that an asynchronous operation has completed.'
    TRIG             = 0xBFFF200A, 'This event notifies the application that a trigger interrupt was received from the device.'
    SERVICE_REQ      = 0x3FFF200B, 'This event notifies the application that a service request was received from the device or interface associated with the given session.'
    CLEAR            = 0x3FFF200D, ''
    EXCEPTION        = 0xBFFF200E, 'This event notifies the application that an error condition has occurred during an operation invocation.'
    GPIB_CIC         = 0x3FFF2012, 'Notification that the GPIB controller has gained or lost CIC (controller in charge) status.'
    GPIB_TALK        = 0x3FFF2013, 'Notification that the GPIB controller has been addressed to talk.'
    GPIB_LISTEN      = 0x3FFF2014, 'Notification that the GPIB controller has been addressed to listen.'
    VXI_VME_SYSFAIL  = 0x3FFF201D, 'Notification that the VXI/VME SYSFAIL* line has been asserted.'
    VXI_VME_SYSRESET = 0x3FFF201E, 'Notification that the VXI/VME SYSRESET* line has been asserted.'
    VXI_SIGP         = 0x3FFF2020, ''
    VXI_VME_INTR     = 0xBFFF2021, 'This event notifies the application that a VXIbus interrupt was received from the device associated with the given session.'
    TCPIP_CONNECT    = 0x3FFF2036, 'This event notifies the application that a VXIbus signal or VXIbus interrupt was received from the device associated with the given session.'
    USB_INTR         = 0x3FFF2037, 'This event notifies that a USB interrupt has occurred.'

    ALL_ENABLED_EVENTS = 0x3FFF7FFF, ''


class Constants(metaclass=RichEnum):
    """Enumeration of VISA Constants with their corresponding value and docstring
    """

    _PREFIX = 'VI_'

    FIND_BUFLEN               = 256
    NULL                      = 0

    TRUE                      = 1
    FALSE                     = 0

    INTF_GPIB                 = 1
    INTF_VXI                  = 2
    INTF_GPIB_VXI             = 3
    INTF_ASRL                 = 4
    INTF_TCPIP                = 6
    INTF_USB                  = 7

    PROT_NORMAL               = 1
    PROT_FDC                  = 2
    PROT_HS488                = 3
    PROT_4882_STRS            = 4
    PROT_USBTMC_VENDOR        = 5

    FDC_NORMAL                = 1
    FDC_STREAM                = 2

    LOCAL_SPACE               = 0
    A16_SPACE                 = 1
    A24_SPACE                 = 2
    A32_SPACE                 = 3
    OPAQUE_SPACE              = 0xFFFF

    UNKNOWN_LA                = -1
    UNKNOWN_SLOT              = -1
    UNKNOWN_LEVEL             = -1

    QUEUE                     = 1
    HNDLR                     = 2
    SUSPEND_HNDLR             = 4
    ALL_MECH                  = 0xFFFF

    ANY_HNDLR                 = 0

    TRIG_ALL                  = -2
    TRIG_SW                   = -1
    TRIG_TTL0                 = 0
    TRIG_TTL1                 = 1
    TRIG_TTL2                 = 2
    TRIG_TTL3                 = 3
    TRIG_TTL4                 = 4
    TRIG_TTL5                 = 5
    TRIG_TTL6                 = 6
    TRIG_TTL7                 = 7
    TRIG_ECL0                 = 8
    TRIG_ECL1                 = 9
    TRIG_PANEL_IN             = 27
    TRIG_PANEL_OUT            = 28

    TRIG_PROT_DEFAULT         = 0
    TRIG_PROT_ON              = 1
    TRIG_PROT_OFF             = 2
    TRIG_PROT_SYNC            = 5

    READ_BUF                  = 1
    WRITE_BUF                 = 2
    READ_BUF_DISCARD          = 4
    WRITE_BUF_DISCARD         = 8
    IO_IN_BUF                 = 16
    IO_OUT_BUF                = 32
    IO_IN_BUF_DISCARD         = 64
    IO_OUT_BUF_DISCARD        = 128

    FLUSH_ON_ACCESS           = 1
    FLUSH_WHEN_FULL           = 2
    FLUSH_DISABLE             = 3

    NMAPPED                   = 1
    USE_OPERS                 = 2
    DEREF_ADDR                = 3

    TMO_IMMEDIATE             = 0
    TMO_INFINITE              = 0xFFFFFFFF

    NO_LOCK                   = 0
    EXCLUSIVE_LOCK            = 1
    SHARED_LOCK               = 2
    LOAD_CONFIG               = 4

    NO_SEC_ADDR               = 0xFFFF

    ASRL_PAR_NONE             = 0
    ASRL_PAR_ODD              = 1
    ASRL_PAR_EVEN             = 2
    ASRL_PAR_MARK             = 3
    ASRL_PAR_SPACE            = 4

    ASRL_STOP_ONE             = 10
    ASRL_STOP_ONE5            = 15
    ASRL_STOP_TWO             = 20

    ASRL_FLOW_NONE            = 0
    ASRL_FLOW_XON_XOFF        = 1
    ASRL_FLOW_RTS_CTS         = 2
    ASRL_FLOW_DTR_DSR         = 4

    ASRL_END_NONE             = 0
    ASRL_END_LAST_BIT         = 1
    ASRL_END_TERMCHAR         = 2
    ASRL_END_BREAK            = 3

    STATE_ASSERTED            = 1
    STATE_UNASSERTED          = 0
    STATE_UNKNOWN             = -1

    BIG_ENDIAN                = 0
    LITTLE_ENDIAN             = 1

    DATA_PRIV                 = 0
    DATA_NPRIV                = 1
    PROG_PRIV                 = 2
    PROG_NPRIV                = 3
    BLCK_PRIV                 = 4
    BLCK_NPRIV                = 5
    D64_PRIV                  = 6
    D64_NPRIV                 = 7

    WIDTH_8                   = 1
    WIDTH_16                  = 2
    WIDTH_32                  = 4

    GPIB_REN_DEASSERT         = 0
    GPIB_REN_ASSERT           = 1
    GPIB_REN_DEASSERT_GTL     = 2
    GPIB_REN_ASSERT_ADDRESS   = 3
    GPIB_REN_ASSERT_LLO       = 4
    GPIB_REN_ASSERT_ADDRESS_LLO = 5
    GPIB_REN_ADDRESS_GTL      = 6

    GPIB_ATN_DEASSERT         = 0
    GPIB_ATN_ASSERT           = 1
    GPIB_ATN_DEASSERT_HANDSHAKE = 2
    GPIB_ATN_ASSERT_IMMEDIATE = 3

    GPIB_HS488_DISABLED       = 0
    GPIB_HS488_NIMPL          = -1

    GPIB_UNADDRESSED          = 0
    GPIB_TALKER               = 1
    GPIB_LISTENER             = 2

    VXI_CMD16                 = 0x0200
    VXI_CMD16_RESP16          = 0x0202
    VXI_RESP16                = 0x0002
    VXI_CMD32                 = 0x0400
    VXI_CMD32_RESP16          = 0x0402
    VXI_CMD32_RESP32          = 0x0404
    VXI_RESP32                = 0x0004

    ASSERT_SIGNAL             = -1
    ASSERT_USE_ASSIGNED       = 0
    ASSERT_IRQ1               = 1
    ASSERT_IRQ2               = 2
    ASSERT_IRQ3               = 3
    ASSERT_IRQ4               = 4
    ASSERT_IRQ5               = 5
    ASSERT_IRQ6               = 6
    ASSERT_IRQ7               = 7

    UTIL_ASSERT_SYSRESET      = 1
    UTIL_ASSERT_SYSFAIL       = 2
    UTIL_DEASSERT_SYSFAIL     = 3

    VXI_CLASS_MEMORY          = 0
    VXI_CLASS_EXTENDED        = 1
    VXI_CLASS_MESSAGE         = 2
    VXI_CLASS_REGISTER        = 3
    VXI_CLASS_OTHER           = 4


class VisaLibrary(object):
    """VISA Library wrapper.

    :param library_path: full path of the library. If not given, the default value LIBRARY_PATH it is used.
    """

    #: Holds a mapping between library_path and VisaLibrary objects
    REGISTER = {}

    def __new__(cls, library_path=LIBRARY_PATH):
        if library_path in cls.REGISTER:
            return cls.REGISTER[library_path]

        obj = cls.REGISTER.setdefault(library_path, super().__new__(cls))

        obj.library_path = library_path
        obj.session = None
        obj.status = 0

        obj.lib = LIBTYPE(library_path)
            
        obj.lock = threading.RLock()

        obj._add_types()

        s = StatusCode

        obj.issue_warning_on = [s.SUCCESS_MAX_CNT, s.SUCCESS_DEV_NPRESENT, s.SUCCESS_SYNC,
                                s.WARN_QUEUE_OVERFLOW, s.WARN_CONFIG_NLOADED, s.WARN_NULL_OBJECT,
                                s.WARN_NSUP_ATTR_STATE, s.WARN_UNKNOWN_STATUS, s.WARN_NSUP_BUF, s.WARN_EXT_FUNC_NIMPL]

        #: Contains all installed event handlers.
        #: Its elements are tuples with three elements: The handler itself (a Python
        #: callable), the user handle (as a ct object) and the handler again, this
        #: time as a ct object created with CFUNCTYPE.
        obj.handlers = []
        return obj


    def _return_handler(self, ret_value):
        """Check return values for errors and warnings.
        """

        self.status = ret_value

        if ret_value < 0:
            try:
                err = StatusCode[ret_value]
            except:
                raise Exception('Unknown Error: {}'.format(ret_value))

            raise Exception('{0.doc} ({0.name}: {0.code})'.format(err))

        if ret_value in self.issue_warning_on:
            status = StatusCode[ret_value]
            warnings.warn("{:.name}: {:.doc}".format(status), warnings.WarningMessage, stacklevel=2)

        return ret_value

    def _add_types(self):
        """Add argument types and return type to functions in the library.
        """

        fun = self._set_function_types
        T = Types

        fun("viAssertIntrSignal", [T.Session, T.Int16, T.UInt32])
        fun("viAssertTrigger", [T.Session, T.UInt16])
        fun("viAssertUtilSignal", [T.Session, T.UInt16])
        fun("viBufRead", [T.Session, T.PBuf, T.UInt32, T.PUInt32])
        fun("viBufWrite", [T.Session, T.Buf, T.UInt32, T.PUInt32])
        fun("viClear", [T.Session])
        fun("viClose", [T.Object])
        fun("viDisableEvent", [T.Session, T.EventType, T.UInt16])
        fun("viDiscardEvents", [T.Session, T.EventType, T.UInt16])
        fun("viEnableEvent", [T.Session, T.EventType, T.UInt16, T.EventFilter])
        fun("viFindNext", [T.Session, T.AChar])
        fun("viFindRsrc", [T.Session, T.String, T.PFindList, T.PUInt32, T.AChar])
        fun("viFlush", [T.Session, T.UInt16])
        fun("viGetAttribute", [T.Object, T.Attr, ct.c_void_p])
        fun("viGpibCommand", [T.Session, T.Buf, T.UInt32, T.PUInt32])
        fun("viGpibControlATN", [T.Session, T.UInt16])
        fun("viGpibControlREN", [T.Session, T.UInt16])
        fun("viGpibPassControl", [T.Session, T.UInt16, T.UInt16])
        fun("viGpibSendIFC", [T.Session])
        fun("viIn8", [T.Session, T.UInt16, T.BusAddress, T.PUInt8])
        fun("viIn16", [T.Session, T.UInt16, T.BusAddress, T.PUInt16])
        fun("viIn32", [T.Session, T.UInt16, T.BusAddress, T.PUInt32])
        fun("viInstallHandler", [T.Session, T.EventType, T.Hndlr, T.Addr])
        fun("viLock", [T.Session, T.AccessMode, T.UInt32, T.KeyId, T.AChar])
        fun("viMapAddress", [T.Session, T.UInt16, T.BusAddress, T.BusSize, T.Boolean, T.Addr, T.PAddr])
        fun("viMapTrigger", [T.Session, T.Int16, T.Int16, T.UInt16])
        fun("viMemAlloc", [T.Session, T.BusSize, T.PBusAddress])
        fun("viMemFree", [T.Session, T.BusAddress])
        fun("viMove", [T.Session, T.UInt16, T.BusAddress, T.UInt16, T.UInt16, T.BusAddress, T.UInt16, T.BusSize])
        fun("viMoveAsync", [T.Session, T.UInt16, T.BusAddress, T.UInt16, T.UInt16, T.BusAddress, T.UInt16, T.BusSize, T.PJobId])
        fun("viMoveIn8", [T.Session, T.UInt16, T.BusAddress, T.BusSize, T.AUInt8])
        fun("viMoveIn16", [T.Session, T.UInt16, T.BusAddress, T.BusSize, T.AUInt16])
        fun("viMoveIn32", [T.Session, T.UInt16, T.BusAddress, T.BusSize, T.AUInt32])
        fun("viMoveOut8", [T.Session, T.UInt16, T.BusAddress, T.BusSize, T.AUInt8])
        fun("viMoveOut16", [T.Session, T.UInt16, T.BusAddress, T.BusSize, T.AUInt16])
        fun("viMoveOut32", [T.Session, T.UInt16, T.BusAddress, T.BusSize, T.AUInt32])
        fun("viOpen", [T.Session, T.Rsrc, T.AccessMode, T.UInt32, T.PSession], may_be_missing=False)
        fun("viOpenDefaultRM", [T.PSession])
        fun("viOut8", [T.Session, T.UInt16, T.BusAddress, T.UInt8])
        fun("viOut16", [T.Session, T.UInt16, T.BusAddress, T.UInt16])
        fun("viOut32", [T.Session, T.UInt16, T.BusAddress, T.UInt32])
        fun("viParseRsrc", [T.Session, T.Rsrc, T.PUInt16, T.PUInt16])
        fun("viParseRsrcEx", [T.Session, T.Rsrc, T.PUInt16, T.PUInt16, T.AChar, T.AChar, T.AChar])
        fun("viPeek8", [T.Session, T.Addr, T.PUInt8], restype=None)
        fun("viPeek16", [T.Session, T.Addr, T.PUInt16], restype=None)
        fun("viPeek32", [T.Session, T.Addr, T.PUInt32], restype=None)
        fun("viPoke8", [T.Session, T.Addr, T.UInt8], restype=None)
        fun("viPoke16", [T.Session, T.Addr, T.UInt16], restype=None)
        fun("viPoke32", [T.Session, T.Addr, T.UInt32], restype=None)
        fun("viRead", [T.Session, T.PBuf, T.UInt32, T.PUInt32])
        fun("viReadAsync", [T.Session, T.PBuf, T.UInt32, T.PJobId])
        fun("viReadSTB", [T.Session, T.PUInt16])
        fun("viReadToFile", [T.Session, T.String, T.UInt32, T.PUInt32])
        fun("viSetAttribute", [T.Object, T.Attr, T.AttrState])
        fun("viSetBuf", [T.Session, T.UInt16, T.UInt32])
        fun("viStatusDesc", [T.Object, T.Status, T.AChar])
        fun("viTerminate", [T.Session, T.UInt16, T.JobId])
        fun("viUninstallHandler", [T.Session, T.EventType, T.Hndlr, T.Addr])
        fun("viUnlock", [T.Session])
        fun("viUnmapAddress", [T.Session])
        fun("viUnmapTrigger", [T.Session, T.Int16, T.Int16])
        fun("viUsbControlIn", [T.Session, T.Int16, T.Int16, T.UInt16, T.UInt16, T.UInt16, T.PBuf, T.PUInt16])
        fun("viUsbControlOut", [T.Session, T.Int16, T.Int16, T.UInt16, T.UInt16, T.UInt16, T.PBuf])
        fun("viVxiCommandQuery", [T.Session, T.UInt16, T.UInt32, T.PUInt32])
        fun("viWaitOnEvent", [T.Session, T.EventType, T.UInt32, T.PEventType, T.PEvent])
        fun("viWrite", [T.Session, T.Buf, T.UInt32, T.PUInt32])
        fun("viWriteAsync", [T.Session, T.Buf, T.UInt32, T.PJobId])
        fun("viWriteFromFile", [T.Session, T.String, T.UInt32, T.PUInt32])

    def _set_function_types(self, visa_function, types, may_be_missing=True, restype=True):
        """Set argument and return type in library functions

        :param visa_function: name of the function.
        :param types: list with argument types.
        :param may_be_missing: if False, will raise an Exception if the function is not found.
        :param restype: if True, _return_handler will be set as return type
        """
        try:
            fun = getattr(self.lib, visa_function)
        except AttributeError:
            if not may_be_missing:
                raise
            return

        fun.argtypes = types
        if restype:
            fun.restype = self._return_handler

    def set_user_handle_type(self, user_handle):
        if user_handle is None:
            user_handle_p = ct.c_void_p
        else:
            user_handle_p = ct.POINTER(type(user_handle))

        Types.Hndlr = FUNCTYPE(Types.Status, Types.Session, Types.EventType, Types.Event, user_handle_p)
        self.lib.internal.viInstallHandler.argtypes = [Types.Session, Types.EventType, Types.Hndlr, user_handle_p]
        self.lib.internal.viUninstallHandler.argtypes = [Types.Session, Types.EventType, Types.Hndlr, user_handle_p]

    def assert_interrupt_signal(self, session, mode, status_id):
        """Asserts the specified interrupt or signal.

        :param session: Unique logical identifier to a session.
        :param mode: How to assert the interrupt. (Constants.ASSERT*)
        :param status_id: This is the status value to be presented during an interrupt acknowledge cycle.
        """
        self.lib.viAssertIntrSignal(session, mode, status_id)

    def assert_trigger(self, session, protocol):
        """Asserts software or hardware trigger.

        :param session: Unique logical identifier to a session.
        :param protocol: Trigger protocol to use during assertion. (Constants.PROT*)
        """
        self.lib.viAssertTrigger(session, protocol)

    def assert_utility_signal(self, session, line):
        """Asserts or deasserts the specified utility bus signal.

        :param session: Unique logical identifier to a session.
        :param line: specifies the utility bus signal to assert. (Constants.UTIL_ASSERT*)
        """
        self.lib.viAssertUtilSignal(session, line)

    def buffer_read(self, session, count):
        """Reads data from device or interface through the use of a formatted I/O read buffer.

        :param session: Unique logical identifier to a session.
        :param count: Number of bytes to be read.
        :return: data read.
        :rtype: bytes
        """
        buffer = ct.create_string_buffer(count)
        return_count = Types.UInt32()
        self.lib.viBufRead(session, buffer, count, ct.addressof(return_count))
        return buffer.raw[:return_count.value]

    def buffer_write(self, session, data):
        """Writes data to a formatted I/O write buffer synchronously.

        :param session: Unique logical identifier to a session.
        :param data: data to be written.
        :return: number of written bytes.
        """
        return_count = Types.UInt32()
        self.lib.viBufWrite(session, data, len(data), ct.byref(return_count))
        return return_count.value

    def clear(self, session):
        """Clears a device.

        :param session: Unique logical identifier to a session.
        """
        self.lib.viClear(session)

    def close(self, session):
        """Closes the specified session, event, or find list.

        :param session: Unique logical identifier to a session, event, or find list.
        """
        self.lib.viClose(session)

    def disable_event(self, session, event_type, mechanism):
        """Disables notification of the specified event type(s) via the specified mechanism(s).

        :param session: Unique logical identifier to a session.
        :param event_type: Logical event identifier.
        :param mechanism: Specifies event handling mechanisms to be disabled.
                          (Constants.QUEUE, .Handler, .SUSPEND_HNDLR, .ALL_MECH)
        """
        self.lib.viDisableEvent(session, event_type, mechanism)

    def discard_events(self, session, event_type, mechanism):
        """Discards event occurrences for specified event types and mechanisms in a session.

        :param session: Unique logical identifier to a session.
        :param event_type: Logical event identifier.
        :param mechanism: Specifies event handling mechanisms to be disabled.
                          (Constants.QUEUE, .Handler, .SUSPEND_HNDLR, .ALL_MECH)
        """
        self.lib.viDiscardEvents(session, event_type, mechanism)

    def enable_event(self, session, event_type, mechanism, context=Constants.NULL):
        """Discards event occurrences for specified event types and mechanisms in a session.

        :param session: Unique logical identifier to a session.
        :param event_type: Logical event identifier.
        :param mechanism: Specifies event handling mechanisms to be disabled.
                          (Constants.QUEUE, .Handler, .SUSPEND_HNDLR)
        :param context:
        """
        self.lib.viEnableEvent(session, event_type, mechanism, context)

    def find_next(self, find_list):
        """Returns the next resource from the list of resources found during a previous call to find_resources().

        :param find_list: Describes a find list. This parameter must be created by find_resources().
        :return: Returns a string identifying the location of a device.
        """
        instrument_description = ct.create_string_buffer(b'', Constants.FIND_BUFLEN)
        self.lib.viFindNext(find_list, instrument_description)
        return instrument_description.value.decode('ascii')

    def find_resources(self, session, query):
        """Queries a VISA system to locate the resources associated with a specified interface.

        :param session: Unique logical identifier to a session (unused, just to uniform signatures).
        :param query: A regular expression followed by an optional logical expression. Use '?*' for all.
        :return: find_list, return_counter, instrument_description
        """
        find_list = Types.FindList()
        return_counter = Types.UInt32()
        instrument_description = ct.create_string_buffer(b'', Constants.FIND_BUFLEN)
        self.lib.viFindRsrc(session, query, ct.byref(find_list), ct.byref(return_counter),
                            instrument_description)
        return find_list, return_counter.value, instrument_description.value.decode('ascii')

    def flush(self, session, mask):
        """Manually flushes the specified buffers associated with formatted I/O operations and/or serial communication.

        :param session: Unique logical identifier to a session.
        :param mask: Specifies the action to be taken with flushing the buffer.
                     (Constants.READ*, .WRITE*, .IO*)
        """
        self.lib.viFlush(session, mask)

    def get_attribute(self, session, attribute):
        """Retrieves the state of an attribute.

        :param session: Unique logical identifier to a session, event, or find list.
        :param attribute: Resource attribute for which the state query is made (see Attributes.*)
        :return: The state of the queried attribute for a specified resource.
        """
        # FixMe: How to deal with Types.Buf?
        if not hasattr(attribute, 'ctype'):
            attribute = Attributes[attribute]
        code = attribute.code
        datatype = attribute.ctype
        if datatype == Types.String:
            attribute_state = ct.create_string_buffer(256)
            self.lib.viGetAttribute(code, attribute_state)
        elif datatype == Types.AUInt8:
            length = self.get_attribute(session, Attributes.USB_RECV_INTR_SIZE)
            attribute_state = (Types.UInt8 * length)()
            self.lib.viGetAttribute(session, code, ct.byref(attribute_state))
            return list(attribute_state)
        else:
            attribute_state = datatype()
            self.lib.viGetAttribute(session, code, ct.byref(attribute_state))
        return attribute_state.value

    def gpib_command(self, session, data):
        """Write GPIB command bytes on the bus.

        :param session: Unique logical identifier to a session.
        :param data: data tor write.
        :return: Number of written bytes.
        """
        return_count = Types.UInt32()
        self.lib.viGpibCommand(session, data, len(data), ct.byref(return_count))
        return return_count.value

    def gpib_control_atn(self, session, mode):
        """Specifies the state of the ATN line and the local active controller state.

        :param session: Unique logical identifier to a session.
        :param mode: Specifies the state of the ATN line and optionally the local active controller state.
                     (Constants.GPIB_ATN*)
        """
        self.lib.viGpibControlATN(session, mode)

    def gpib_control_ren(self, session, mode):
        """Controls the state of the GPIB Remote Enable (REN) interface line, and optionally the remote/local
        state of the device.

        :param session: Unique logical identifier to a session.
        :param mode: Specifies the state of the REN line and optionally the device remote/local state.
                     (Constants.GPIB_REN*)
        """
        self.lib.viGpibControlREN(session, mode)

    def gpib_pass_control(self, session, primary_address, secondary_address):
        """Tell the GPIB device at the specified address to become controller in charge (CIC).

        :param session: Unique logical identifier to a session.
        :param primary_address: Primary address of the GPIB device to which you want to pass control.
        :param secondary_address: Secondary address of the targeted GPIB device.
                                  If the targeted device does not have a secondary address,
                                  this parameter should contain the value Constants.NO_SEC_ADDR.
        """
        self.lib.viGpibPassControl(session, primary_address, secondary_address)

    def gpib_send_ifc(self, session):
        """Pulse the interface clear line (IFC) for at least 100 microseconds.

        :param session: Unique logical identifier to a session.
        :return:
        """
        self.lib.viGpibSendIFC(session)

    def read_memory(self, session, space, offset, width, extended=False):
        """Reads in an 8-bit, 16-bit, 32-bit, or 64-bit value from the specified memory space and offset.
        :param session: Unique logical identifier to a session.
        :param space: Specifies the address space. (Constants.*SPACE*)
        :param offset: Offset (in bytes) of the address or register from which to read.
        :param width: Number of bits to read.
        :param extended: Use 64 bits offset independent of the platform.
        :return: Data read from memory.

        Corresponds to viIn* functions of the visa library.
        """
        if width not in (8, 16, 32, 64):
            raise ValueError('{} is not a valid size. Valid values are 8, 16, 32, 64'.format(width))
        value = Types['UInt{}'.format(width)]
        fun = getattr(self.lib, 'viIn{}{}'.format(width, 'Ex' if extended else ''))
        fun(session, space, offset, ct.byref(value))
        return value.value

    def install_handler(self, session, event_type, handler, user_handle=None):
        """Installs handlers for event callbacks.

        :param session: Unique logical identifier to a session.
        :param event_type: Logical event identifier.
        :param handler: Interpreted as a valid reference to a handler to be installed by a client application.
        :param user_handle: A value specified by an application that can be used for identifying handlers
                            uniquely for an event type.
        """
        if user_handle is None:
            converted_user_handle = None
        else:
            if isinstance(user_handle, int):
                converted_user_handle = ct.c_long(user_handle)
            elif isinstance(user_handle, float):
                converted_user_handle = ct.c_double(user_handle)
            elif isinstance(user_handle, str):
                converted_user_handle = ct.create_string_buffer(b'', user_handle)
            elif isinstance(user_handle, list):
                for element in user_handle:
                    if not isinstance(element, int):
                        converted_user_handle = (ct.c_double * len(user_handle))(tuple(user_handle))
                        break
                else:
                    converted_user_handle = (ct.c_long * len(user_handle))(*tuple(user_handle))
            else:
                raise TypeError("Type not allowed as user handle: %s" % type(user_handle))

        self.set_user_handle_type(converted_user_handle)
        converted_handler = Types.Hndlr(handler)

        if user_handle is None:
            self.lib.viInstallHandler(session, event_type, converted_handler, None)
        else:
            self.lib.viInstallHandler(session, event_type, converted_handler, ct.byref(converted_user_handle))

        self.handlers.append((handler, converted_user_handle, converted_handler))

        return converted_user_handle

    def lock(self, session, lock_type, timeout, requested_key=None):
        """Establishes an access mode to the specified resources.

        :param session: Unique logical identifier to a session.
        :param lock_type: Specifies the type of lock requested, either Constants.EXCLUSIVE_LOCK or Constants.SHARED_LOCK.
        :param timeout: Absolute time period (in milliseconds) that a resource waits to get unlocked by the
                        locking session before returning an error.
        :param requested_key: This parameter is not used and should be set to VI_NULL when lockType is VI_EXCLUSIVE_LOCK.
        :return: access_key that can then be passed to other sessions to share the lock.
        """
        if lock_type == Constants.EXCLUSIVE_LOCK:
            requested_key = None
            access_key = None
        else:
            access_key = ct.create_string_buffer(256)
        self.lib.viLock(session, lock_type, timeout, requested_key, access_key)
        return access_key.decode('ascii')

    def map_address(self, session, map_space, map_base, map_size, access=Constants.FALSE, suggested=Constants.NULL,
                    extended=False):
        """Maps the specified memory space into the process's address space.

        :param session: Unique logical identifier to a session.
        :param map_space: Specifies the address space to map. (Constants.*SPACE*)
        :param map_base: Offset (in bytes) of the memory to be mapped.
        :param map_size: Amount of memory to map (in bytes).
        :param access:
        :param suggested: If not Constants.NULL (0), the operating system attempts to map the memory to the address
                          specified in suggested. There is no guarantee, however, that the memory will be mapped to
                          that address. This operation may map the memory into an address region different from
                          suggested.
        :param extended: Use 64 bits offset independent of the platform.
        :return: Address in your process space where the memory was mapped.
        """
        address = Types.Addr()
        if extended:
            self.lib.viMapAddressEx(session, map_space, map_base, map_size, access, suggested, ct.byref(address))
        else:
            self.lib.viMapAddress(session, map_space, map_base, map_size, access, suggested, ct.byref(address))
        return address

    def map_trigger(self, session, trigger_source, trigger_destination, mode=Constants.NULL):
        """Map the specified trigger source line to the specified destination line.

        :param session: Unique logical identifier to a session.
        :param trigger_source: Source line from which to map. (Constants.TRIG*)
        :param trigger_destination: Destination line to which to map. (Constants.TRIG*)
        :param mode:
        """
        self.lib.viMapTrigger(session, trigger_source, trigger_destination, mode)

    def memory_allocation(self, session, size, extended=False):
        """Allocates memory from a resource's memory region.

        :param session: Unique logical identifier to a session.
        :param size: Specifies the size of the allocation.
        :param extended: Use 64 bits offset independent of the platform.
        :return: Returns the offset of the allocated memory.
        """
        offset = Types.BusAddress()
        if extended:
            self.lib.viMemAllocEx(session, size, ct.byref(offset))
        else:
            self.lib.viMemAlloc(session, size, ct.byref(offset))
        return offset

    def memory_free(self, session, offset, extended=False):
        """Frees memory previously allocated using the memory_allocation() operation.

        :param session: Unique logical identifier to a session.
        :param size: Specifies the size of the allocation.
        :param extended: Use 64 bits offset independent of the platform.
        """
        if extended:
           self.lib.viMemFreeEx(session, offset)
        else:
           self.lib.viMemFree(session, offset)

    def move(self, session, source_space, source_offset, source_width,
             destination_space, destination_offset, destination_width, length, extended=False):
        """Moves a block of data.

        :param session: Unique logical identifier to a session.
        :param source_space: Specifies the address space of the source.
        :param source_offset: Offset of the starting address or register from which to read.
        :param source_width: Specifies the data width of the source.
        :param destination_space: Specifies the address space of the destination.
        :param destination_offset: Offset of the starting address or register to which to write.
        :param destination_width: Specifies the data width of the destination.
        :param length: Number of elements to transfer, where the data width of the elements to transfer
                       is identical to the source data width.
        :param extended: Use 64 bits offset independent of the platform.
        """
        if extended:
            self.lib.viMoveEx(session, source_space, source_offset, source_width,
                              destination_space, destination_offset, destination_width, length)
        else:
            self.lib.viMove(session, source_space, source_offset, source_width,
                            destination_space, destination_offset, destination_width, length)

    def move_async(self, session, source_space, source_offset, source_width,
                   destination_space, destination_offset, destination_width, length, extended=False):
        """Moves a block of data asynchronously.

        :param session: Unique logical identifier to a session.
        :param source_space: Specifies the address space of the source.
        :param source_offset: Offset of the starting address or register from which to read.
        :param source_width: Specifies the data width of the source.
        :param destination_space: Specifies the address space of the destination.
        :param destination_offset: Offset of the starting address or register to which to write.
        :param destination_width: Specifies the data width of the destination.
        :param length: Number of elements to transfer, where the data width of the elements to transfer
                       is identical to the source data width.
        :param extended: Use 64 bits offset independent of the platform.
        :return: Job identifier of this asynchronous move operation.
        """
        job_id = Types.JobId()
        if extended:
            self.lib.viMoveAsyncEx(session, source_space, source_offset, source_width,
                                   destination_space, destination_offset,
                                   destination_width, length, ct.byref(job_id))
        else:
            self.lib.viMoveAsync(session, source_space, source_offset, source_width,
                                 destination_space, destination_offset,
                                 destination_width, length, ct.byref(job_id))
        return job_id

    def move_memory_in(self, session, space, offset, length, width, extended=False):
        """Moves a block of data from the specified address space and offset to local memory.

        :param session: Unique logical identifier to a session.
        :param space: Specifies the address space. (Constants.*SPACE*)
        :param offset: Offset (in bytes) of the address or register from which to read.
        :param length: Number of elements to transfer, where the data width of the elements to transfer
                       is identical to the source data width.
        :param width: Number of bits to read per element.
        :param extended: Use 64 bits offset independent of the platform.
        :return: Data read from bus.

        Corresponds to viIn* functions of the visa library.
        """
        if width not in (8, 16, 32, 64):
            raise ValueError('{} is not a valid size. Valid values are 8, 16, 32, 64'.format(width))
        value = (Types['UInt{}'.format(width)] * length)()
        fun = getattr(self.lib, 'viMoveIn{}{}'.format(width, 'Ex' if extended else ''))
        fun(session, space, offset, length, value)
        return list(value.value)

    def move_memory_out(self, session, space, offset, length, data, width, extended=False):
        """Moves a block of data from local memory to the specified address space and offset.

        :param session: Unique logical identifier to a session.
        :param space: Specifies the address space. (Constants.*SPACE*)
        :param offset: Offset (in bytes) of the address or register from which to read.
        :param length: Number of elements to transfer, where the data width of the elements to transfer
                       is identical to the source data width.
        :param data: Data to write to bus.
        :param width: Number of bits to read per element.
        :param extended: Use 64 bits offset independent of the platform.
        """
        if width not in (8, 16, 32, 64):
            raise ValueError('{} is not a valid size. Valid values are 8, 16, 32, 64'.format(width))
        value = (Types['UInt{}'.format(width)] * length)(*data)
        fun = getattr(self.lib, 'viMoveOut{}{}'.format(width, 'Ex' if extended else ''))
        fun(session, space, offset, length, value)

    def open(self, session, resource_name, access_mode=Constants.NO_LOCK, open_timeout=Constants.TMO_IMMEDIATE):
        """Opens a session to the specified resource.

        :param session: Resource Manager session (should always be a session returned from open_default_resource_manager()).
        :param resource_name: Unique symbolic name of a resource.
        :param access_mode: Specifies the mode by which the resource is to be accessed. (Constants.NULL or Constants.*LOCK*)
        :param open_timeout: Specifies the maximum time period (in milliseconds) that this operation waits
                             before returning an error.
        :return: Unique logical identifier reference to a session.
        """
        vi = Types.Session()
        self.lib.viOpen(session, resource_name, access_mode, open_timeout, ct.byref(vi))
        return vi.value

    def open_default_resource_manager(self):
        """This function returns a session to the Default Resource Manager resource.

        :return: Unique logical identifier to a Default Resource Manager session.
        """
        session = Types.Session()
        self.lib.viOpenDefaultRM(ct.byref(session))
        return session.value

    def write_memory(self, session, space, offset, data, width, extended=False):
        """Reads in an 8-bit, 16-bit, 32-bit, or 64-bit value from the specified memory space and offset.
        :param session: Unique logical identifier to a session.
        :param space: Specifies the address space. (Constants.*SPACE*)
        :param offset: Offset (in bytes) of the address or register from which to read.
        :param data: Data to write to bus.
        :param width: Number of bits to read.
        :param extended: Use 64 bits offset independent of the platform.

        Corresponds to viOut* functions of the visa library.
        """
        if width not in (8, 16, 32, 64):
            raise ValueError('{} is not a valid size. Valid values are 8, 16, 32, 64'.format(width))
        fun = getattr(self.lib, 'viOut{}{}'.format(width, 'Ex' if extended else ''))
        fun(session, space, offset, data)

    def parse_resource(self, session, resource_name):
        """Parse a resource string to get the interface information.

        :param session: Resource Manager session (should always be the Default Resource Manager for VISA
                        returned from open_default_resource_manager()).
        :param resource_name: Unique symbolic name of a resource.
        :return: Resource information with interface type and board number.
        :rtype: :class:ResourceInfo
        """
        interface_type = Types.UInt16()
        interface_board_number = Types.UInt16()
        self.lib.viParseRsrc(session, resource_name, ct.byref(interface_type), ct.byref(interface_board_number))
        return ResourceInfo(interface_type.value, interface_board_number.value, None, None, None, None)

    def parse_resource_extended(self, session, resource_name):
        """Parse a resource string to get extended interface information.

        :param session: Resource Manager session (should always be the Default Resource Manager for VISA
                        returned from open_default_resource_manager()).
        :param resource_name: Unique symbolic name of a resource.
        :return: Resource information.
        :rtype: :class:ResourceInfo
        """
        interface_type = Types.UInt16()
        interface_board_number = Types.UInt16()
        resource_class = ct.create_string_buffer(b'', Constants.FIND_BUFLEN)
        unaliased_expanded_resource_name = ct.create_string_buffer(b'', Constants.FIND_BUFLEN)
        alias_if_exists = ct.create_string_buffer(b'', Constants.FIND_BUFLEN)
        self.lib.viParseRsrcEx(session, resource_name, ct.byref(interface_type),
                               ct.byref(interface_board_number), resource_class,
                               unaliased_expanded_resource_name, alias_if_exists)

        return ResourceInfo(interface_type.value, interface_board_number.value,
                            resource_class.value.decode('ascii'),
                            unaliased_expanded_resource_name.value.decode('ascii'),
                            alias_if_exists.value.decode('ascii'))

    def peek(self, session, address, width):
        """Writes an 8-bit, 16-bit, 32-bit, or 64-bit value from the specified address.

        :param session: Unique logical identifier to a session.
        :param address: Source address to read the value.
        :param width: Number of bits to read.
        :return: Data read from bus.
        :rtype: bytes
        """
        if width not in (8, 16, 32, 64):
            raise ValueError('{} is not a valid size. Valid values are 8, 16, 32, 64'.format(width))
        value = Types['UInt{}'.format(width)]
        fun = getattr(self.lib, 'viPeek{}'.format(width))
        fun(session, address, ct.byref(value))
        return value.value

    def poke(self, session, address, data, width):
        """Reads an 8-bit, 16-bit, 32-bit, or 64-bit value from the specified address.

        :param session: Unique logical identifier to a session.
        :param address: Source address to read the value.
        :param data: value to be written to the bus.
        :param width: Number of bits to read.
        :return: Data read from bus.
        :rtype: bytes
        """
        if width not in (8, 16, 32, 64):
            raise ValueError('{} is not a valid size. Valid values are 8, 16, 32, 64'.format(width))
        fun = getattr(self.lib, 'viPoke{}'.format(width))
        fun(session, address, data)

    def read(self, session, count):
        """Reads data from device or interface synchronously.

        :param session: Unique logical identifier to a session.
        :param count: Number of bytes to be read.
        :return: data read.
        """
        buffer = ct.create_string_buffer(count)
        return_count = Types.UInt32()
        self.lib.viRead(session, buffer, count, ct.byref(return_count))
        return buffer.value[:return_count.value]

    def read_asynchronously(self, session, count):
        """Reads data from device or interface asynchronously.

        :param session: Unique logical identifier to a session.
        :param count: Number of bytes to be read.
        :return: (ctypes buffer with result, jobid)
        """
        buffer = ct.create_string_buffer(count)
        job_id = Types.JobId()
        self.lib.viReadAsync(session, buffer, count, ct.byref(job_id))
        return buffer, job_id

    def read_stb(self, session):
        """Reads a status byte of the service request.

        :param session: Unique logical identifier to a session.
        :return: Service request status byte.
        """
        status = Types.UInt16()
        self.lib.viReadSTB(session, ct.byref(status))
        return status.value

    def read_to_file(self, session, filename, count):
        """Read data synchronously, and store the transferred data in a file.

        :param session: Unique logical identifier to a session.
        :param filename: Name of file to which data will be written.
        :param count: Number of bytes to be read.
        :return: Number of bytes actually transferred.
        """
        return_count = Types.UInt32()
        self.lib.viReadToFile(session, filename, count, return_count)
        return return_count

    def set_attribute(self, session, attribute, attribute_state):
        """Sets the state of an attribute.

        :param session: Unique logical identifier to a session.
        :param attribute: Attribute for which the state is to be modified. (Attributes.*)
        :param attribute_state: The state of the attribute to be set for the specified object.
        :return:
        """
        if isinstance(attribute, str):
            attribute = Attributes[attribute].code
        self.lib.viSetAttribute(session, attribute, attribute_state)

    def set_buffer(self, session, mask, size):
        """Sets the size for the formatted I/O and/or low-level I/O communication buffer(s).

        :param session: Unique logical identifier to a session.
        :param mask: Specifies the type of buffer. (Constants.READ_BUF, .WRITE_BUF, .IO_IN_BUF, .IO_OUT_BUF)
        :param size: The size to be set for the specified buffer(s).
        :return:
        """
        self.lib.viSetBuf(session, mask, size)

    def status_description(self, session, status):
        """Returns a user-readable description of the status code passed to the operation.

        :param session: Unique logical identifier to a session.
        :param status: Status code to interpret.
        :return: The user-readable string interpretation of the status code passed to the operation.
        """
        description = ct.create_string_buffer(256)
        self.lib.viStatusDesc(session, status, description)
        return description.value.decode('ascii')

    def terminate(self, session, degree, job_id):
        """Requests a VISA session to terminate normal execution of an operation.

        :param session: Unique logical identifier to a session.
        :param degree: Constants.NULL
        :param job_id: Specifies an operation identifier.
        """
        self.lib.viTerminate(session, degree, job_id)

    def uninstall_handler(self, session, event_type, handler, user_handle=None):
        """Uninstalls handlers for events.

        :param session: Unique logical identifier to a session.
        :param event_type: Logical event identifier.
        :param handler: Interpreted as a valid reference to a handler to be uninstalled by a client application.
        :param user_handle: A value specified by an application that can be used for identifying handlers
                            uniquely in a session for an event.
        """
        for ndx, (listed_handler, converted_user_handle, converted_handler) in enumerate(self.handlers):
            if listed_handler is handler and converted_user_handle is user_handle:
                self.lib.viUninstallHandler(session, event_type, converted_handler, ct.byref(converted_user_handle))
                del self.handlers[ndx]
                break
        else:
            raise IndexError('Unknown handler')

    def unlock(self, session):
        """Relinquishes a lock for the specified resource.

        :param session: Unique logical identifier to a session.
        """
        self.lib.viUnlock(session)

    def unmap_address(self, session):
        """Unmaps memory space previously mapped by map_address().

        :param session: Unique logical identifier to a session.
        """
        self.lib.viUnmapAddress(session)

    def unmap_trigger(self, session, trigger_source, trigger_destination):
        """Undo a previous map from the specified trigger source line to the specified destination line.

        :param session: Unique logical identifier to a session.
        :param trigger_source: Source line used in previous map. (Constants.TRIG*)
        :param trigger_destination: Destination line used in previous map. (Constants.TRIG*)
        :return:
        """
        self.lib.viUnmapTrigger(session, trigger_source, trigger_destination)

    def usb_control_in(self, session, request_type_bitmap_field, request_id, request_value, index, length=0):
        """Performs a USB control pipe transfer from the device.

        :param session: Unique logical identifier to a session.
        :param request_type_bitmap_field: bmRequestType parameter of the setup stage of a USB control transfer.
        :param request_id: bRequest parameter of the setup stage of a USB control transfer.
        :param request_value: wValue parameter of the setup stage of a USB control transfer.
        :param index: wIndex parameter of the setup stage of a USB control transfer.
                      This is usually the index of the interface or endpoint.
        :param length: wLength parameter of the setup stage of a USB control transfer.
                       This value also specifies the size of the data buffer to receive the data from the
                       optional data stage of the control transfer.
        :return: The data buffer that receives the data from the optional data stage of the control transfer.
        :rtype: bytes
        """
        buffer = ct.create_string_buffer(length)
        return_count = Types.UInt16()
        self.lib.viUsbControlIn(session, request_type_bitmap_field, request_id,
                                request_value, index, length, buffer,
                                ct.byref(return_count))
        return buffer.raw[:return_count.value]

    def usb_control_out(self, session, request_type_bitmap_field, request_id, request_value, index, data=""):
        """Performs a USB control pipe transfer to the device.

        :param session: Unique logical identifier to a session.
        :param request_type_bitmap_field: bmRequestType parameter of the setup stage of a USB control transfer.
        :param request_id: bRequest parameter of the setup stage of a USB control transfer.
        :param request_value: wValue parameter of the setup stage of a USB control transfer.
        :param index: wIndex parameter of the setup stage of a USB control transfer.
                      This is usually the index of the interface or endpoint.
        :param data: The data buffer that sends the data in the optional data stage of the control transfer.
        """
        length = len(data)
        self.lib.viUsbControlOut(session, request_type_bitmap_field, request_id, request_value, index, length, data)

    def vxi_command_query(self, session, mode, command):
        """Sends the device a miscellaneous command or query and/or retrieves the response to a previous query.

        :param session: Unique logical identifier to a session.
        :param mode: Specifies whether to issue a command and/or retrieve a response. (Constants.VXI_CMD*, .VXI_RESP*)
        :param command: The miscellaneous command to send.
        :return: The response retrieved from the device.
        """
        response = Types.UInt32()
        self.lib.viVxiCommandQuery(session, mode, command, ct.byref(response))
        return response.value

    def wait_on_event(self, session, in_event_type, timeout):
        """Waits for an occurrence of the specified event for a given session.

        :param session: Unique logical identifier to a session.
        :param in_event_type: Logical identifier of the event(s) to wait for.
        :param timeout: Absolute time period in time units that the resource shall wait for a specified event to
                        occur before returning the time elapsed error. The time unit is in milliseconds.
        :return: Logical identifier of the event actually received, A handle specifying the unique occurrence of an event.
        """
        out_event_type = Types.EventType()
        out_context = Types.Event()
        self.lib.viWaitOnEvent(session, in_event_type, timeout,
                               ct.byref(out_event_type), ct.byref(out_context))
        return out_event_type.value, out_context

    def write(self, session, data):
        """Writes data to device or interface synchronously.

        :param session: Unique logical identifier to a session.
        :param data: data to be written.
        :return: Number of bytes actually transferred.
        """
        return_count = Types.UInt32()
        self.lib.viWrite(session, data, len(data), ct.byref(return_count))
        return return_count.value

    def write_asynchronously(self, session, buffer):
        """Writes data to device or interface asynchronously.

        :param session: Unique logical identifier to a session.
        :param data: data to be written.
        :return: Job ID of this asynchronous write operation.
        """
        job_id = Types.JobId()
        self.lib.viWriteAsync(session, buffer, len(buffer), ct.byref(job_id))
        return job_id

    def write_from_file(self, session, filename, count):
        """Take data from a file and write it out synchronously.

        :param session: Unique logical identifier to a session.
        :param filename: Name of file from which data will be read.
        :param count: Number of bytes to be written.
        :return: Number of bytes actually transferred.
        """
        return_count = Types.UInt32()
        self.lib.viWriteFromFile(session, filename, count, return_count)
        return return_count


class ResourceManager(object):
    """VISA Resource Manager

    :param library_path: path of the VISA library (if not given, the default for the platform will be used).
    """

    #: Holds a mapping between library_path and the default manager
    REGISTER = {}

    def __new__(cls, library_path=None):
        library_path = library_path or LIBRARY_PATH
        if library_path in cls.REGISTER:
            return cls.REGISTER[library_path]

        obj = cls.REGISTER.setdefault(library_path, super().__new__(cls))

        obj.visa = VisaLibrary(library_path)

        obj.session = obj.visa.open_default_resource_manager()
        logger.debug('Created ResourceManager (session: {}) for library {}'.format(obj.session, library_path))

        return obj

    def __del__(self):
        self.visa.close(self.session)

    def list_resources(self, query='?*::INSTR'):
        """Returns a list of all connected devices matching query.

        :param query: regular expression used to match devices.
        """

        lib = self.visa

        resources = []
        find_list, return_counter, instrument_description = lib.find_resources(self.session, query)
        resources.append(instrument_description)
        for i in range(return_counter - 1):
            resources.append(lib.find_next(find_list))

        return tuple(resource for resource in resources)

    def list_resources_info(self, query='?*::INSTR'):
        """Returns a dictionary mapping resource names to resource extended
        information of all connected devices matching query.

        :param query: regular expression used to match devices.
        """

        return {resource: self.resource_info(resource) for resource in self.list_resources(query)}

    def resource_info(self, resource_name):
        """Get the extended information of a particular resource
        """
        return self.visa.parse_resource_extended(self.session, resource_name)

    def open_resource(self, resource_name, access_mode=Constants.NO_LOCK, open_timeout=Constants.TMO_IMMEDIATE):
        """Open the specified resources.

        :param resource_name: name or alias of the resource to open.
        :param access_mode: access mode.
        :param open_timeout: time out to open.
        """
        return self.visa.open(self.session, resource_name, access_mode, open_timeout)
