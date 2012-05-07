import ctypes as ct

from lantz import Feat, Action, DictFeat
from lantz.foreign import LibraryDriver, RetStr, RetTuple

_ERRORS = {
        4: "ID 4",
        3: "ID 3",
        2: "ID 2",
        1: "1",
        0: "Success",
        -1: "COM_ERROR",
        }

class C843(LibraryDriver):
    """C-843 DC-Servo-Motor Controller
    """

    LIBRARY_NAME = 'C843_GCS_DLL.dll'

    def __init__(self, board_number, stages=None, axes=None, **kwargs):
        super().__init__(**kwargs)
        self.board = ct.c_int(board_number) 
        self.ild = 0
        self.axes = axes
        self.stages = stages

    def _return_handler(self, name, func):
        def _inner(*args, **kwargs):
            value = func(*args, **kwargs)
            if value < 0:
                raise LantzError('{} ({})'.format(value, _ERRORS[value]))
            return value
        return _inner

    def initialize(self):
        """Initialise Library.
        """
        self.ild = self.lib.C843_Connect(self.board)

    def finalize(self):
        """Initialise Library."""
        self.lib.C843_CloseConnection(self.ild)

    @Feat(read_once=True)
    def idn(self):
        """Identification
        """
        ret, idn = self.lib.E816_qIDN(self.ild, *RetStr(64))
        return idn

    @Feat()
    def is_connected(self):
        """Is library connected.
        """
        error = self.lib.C843_IsConnected(self.ild)
        # TODO THIS does not look right
        return 'XXXXX'

    @Feat()
    def stages(self):
        """Connect Stages.
        """
        channels = ct.c_char_p(self.axes)
        length = ct.c_int(40)
        stages = (ct.c_char * 40)()
        self.lib.C843_qCST(self.ild, channels, stages, length)
        return stages

    @stages.setter
    def stages(self, stages):
        channels = ct.c_char_p(''.join(str(x + 1) for x in range(0, len(stages))))
        stages = ct.c_char_p('\n'.join(stages))
        self.lib.C843_CST(self.ild, channels, stages)


    @Action()
    def initialize_axes(self):
        self.lib.C843_INI(self.ild, self.axes)


    def qsai(self):
        """Configured Stages."""
        length = 32
        axes = (ct.c_char*length)()
        length = ct.c_int(length)
        error = self.lib.C843_qSAI(self.ild, axes, length)
        print("qSAI -> %s" %  _ERRORS[error])
        print(axes[:32])


    @DictFeat()
    def position(self, axis):
        """Move axes.
        """
        axes = ct.c_char_p(str(axis))
        pos = (ct.c_double*3)()
        self.lib.C843_qMOV(self.ild, axes, pos)

    @position.setter
    def position(self, axis, value):
        """Move axes."""
        axes = ct.c_char_p(str(axis))
        valuearr = (ct.c_double*1)(value)
        self.lib.C843_MOV(self.ild, axes, valuearr)


    @action 
    def mvr(self, ax, value):
        """Move axes."""
        axes = ct.c_char_p(str(ax))
        valuearr = (ct.c_double*1)(value)
        self.lib.C843_MVR(self.ild, axes, valuearr)

    @position
    def position(self, axis):
        """Move axes."""
        axes = ct.c_char_p(str(axis))
        pos = (ct.c_double*1)()
        self.lib.C843_qPOS(self.ild, axes, pos)
        
    @position.setter
    def position(self, axis, value):
        """Move axes."""
        axes = ct.c_char_p(str(axis))
        valuearr = (ct.c_double*3)(value)
        self.lib.C843_POS(self.ild, axes, valuearr)

    @dictfeat    
    def has_arrived(self, axis):
        """Check if the given axis has reached target position.
        """
        axes = ct.c_char_p(str(axis))
        state = (ct.c_bool*1)()
        self.lib.C843_qONT(self.ild, axes, state)
        return state[:]

    @action
    def move_(self, axis):
        """Move to positive limit switch."""
        axes = ct.c_char_p(str(axis))
        self.lib.C843_MPL(self.ild, axes)

    def mnl(self, axis):
        """Move to negative limit switch."""
        axes = ct.c_char_p(str(axis))
        self.lib.C843_MNL(self.ild, axes)

    @dictfeat
    def has_reference(self, axis):
        """Check if the given axis has a reference."""
        axes = ct.c_char_p(str(axis))
        state = (ct.c_bool*1)()
        error = self.lib.C843_qREF(self.ild, axes, state)
        return state[0]

    @has_reference.setter
    def ref(self, axis):
        """Reference move of axes."""
        axes = ct.c_char_p(str(axis))
        self.lib.C843_REF(self.ild, axes)


    def refmode(self, axis, state):
        """Sets reference mode of given axes."""
        axes = ct.c_char_p(str(axis))
        state = (ct.c_bool*1)(state)
        error = self.lib.C843_RON(self.ild, axes, state)


    def isrefok(self, ax):
        """Check the reference status for the given axes."""
        axes = ct.c_char_p(str(ax))
        state = (ct.c_bool*1)()
        error = self.lib.C843_IsReferenceOK(self.ild, axes, state)
        print("IsReferenceOK -> %s" %  _ERRORS[error])
        print(state[:])
        return state[0]

    @dictfeat
    def has_limits(self, axis):
        """Check if the given axis has limit switches."""
        axes = ct.c_char_p(str(axis))
        state = (ct.c_bool*1)()
        error = self.lib.C843_qLIM(self.ild, axes, state)
        print("LIM? -> %s" %  _ERRORS[error])


    @DictFeat(values=((True, False),))
    def servo_control_enabled(self, axis):
        """Query servo-control state.
        """
        axes = ct.c_char_p(str(axis))
        state = (ct.c_bool*3)()
        self.lib.C843_qSVO(self.ild, axes, state)

    @servo_control.setter
    def servo_control(self, axis, state):
        """Sets servo-control ON or OFF.
        """
        axes = ct.c_char_p(str(axis))
        state = (ct.c_bool*1)(state)
        self.lib.C843_SVO(self.ild, axes, state)

    def qspa(self, ax, param):
        """Read axes parameters.

            Parameters:
                        1 : "P-Term",
                        2 : "i-Term",
                        3 : "D-Term",
                        4 : "i-Limit",
                        11 : "max. Acceleration",
                        10 : "max. Velocity",
                        14 : "Conversion Factor"
        """
        axes = ct.c_char_p(str(ax))
        _params = {
                    1 : "P-Term",
                    2 : "i-Term",
                    3 : "D-Term",
                    4 : "i-Limit",
                    11 : "max. Acceleration",
                    10 : "max. Velocity",
                    14 : "Numerator of the Conversion Factor", # num./denom.=counts/mm
                    15 : "Denominator of the Conversion Factor", # num./denom.=counts/mm
                    20 : "Stage has a reference",
                    21 : "Maximum travel range in pos. direction",
                    48 : "Maximum travel range in neg. direction",
                    }

        params = [param]
        params = (ct.c_int*len(params))(*params)
        values = (ct.c_double*len(params))()
        stagenames = (ct.c_char*1)()
        length = ct.c_int(1)
        state = ct.c_bool(0)
        error = self.lib.C843_qSPA(self.ild, axes, params, values, stagenames, length)
        print("Stage %d %s : %d" % (ax, _params[param], values[0]))

    @Feat()
    def error(self):
        """Get Error.
        """
        error_code = self.lib.C843_GetError(self.ild)
        return error_code, self.translate_error(error_code)

    @Action()
    def translate_error(self, error_code):
        """Translate error code to error message.
        """
        ret, msg = self.lib.C843_TranslateError(error_code, *RetStr(128))
        return msg

if __name__ == '__main__':
    from time import sleep
from c843 import C843


def props(ax):
    """Read parameters for axis."""
    stage.qspa(ax, 1)
    stage.qspa(ax, 2)
    stage.qspa(ax, 3)
    stage.qspa(ax, 4)
    stage.qspa(ax, 11)
    stage.qspa(ax, 10)
    stage.qspa(ax, 14)
    stage.qspa(ax, 15)
    stage.qspa(ax, 20)
    stage.qspa(ax, 21)
    stage.qspa(ax, 48)

stage = C843()
stage.connect()
stage.isconnected()

stage.idn()

stage.cst()
stage.qcst()

stage.init()

#chn = 2
chn = (1, 2, 3, 4)
#chn = (1, 2, 3)

for i in chn:
    props(i)
    #if i == 4:
    #_ref = stage.qref(i)
    #else:
    #_lim = stage.qlim(i)
    _ref = stage.qref(i)
    #_lim = stage.qlim(i)
    stage.geterror()
    sleep(2)

for i in chn:
    if stage.isrefok(i) is False:
        if _ref == True:
            stage.ref(i)
            #if _lim == True:
            #stage.mpl(i)

        #for i in chn:
        #if chn == 4:
        #stage.ref(i)
        #else:
        #stage.mpl(i)
        #sleep(1)

inp = None
chan = 1
while inp != 'quit':
    chan = raw_input("Channel ({}): ".format(chan) )
    inp = raw_input("Position ({}): ".format(inp) )
    try:
        target_position = float(inp)
        if chan in (1,2,3):
            if target_position <= 14 and target_position >= 0:
                stage.mov(chan, target_position)
                stage.geterror()
                sleep(1)
            else:
                print("Position must be a number in the 0..14 range")
        else:
            stage.mov(chan, target_position)
            stage.geterror()
            sleep(1)
    except:
        print("Input should be a float or QUIT")

#stage.mov(chn, target_position)
#sleep(2)
#stage.qont(chn)
#stage.qpos(chn)

stage.disconnect()







