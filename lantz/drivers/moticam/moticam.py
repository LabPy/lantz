import ctypes as ct


class Moticam(object):
    """FIXME
    """
    
    def __init__(self):
        self.cam = ct.WinDLL("MUCam32.dll")

    def camerafinder(self):
        pass



