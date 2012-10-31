import unittest
from time import sleep

from lantz import Driver, Feat, DictFeat, Action, Q_
from lantz.feat import MISSING

class aDriver(Driver):

    @Action()
    def run(self):
        return 42

    @Action()
    def run2(self, value):
        return 42 * value

    @Action()
    def run3(self, value):
        return 42 * value

    @Action(units='ms')
    def run4(self, value):
        return value

    @Action(values=({1, 2, 3}, {'a': 1, 'b': 2}, str))
    def run5(self, x, y, z):
        return x, y, z


class ActionTest(unittest.TestCase):

    def test_action(self):
        obj = aDriver()
        self.assertEqual(obj.run(), 42)
        self.assertEqual(obj.run2(2), 42 * 2)
        self.assertEqual(obj.run3(3), 42 * 3)
        self.assertEqual(obj.run4(Q_(3, 'ms')), 3)
        self.assertEqual(obj.run4(Q_(3, 's')), 3000)

    def test_action_async(self):
        obj = aDriver()
        fut = obj.run_async()
        self.assertEqual(fut.result(), 42)
        fut = obj.run2_async(2)
        self.assertEqual(fut.result(), 42 * 2)

    def test_multiple_values(self):
        obj = aDriver()
        self.assertEqual(obj.run5(1, 'a', 3), (1, 1, '3'))

    def test_instance_specific(self):
        x = aDriver()
        y = aDriver()
        val = Q_(3, 's')
        self.assertEqual(x.run4(val), y.run4(val))
        x.actions.run4.units = 's'
        self.assertNotEqual(x.run4(val), y.run4(val))
        self.assertEqual(x.run4(val), 3)


if __name__ == '__main__':
    unittest.main()
