# -*- coding: utf-8 -*-
"""
    lantz.stats
    ~~~~~~~~~~~

    Implements an statistical accumulator

    :copyright: 2012 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from collections import namedtuple

#: Data structure
Stats = namedtuple('Stats', 'last count mean std min max')


def stats(state):
    """Return the statistics for given state.

    :param state: state
    :type state: RunningState
    :return: statistics
    :rtype: Stats named tuple

    """
    if not state.count:
        return Stats(0, 0, 0, 0, 0, 0)

    mean = state.sum / state.count
    std = (float(state.sum2 - 2.0 * state.sum * mean + state.count * mean ** 2.0) / float(state.count)) ** 0.5
    return Stats(state.last, state.count,
                 mean, std, state.min, state.max)


class RunningState(object):
    """Accumulator for events.

    :param value: first value to add.
    """

    def __init__(self, value=None):
        if value is not None:
            self.add(value)

    def __getattr__(self, key):
        if key in ('last', 'count', 'sum', 'sum2'):
            return 0
        if key == 'min':
            return float('inf')
        if key == 'max':
            return float('-inf')
        raise AttributeError('{} is not a valid attribute of RunningState'.format(key))

    def add(self, value):
        """Add to the accumulator.

        :param value: value to be added.
        """
        self.last = value
        self.count += 1
        self.sum += value
        self.sum2 += value * value
        self.min = min(self.min, value)
        self.max = max(self.max, value)


class RunningStats(dict):
    """Accumulator for categorized event statistics.
    """

    def add(self, key, value):
        """Add an event to a given accumulator.

        :param key: category to which the event should be added.
        :param value: value of the event.
        """
        if key in self:
            super().__getitem__(key).add(value)
        else:
            super().__setitem__(key, RunningState(value))

    def stats(self, key):
        """Return the statistics for the current accumulator.

        :rtype: Stats.
        """
        return stats(super().__getitem__(key))
