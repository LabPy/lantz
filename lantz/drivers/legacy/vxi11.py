# -*- coding: utf-8 -*-
"""
    lantz.drivers.legacy.vx11
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Implements a VXI11Driver based class to control VXI11 instruments

    Loosely based on Python Sun RPC Demo and Alex Forencich python-vx11

    :copyright: 2015 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

import enum
import socket

from lantz.errors import InstrumentError
from lantz.drivers.legacy import rpc
from lantz import Driver


# VXI-11 RPC constants

# Device async
DEVICE_ASYNC_PROG = 0x0607b0
DEVICE_ASYNC_VERS = 1
DEVICE_ABORT      = 1

# Device core
DEVICE_CORE_PROG  = 0x0607af
DEVICE_CORE_VERS  = 1
CREATE_LINK       = 10
DEVICE_WRITE      = 11
DEVICE_READ       = 12
DEVICE_READSTB    = 13
DEVICE_TRIGGER    = 14
DEVICE_CLEAR      = 15
DEVICE_REMOTE     = 16
DEVICE_LOCAL      = 17
DEVICE_LOCK       = 18
DEVICE_UNLOCK     = 19
DEVICE_ENABLE_SRQ = 20
DEVICE_DOCMD      = 22
DESTROY_LINK      = 23
CREATE_INTR_CHAN  = 25
DESTROY_INTR_CHAN = 26

# Device intr
DEVICE_INTR_PROG  = 0x0607b1
DEVICE_INTR_VERS  = 1
DEVICE_INTR_SRQ   = 30

# Error states
class ERROR_CODES(enum.IntEnum):
    NO_ERROR = 0
    SYNTAX_ERROR = 1
    DEVICE_NOT_ACCESSIBLE = 3
    INVALID_LINK_IDENTIFIER = 4
    PARAMETER_ERROR = 5
    CHANNEL_NOT_ESTABLISHED = 6
    OPERATION_NOT_SUPPORTED = 8
    OUT_OF_RESOURCES = 9
    DEVICE_LOCKED_BY_ANOTHER_LINK = 11
    NO_LOCK_HELD_BY_THIS_LINK = 12
    IO_TIMEOUT = 15
    IO_ERROR = 17
    ABORT = 23
    CHANNEL_ALREADY_ESTABLISHED = 29

# Flags
OP_FLAG_WAIT_BLOCK = 1
OP_FLAG_END = 8
OP_FLAG_TERMCHAR_SET = 128

RX_REQCNT = 1
RX_CHR = 2
RX_END = 4

# Exceptions
class Vxi11Error(InstrumentError):
    pass


class Vxi11Packer(rpc.Packer):
    def pack_device_link(self, link):
        self.pack_int(link)
    
    def pack_create_link_parms(self, params):
        id, lock_device, lock_timeout, device = params
        self.pack_int(id)
        self.pack_bool(lock_device)
        self.pack_uint(lock_timeout)
        self.pack_string(device)
    
    def pack_device_write_parms(self, params):
        link, io_timeout, lock_timeout, flags, data = params
        self.pack_int(link)
        self.pack_uint(io_timeout)
        self.pack_uint(lock_timeout)
        self.pack_int(flags)
        self.pack_opaque(data)
    
    def pack_device_read_parms(self, params):
        link, request_size, io_timeout, lock_timeout, flags, term_char = params
        self.pack_int(link)
        self.pack_uint(request_size)
        self.pack_uint(io_timeout)
        self.pack_uint(lock_timeout)
        self.pack_int(flags)
        self.pack_int(term_char)
    
    def pack_device_generic_parms(self, params):
        link, flags, lock_timeout, io_timeout = params
        self.pack_int(link)
        self.pack_int(flags)
        self.pack_uint(lock_timeout)
        self.pack_uint(io_timeout)
    
    def pack_device_remote_func_parms(self, params):
        host_addr, host_port, prog_num, prog_vers, prog_family = params
        self.pack_uint(host_addr)
        self.pack_uint(host_port)
        self.pack_uint(prog_num)
        self.pack_uint(prog_vers)
        self.pack_int(prog_family)
    
    def pack_device_enable_srq_parms(self, params):
        link, enable, handle = params
        self.pack_int(link)
        self.pack_bool(enable)
        if len(handle) > 40:
            raise Vxi11Error("array length too long")
        self.pack_opaque(handle)
    
    def pack_device_lock_parms(self, params):
        link, flags, lock_timeout = params
        self.pack_int(link)
        self.pack_int(flags)
        self.pack_uint(lock_timeout)
    
    def pack_device_docmd_parms(self, params):
        link, flags, io_timeout, lock_timeout, cmd, network_order, datasize, data_in = params
        self.pack_int(link)
        self.pack_int(flags)
        self.pack_uint(io_timeout)
        self.pack_uint(lock_timeout)
        self.pack_int(cmd)
        self.pack_bool(network_order)
        self.pack_int(datasize)
        self.pack_opaque(data_in)


class Vxi11Unpacker(rpc.Unpacker):
    def unpack_device_link(self):
        return self.unpack_int()
    
    def unpack_device_error(self):
        return self.unpack_int()
    
    def unpack_create_link_resp(self):
        error = self.unpack_int()
        link = self.unpack_int()
        abort_port = self.unpack_uint()
        max_recv_size = self.unpack_uint()
        return error, link, abort_port, max_recv_size
    
    def unpack_device_write_resp(self):
        error = self.unpack_int()
        size = self.unpack_uint()
        return error, size
    
    def unpack_device_read_resp(self):
        error = self.unpack_int()
        reason = self.unpack_int()
        data = self.unpack_opaque()
        return error, reason, data
    
    def unpack_device_read_stb_resp(self):
        error = self.unpack_int()
        stb = self.unpack_uint()
        return error, stb
    
    def unpack_device_docmd_resp(self):
        error = self.unpack_int()
        data_out = self.unpack_opaque()
        return error, data_out


class CoreClient(rpc.TCPClient):

    def __init__(self, host):
        self.packer = Vxi11Packer()
        self.unpacker = Vxi11Unpacker('')
        super().__init__(host, DEVICE_CORE_PROG, DEVICE_CORE_VERS)
        # I have disabled the creation of the socket by overriding connect.
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        # Overrides connect method from parent class to avoid automatic
        # opening of connection.
        pass

    def create_link(self, id, lock_device, lock_timeout, name):
        params = (id, lock_device, lock_timeout, name)
        return self.make_call(CREATE_LINK, params,
                              self.packer.pack_create_link_parms,
                              self.unpacker.unpack_create_link_resp)

    def device_write(self, link, io_timeout, lock_timeout, flags, data):
        params = (link, io_timeout, lock_timeout, flags, data)
        return self.make_call(DEVICE_WRITE, params,
                              self.packer.pack_device_write_parms,
                              self.unpacker.unpack_device_write_resp)

    def device_read(self, link, request_size, io_timeout, lock_timeout, flags, term_char):
        params = (link, request_size, io_timeout, lock_timeout, flags, term_char)
        return self.make_call(DEVICE_READ, params,
                              self.packer.pack_device_read_parms,
                              self.unpacker.unpack_device_read_resp)

    def device_read_stb(self, link, flags, lock_timeout, io_timeout):
        params = (link, flags, lock_timeout, io_timeout)
        return self.make_call(DEVICE_READSTB, params,
                              self.packer.pack_device_generic_parms,
                              self.unpacker.unpack_device_read_stb_resp)

    def device_trigger(self, link, flags, lock_timeout, io_timeout):
        params = (link, flags, lock_timeout, io_timeout)
        return self.make_call(DEVICE_TRIGGER, params,
                              self.packer.pack_device_generic_parms,
                              self.unpacker.unpack_device_error)

    def device_clear(self, link, flags, lock_timeout, io_timeout):
        params = (link, flags, lock_timeout, io_timeout)
        return self.make_call(DEVICE_CLEAR, params,
                              self.packer.pack_device_generic_parms,
                              self.unpacker.unpack_device_error)

    def device_remote(self, link, flags, lock_timeout, io_timeout):
        params = (link, flags, lock_timeout, io_timeout)
        return self.make_call(DEVICE_REMOTE, params,
                              self.packer.pack_device_generic_parms,
                              self.unpacker.unpack_device_error)

    def device_local(self, link, flags, lock_timeout, io_timeout):
        params = (link, flags, lock_timeout, io_timeout)
        return self.make_call(DEVICE_LOCAL, params,
                              self.packer.pack_device_generic_parms,
                              self.unpacker.unpack_device_error)

    def device_lock(self, link, flags, lock_timeout):
        params = (link, flags, lock_timeout)
        return self.make_call(DEVICE_LOCK, params,
                              self.packer.pack_device_lock_parms,
                              self.unpacker.unpack_device_error)

    def device_unlock(self, link):
        return self.make_call(DEVICE_UNLOCK, link,
                              self.packer.pack_device_link,
                              self.unpacker.unpack_device_error)

    def device_enable_srq(self, link, enable, handle):
        params = (link, enable, handle)
        return self.make_call(DEVICE_ENABLE_SRQ, params,
                              self.packer.pack_device_enable_srq_parms,
                              self.unpacker.unpack_device_error)

    def device_docmd(self, link, flags, io_timeout, lock_timeout, cmd, network_order, datasize, data_in):
        params = (link, flags, io_timeout, lock_timeout, cmd, network_order, datasize, data_in)
        return self.make_call(DEVICE_DOCMD, params,
                              self.packer.pack_device_docmd_parms,
                              self.unpacker.unpack_device_docmd_resp)

    def destroy_link(self, link):
        return self.make_call(DESTROY_LINK, link,
                              self.packer.pack_device_link,
                              self.unpacker.unpack_device_error)
    
    def create_intr_chan(self, host_addr, host_port, prog_num, prog_vers, prog_family):
        params = (host_addr, host_port, prog_num, prog_vers, prog_family)
        return self.make_call(CREATE_INTR_CHAN, params,
                              self.packer.pack_device_docmd_parms,
                              self.unpacker.unpack_device_error)
    
    def destroy_intr_chan(self):
        return self.make_call(DESTROY_INTR_CHAN, None,
                              None,
                              self.unpacker.unpack_device_error)


class Vxi11Driver(Driver):
    """VXI-11 instrument interface client.
    We do not inherit from TCPDriver because the RPC implementation has its own socket.
    """

    def __init__(self, host='localhost', *args, **kwargs):
        super().__init__(host, *args, **kwargs)

        self.socket = None
        self.lock_timeout = 10000
        self.io_timeout = 10000
        self.client = CoreClient(host)
        self.link = None

    def initialize(self):
        """Open connection to VXI-11 instrument
        """
        super().initialize()
        self.socket = self.client.sock
        self.socket.connect((self.client.sock, self.client.port))

        error, link, abort_port, max_recv_size = self.client.create_link(self.client_id, 0, self.lock_timeout, self.name.encode(self.ENCODING))
        
        if error:
            raise Vxi11Error("error creating link: %d" % error)
        
        self.link = link
        self.RECV_CHUNK = max_recv_size
        
    def finalize(self):
        """Close connection
        """
        self.client.destroy_link(self.link)
        self.client.close()
        super().finalize()

    def write_raw(self, data):
        """Write binary data to instrument
        """

        if self.term_char is not None:
            flags = OP_FLAG_TERMCHAR_SET
            term_char = str(self.term_char).encode('utf-8')[0]
            data += term_char
        
        flags = 0
        
        num = len(data)
        
        offset = 0
        
        while num > 0:
            if num <= self.RECV_CHUNK:
                flags |= OP_FLAG_END
            
            block = data[offset:offset+self.RECV_CHUNK]
            
            error, size = self.client.device_write(self.link, self.io_timeout, self.lock_timeout, flags, block)
            
            if error:
                raise Vxi11Error("error writing data: %d" % error)
            elif size < len(block):
                raise Vxi11Error("did not write complete block")
            
            offset += size
            num -= size

    def read_raw(self, num=-1):
        """Read binary data from instrument
        """

        read_len = self.RECV_CHUNK
        if 0 < num < self.RECV_CHUNK:
            read_len = num
        
        flags = 0
        reason = 0
        
        term_char = 0
        
        if self.term_char is not None:
            flags = OP_FLAG_TERMCHAR_SET
            term_char = str(self.term_char).encode('utf-8')[0]
        
        read_data = b''
        
        while reason & (RX_END | RX_CHR) == 0:
            error, reason, data = self.client.device_read(self.link, read_len, self.io_timeout, self.lock_timeout, flags, term_char)
            
            if error:
                raise Vxi11Error("error reading data: %d" % error)
            
            read_data += data
            
            if num > 0:
                num = num - len(data)
                if num <= 0:
                    break
                if num < read_len:
                    read_len = num
            
        return read_data

    def read_stb(self):
        """Read status byte
        """

        flags = 0
        
        error, stb = self.client.device_read_stb(self.link, flags, self.lock_timeout, self.io_timeout)
        
        if error:
            raise Vxi11Error("error reading status: %d" % error)
        
        return stb
    
    def trigger(self):
        """Send trigger command.
        """

        flags = 0
        
        error = self.client.device_trigger(self.link, flags, self.lock_timeout, self.io_timeout)
        
        if error:
            raise Vxi11Error("error triggering: %d" % error)
    
    def clear(self):
        """Send clear command.
        """

        flags = 0

        error = self.client.device_clear(self.link, flags, self.lock_timeout, self.io_timeout)
        
        if error:
            raise Vxi11Error("error clearing: %d" % error)
    
    def remote(self):
        """Send remote command.
        """

        flags = 0
        
        error = self.client.device_remote(self.link, flags, self.lock_timeout, self.io_timeout)
        
        if error:
            raise Vxi11Error("error remote: %d" % error)
    
    def local(self):
        """Send local command
        """
        
        flags = 0
        
        error = self.client.device_local(self.link, flags, self.lock_timeout, self.io_timeout)
        
        if error:
            raise Vxi11Error("error local: %d" % error)
    
    def lock(self):
        """Send lock command.
        """

        flags = 0
        
        error = self.client.device_lock(self.link, flags, self.lock_timeout)
        
        if error:
            raise Vxi11Error("error locking: %d" % error)
    
    def unlock(self):
        """Send unlock command.
        """

        flags = 0
        
        error = self.client.device_unlock(self.link)
        
        if error:
            raise Vxi11Error("error unlocking: %d" % error)



