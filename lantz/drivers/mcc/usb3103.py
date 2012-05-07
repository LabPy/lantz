import ctypes as ct

from lantz.foreign import ForeignDriver
from lantz.errors import InstrumentError

from lantz.drivers.mcc import param

def logged(func):
    return func

class Usb3103(ForeignDriver):
    """8-Channel, 16-Bit Analog Voltage Output Device
    """

    LIBRARY_NAME = 'cbw32.dll'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.RevLevel = param.CURRENTREVNUM
        self.status = self.lib.cbErrHandling(param.PRINTALL, param.DONTSTOP)

    def _return_handler(self, func_name, ret_value):
        if ret_value != 0:
            raise InstrumentError('{} ({})'.format(ret_value, _ERRORS[ret_value]))
        return ret_value

    @logged
    def getDeclareRevision(self):
        return self.RevLevel

    @logged
    def getStatus(self):
        return self.status,

    @logged
    def AIn(self, Chan=0, Gain=param.BIP5VOLTS):
        (self.status, data) = self.lib.cbAIn(self.BoardNum, Chan, Gain)
        return data

    def AInScan(self, LowChan=0, HighChan=4, Count=20, Rate=3125,
                      Gain=param.BIP5VOLTS, Options=param.CONVERTDATA):
        self.status = self.lib.cbAInScan(self.BoardNum, LowChan, HighChan, Count,
                                             Rate, Gain, Options)

    def AOut(self, Chan=0, Gain=param.BIP5VOLTS, DataValue=0):
        self.status = self.lib.cbAOut(self.BoardNum, Chan, Gain, DataValue)

    @logged
    def ToEngUnits(self, Gain=param.BIP5VOLTS, DataValue=0):
        (self.status, EngUnits) = self.lib.cbToEngUnits(self.BoardNum, Gain, DataValue)
        return EngUnits

    @logged
    def FromEngUnits(self, Gain=param.BIP5VOLTS, EngUnits=0.0):
        (self.status, DataValue) = self.lib.cbFromEngUnits(self.BoardNum, Gain, EngUnits)
        return DataValue

    @logged
    def DConfigPort(self, PortNum=param.AUXPORT, Direction=param.DIGITALIN):
        PortNum = ct.c_int(PortNum)
        Direction = ct.c_int(Direction)
        self.status = self.lib.cbDConfigPort(self.BoardNum, PortNum, Direction)
        return self.status

    @logged
    def DConfigBit(self, PortNum=param.AUXPORT, BitNum=0, Direction=param.DIGITALIN):
        PortNum = ct.c_int(PortNum)
        BitNum = ct.c_int(BitNum)
        Direction = ct.c_int(Direction)
        self.status = self.lib.cbDConfigPort(self.BoardNum, PortNum, Direction)
        return self.status

    @logged
    def DIn(self, PortNum=param.FIRSTPORTA):
        (self.status, data) = self.lib.cbDIn(self.BoardNum, PortNum)
        return data

    @logged
    def DBitIn(self, PortType=param.FIRSTPORTA, BitNum=0):
        PortType = ct.c_int(PortType)
        BitNum = ct.c_int(BitNum)
        (self.status, data) = self.lib.cbDBitIn(self.BoardNum, PortType, BitNum)
        return data

    def DOut(self, PortNum=param.FIRSTPORTA, DataValue=0):
        PortNum = ct.c_int(PortNum)
        DataValue = ct.c_int(DataValue)
        self.status = self.lib.cbDOut(self.BoardNum, PortNum, DataValue)

    def DBitOut(self, PortType=param.AUXPORT, BitNum=0, BitValue=0):
        PortType = ct.c_int(PortType)
        BitNum = ct.c_int(BitNum)
        BitValue = ct.c_ushort(BitValue)
        self.status = self.lib.cbDBitOut(self.BoardNum, PortType, BitNum, BitValue)

    def C8254Config(self, CounterNum=1, Config=param.HIGHONLASTCOUNT):
        self.status = self.lib.cbC8254Config(self.BoardNum, CounterNum, Config)

    def CLoad(self, RegName=param.LOADREG1, LoadValue=1000):
        self.status = self.lib.cbCLoad(self.BoardNum, RegName, LoadValue)

    def CLoad32(self, RegName=param.LOADREG1, LoadValue=1000):
        self.status = self.lib.cbCLoad32(self.BoardNum, RegName, LoadValue)

    def CIn(self, CounterNum=1):
        (self.status, data) = self.lib.cbCIn(self.BoardNum, CounterNum)
        return data

    @logged
    def CIn32(self, CounterNum=1):
        (self.status, data) = self.lib.cbCIn32(self.BoardNum, CounterNum)
        return data

    @logged
    def CFreqIn(self, SigSource=param.CTRINPUT1, GateInterval=100):
        (self.status, Count, Freq) = self.lib.cbCFreqIn(self.BoardNum, SigSource, GateInterval)
        return Count, Freq

    def C9513Init(self, ChipNum=1, FOutDivider=0, FOutSource=param.FREQ4,
                  Compare1=param.DISABLED, Compare2=param.DISABLED, TimeOfDay=param.DISABLED):

        self.status = self.lib.cbC9513Init(self.BoardNum, ChipNum, FOutDivider,
                                    FOutSource, Compare1, Compare2, TimeOfDay)

    @logged
    def GetBoardName(self):
        boardName = (ct.c_char * 8)()
        Name = self.lib.cbGetBoardName(self.BoardNum, boardName)
        return boardName[:8]

    @logged
    def GetErrMsg(self, ErrCode=0):
        ErrMsg = self.lib.cbGetErrMsg(ErrCode)
        return ErrMsg

    @logged
    def GetConfig(self, InfoType=param.DIGITALINFO, DevNum=0, ConfigItem=param.DIDEVTYPE):
        InfoType = ct.c_int(InfoType)
        DevNum = ct.c_int(DevNum)
        ConfigItem = ct.c_int(ConfigItem)
        ConfigVal = (ct.c_int * 1)()
        #(self.status, ConfigVal) =\
        self.status = self.lib.cbGetConfig(InfoType, self.BoardNum,
                                               DevNum, ConfigItem, ConfigVal)

        return ConfigVal[0]

    def SetConfig(self, InfoType=param.BOARDINFO, DevNum=0,
                        ConfigItem=param.BIDACUPDATEMODE, ConfigVal=param.UPDATEONCOMMAND):
        self.status = self.lib.cbSetConfig(InfoType, self.BoardNum, DevNum, ConfigItem, ConfigVal)

    def FlashLED(self):
        self.status = self.lib.cbFlashLED(self.BoardNum)

if __name__ == '__main__':
    import param
    from time import sleep

    with MCCDAQ() as daq:
        daq.FlashLED()
        daq.GetBoardName()
        portType = daq.GetConfig()

        if portType != param.AUXPORT:
            print("ERROR: This board does NOT have an AUXPORT.")

        daq.DConfigBit(BitNum=4, Direction=param.DIGITALOUT)
        daq.DBitOut(BitNum=4, BitValue=1)
        sleep(3)
        daq.DBitOut(BitNum=4, BitValue=0)

