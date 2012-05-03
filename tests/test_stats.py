import unittest

import numpy as np

from lantz.stats import RunningStats


class StatsTest(unittest.TestCase):

    def test_grouping(self):
        x = RunningStats()
        for key in ('first', 'second'):
            values = np.random.random(20)
            for ndx, value in enumerate(values, 1):
                x.add(key, value)
                s = x.stats(key)

                self.assertAlmostEqual(x[key].last, value)
                self.assertAlmostEqual(x[key].count, ndx)
                self.assertAlmostEqual(x[key].sum, np.sum(values[:ndx]))
                self.assertAlmostEqual(x[key].sum2, np.sum(values[:ndx] ** 2))
                self.assertAlmostEqual(x[key].min, np.min(values[:ndx]))
                self.assertAlmostEqual(x[key].max, np.max(values[:ndx]))

                self.assertAlmostEqual(s.last, value)
                self.assertAlmostEqual(s.count, ndx)
                self.assertAlmostEqual(s.mean, np.mean(values[:ndx]))
                self.assertAlmostEqual(s.std, np.std(values[:ndx]))
                self.assertAlmostEqual(s.min, np.min(values[:ndx]))
                self.assertAlmostEqual(s.max, np.max(values[:ndx]))
