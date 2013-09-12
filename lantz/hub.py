__author__ = 'grecco'




class Hub(object):


    def __init__(self):

        #: name to instantiated device driver or Proxy
        self.devices = {}


    def add_device(self, name, device_class, args, kwargs, depends_on=None, run_on=''):
        """

        :param name:
        :param device_class:
        :param args:
        :param kwargs:
        :param depends_on:
        :param run_on: 'current' or 'thread' or 'process' or remote address
        :return:
        """

    def initialize_devices(self):
        pass

    def finalize_devices(self):
        pass
