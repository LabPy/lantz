# -*- coding: utf-8 -*-
"""
    lantz.drivers.scpi
    ~~~~~~~~~~~~~~~~~~

    Implements the SCPI protocol.

    Standard Commands for Programmable Instruments

    :copyright: 2015 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from lantz import Action, Feat, Driver
from lantz.drivers.ieee4882 import IEEE4882Driver


def build_feat(command, **kwargs):
    """Builds a feat with with SCPI. Can be used as decorator
    for an empty function providing only the name and docstring.

    :param command: SCPI command

    Keyword arguments will be given to the Feat constructor.
    (e.g. units, limits, etc)

    Special behaviours for kwargs:
    - If the 'values' is a string, a set will be created by splitting on |


    Example:

        @build_feat('MEAS')
        def measure():
            "Meas docstring"

    If the command ends in ?, the Feat will be read only (no setter)
    If you want a write only Feat (no getter), append a ! to the command.
    (but consider if this is not actually an action)
    """

    if 'values' in kwargs and isinstance(kwargs['values'], str):
        kwargs['values'] = set(kwargs['values'].split('|'))

    def deco(func):

        nonlocal command
        if command.endswith('!'):
            command = command[:-1]
            getter = None
        else:
            def getter(self):
                return self.query(command + '?')

        if command.endswith('?'):
            setter = None
        else:
            def setter(self, value):
                return self.send(command + str(value))

        return Feat(getter, setter, doc=func.__doc__, **kwargs)

    return deco


class SCPIDriver(IEEE4882Driver):
    """Implements mandatory functions for a SCPI Device.

    You can use it as a mixin class.
    """
