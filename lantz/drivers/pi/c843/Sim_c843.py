import ctypes as ct
import numpy as np
from time import sleep


_ERRORS = {
        4: "ID 4",
        3: "ID 3",
        2: "ID 2",
        1: "1",
        0: "Success",
        -1: "COM_ERROR",
        }

class C843(object):
    def __init__(self):
        #self.stage = ct.WinDLL("C843_GCS_DLL.dll")
        #self.ild = ct.c_int(9)
        self.board = ct.c_int(1) 
        self.ild = 0 

    def connect(self):
        """Initialise Library."""
        self.ild = 1
        print("Connect to ID -> %s" %  self.ild)

    def disconnect(self):
        """Initialise Library."""
        print("Close Connection Board -> %s" %  self.board.value)

    def isconnected(self):
        """Initialise Library."""
        error = 0
        print("IsConnected -> %s" %  _ERRORS[error])

    def qcst(self):
        """Query Connected Stages."""
        channels = ct.c_char_p("123")
        length = ct.c_int(40)
        stages = (ct.c_char*40)()
        #error = self.stage.C843_qCST(self.ild, channels, stages, length)
        error = 0
        print("qCST -> %s" %  _ERRORS[error])

    def cst(self):
        """Connect Stages."""
        channels = ct.c_char_p("123")
        stages = ct.c_char_p("M-111.1DG\nM-111.1DG\nM-116.DG")
        #error = self.stage.C843_CST(self.ild, channels, stages)
        error = 0
        print("CST -> %s" %  _ERRORS[error])

    def qsai(self):
        """Configured Stages."""
        length = 32
        axes = (ct.c_char*length)()
        length = ct.c_int(length)
        #error = self.stage.C843_qSAI(self.ild, axes, length)
        error = 0
        print("qSAI -> %s" %  _ERRORS[error])
        print(axes[:32])

    def idn(self):
        """*IDN?."""
        length = 64 
        axes = (ct.c_char*length)()
        length = ct.c_int(length)
        #error = self.stage.C843_qIDN(self.ild, axes, length)
        error = 0
        print("IDN -> %s" %  _ERRORS[error])
        print(axes[:])

    def init(self):
        """Initialize axes."""
        axes = ct.c_char_p("123")
        #error = self.stage.C843_INI(self.ild, axes)
        error = 0
        print("INI -> %s" %  _ERRORS[error])

    def qmov(self, ax):
        """Move axes."""
        axes = ct.c_char_p(str(ax))
        pos = (ct.c_double*3)()
        #error = self.stage.C843_qMOV(self.ild, axes, pos)
        error = 0
        print("qMOV -> %s" %  _ERRORS[error])
        print(pos[:])
        print("MOV? = %d" % pos[ax-1])

    def mov(self, ax, value):
        """Move axes."""
        axes = ct.c_char_p(str(ax))
        valuearr = (ct.c_double*1)(value)
        #error = self.stage.C843_MOV(self.ild, axes, valuearr)
        error = 0
        print("MOV -> %s" %  _ERRORS[error])

    def mvr(self, ax, value):
        """Move axes."""
        axes = ct.c_char_p(str(ax))
        valuearr = (ct.c_double*1)(value)
        #error = self.stage.C843_MVR(self.ild, axes, valuearr)
        error = 0
        print("MVR -> %s" %  _ERRORS[error])
        print("MVR = %d" % value)

    def qont(self, ax):
        """Check if the given axis has reached target position."""
        axes = ct.c_char_p(str(ax))
        state = (ct.c_bool*1)()
        #error = self.stage.C843_qONT(self.ild, axes, state)
        error = 0
        print("ONT? -> %s" %  _ERRORS[error])
        print(state[:])

    def qpos(self, ax):
        """Move axes."""
        axes = ct.c_char_p(str(ax))
        pos = (ct.c_double*1)()
        #error = self.stage.C843_qPOS(self.ild, axes, pos)
        error = 0
        print("qPOS -> %s" %  _ERRORS[error])
        print("POS? = %d" % pos[0])

    def pos(self, ax, value):
        """Move axes."""
        axes = ct.c_char_p(str(ax))
        valuearr = (ct.c_double*3)(value)
        #error = self.stage.C843_POS(self.ild, axes, valuearr)
        error = 0
        print("POS -> %s" %  _ERRORS[error])
        print(valuearr[:])
        print("POS = %d" % value)

    def mpl(self, ax):
        """Move to positive limit switch."""
        axes = ct.c_char_p(str(ax))
        state = ct.c_bool(0)
        #error = self.stage.C843_MPL(self.ild, axes)
        error = 0
        print("MPL -> %s" %  _ERRORS[error])
        #self.stage.C843_IsReferencing(self.ild, axes, state)
        #while state:
            #self.stage.C843_IsReferencing(self.ild, axes, state)
            #print("Referencing \b")

    def mnl(self, ax):
        """Move to negative limit switch."""
        axes = ct.c_char_p(str(ax))
        state = ct.c_bool(0)
        #error = self.stage.C843_MNL(self.ild, axes)
        error = 0
        print("MNL -> %s" %  _ERRORS[error])
       #print("Referenced")

    def ref(self, ax):
        """Reference move of axes."""
        axes = ct.c_char_p(str(ax))
        state = ct.c_bool(0)
        #error = self.stage.C843_REF(self.ild, axes)
        error = 0
        print("REF -> %s" %  _ERRORS[error])

    def refmode(self, ax, state):
        """Sets reference mode of given axes."""
        axes = ct.c_char_p(str(ax))
        state = (ct.c_bool*1)(state)
        #error = self.stage.C843_RON(self.ild, axes, state)
        error = 0
        print("RON -> %s" %  _ERRORS[error])

    def qref(self, ax):
        """Check if the given axis has a reference."""
        axes = ct.c_char_p(str(ax))
        state = (ct.c_bool*1)()
        #error = self.stage.C843_qREF(self.ild, axes, state)
        error = 0
        print("REF? -> %s" %  _ERRORS[error])
        print(state[:])
        return state[0]

    def isrefok(self, ax):
        """Check the reference status for the given axes."""
        axes = ct.c_char_p(str(ax))
        state = (ct.c_bool*1)()
        #error = self.stage.C843_IsReferenceOK(self.ild, axes, state)
        error = 0
        print("IsReferenceOK -> %s" %  _ERRORS[error])
        print(state[:])
        return state[0]

    def qlim(self, ax):
        """Check if the given axis has limit switches."""
        axes = ct.c_char_p(str(ax))
        state = (ct.c_bool*1)()
        #error = self.stage.C843_qLIM(self.ild, axes, state)
        error = 0
        print("LIM? -> %s" %  _ERRORS[error])
        print(state[:])
        return state[0]

    def svo(self, ax, state):
        """Sets servo-control ON or OFF."""
        axes = ct.c_char_p(str(ax))
        state = (ct.c_bool*1)(state)
        #error = self.stage.C843_SVO(self.ild, axes, state)
        error = 0
        print("SERVO -> %s" %  _ERRORS[error])

    def qsvo(self, ax):
        """Query servo-control state."""
        axes = ct.c_char_p(str(ax))
        state = (ct.c_bool*3)()
        #error = self.stage.C843_qSVO(self.ild, axes, state)
        error = 0
        print("SERVO STATE -> %s" %  _ERRORS[error])
        print(state[:])

    def geterror(self):
        """Get Error."""
        length = 128
        errmsg = (ct.c_char*length)()
        #error = self.stage.C843_GetError(self.ild)
        error = 0
        self.stage.C843_TranslateError(ct.c_int(error), errmsg, ct.c_int(length-1))
        print("Error message : %s" %  errmsg[:])

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
        #error = self.stage.C843_qSPA(self.ild, axes, params, values, stagenames, length)
        error = 0
        print("Stage %d %s : %d" % (ax, _params[param], values[0]))
