import unittest
from time import sleep

from lantz import Driver, Feat, DictFeat, Action, Q_

SLEEP = .1
WAIT = .2


class aDriver(Driver):

    def __init__(self, slow=False, *args, **kwargs):
        super().__init__()
        self.slow = slow
        self._eggs = None
        self._ham = None

    @Feat
    def eggs(self):
        if self.slow:
            sleep(SLEEP)
        return self._eggs

    @eggs.setter
    def eggs(self, value):
        if self.slow:
            sleep(SLEEP)
        self._eggs = value

    @Feat
    def ham(self):
        if self.slow:
            sleep(SLEEP)
        return self._ham

    @ham.setter
    def ham(self, value):
        if self.slow:
            sleep(SLEEP)
        self._ham = value

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


class DriverTest(unittest.TestCase):

    def test_repr_str(self):

        class bDriver(aDriver):
            pass

        obj1 = bDriver()
        self.assertEqual(str(obj1), "bDriver bDriver0")
        self.assertEqual(repr(obj1), "<bDriver('bDriver0')>")
        obj2 = bDriver()
        self.assertEqual(str(obj2), "bDriver bDriver1")
        self.assertEqual(repr(obj2), "<bDriver('bDriver1')>")

        obj3 = bDriver(name='first')
        self.assertEqual(str(obj3), "bDriver first")
        self.assertEqual(repr(obj3), "<bDriver('first')>")

        obj3.name = 'second'
        self.assertEqual(str(obj3), "bDriver second")
        self.assertEqual(repr(obj3), "<bDriver('second')>")

    def test_update_kw(self):
        "Update using keyword arguments"
        obj = aDriver()
        obj.update(eggs=1)
        self.assertEqual(obj.eggs, 1)

        obj.update(eggs=2, ham=21)
        self.assertEqual(obj.eggs, 2)
        self.assertEqual(obj.ham, 21)

    def test_update_dict(self):
        "Update using a dictionary"
        obj = aDriver()
        obj.update({'eggs': 3})
        self.assertEqual(obj.eggs, 3)

        obj.update({'eggs': 4, 'ham': 22})
        self.assertEqual(obj.eggs, 4)
        self.assertEqual(obj.ham, 22)

    def test_update_async_kw(self):
        "Update async using keyword arguments"
        obj = aDriver(True)
        obj.update_async(eggs=1)
        self.assertNotEqual(obj._eggs, 1)
        sleep(SLEEP + WAIT)
        self.assertEqual(obj._eggs, 1)

        obj.update_async(eggs=2, ham=21)
        self.assertNotEqual(obj._eggs, 2)
        self.assertNotEqual(obj._ham, 21)
        sleep(2 * SLEEP + WAIT)
        self.assertEqual(obj._eggs, 2)
        self.assertEqual(obj._ham, 21)

    def test_update_async_dict(self):
        "Update async using a dictionary"
        obj = aDriver(True, name='test_update_async_dict')
        obj.update_async({'eggs': 3})
        self.assertNotEqual(obj._eggs, 3)
        sleep(SLEEP + WAIT)
        self.assertEqual(obj._eggs, 3)

        obj.update_async({'eggs': 4, 'ham': 22})
        self.assertNotEqual(obj._eggs, 4)
        self.assertNotEqual(obj._ham, 22)
        sleep(2 * SLEEP + WAIT)
        self.assertEqual(obj._eggs, 4)
        self.assertEqual(obj._ham, 22)

    def test_update_async_unfinished_tasks(self):
        obj = aDriver(True)
        self.assertEqual(obj.unfinished_tasks, 0)
        obj.update_async({'eggs': 4})
        self.assertEqual(obj.unfinished_tasks, 1)
        sleep(SLEEP + WAIT)
        self.assertEqual(obj.unfinished_tasks, 0)
        obj.update_async({'eggs': 5})
        obj.update_async({'ham': 23})
        self.assertEqual(obj.unfinished_tasks, 2)
        sleep(2 * SLEEP + WAIT)
        self.assertEqual(obj.unfinished_tasks, 0)

    def test_refresh(self):
        obj = aDriver()
        obj._eggs = 1
        self.assertEqual(obj.refresh('eggs'), 1)
        obj._eggs = 2
        obj._ham = 22
        self.assertEqual(obj.refresh(('eggs', 'ham')), (2, 22))
        obj._eggs = 3
        obj._ham = 23
        self.assertEqual(obj.refresh({'eggs': None, 'ham': None}), {'eggs': 3, 'ham': 23})

    def test_refresh_async(self):
        obj = aDriver()
        obj._eggs = 1
        fut = obj.refresh_async('eggs')
        self.assertEqual(fut.result(), 1)
        obj._eggs = 2
        obj._ham = 22
        fut = obj.refresh_async(('eggs', 'ham'))
        self.assertEqual(fut.result(), (2, 22))
        obj._eggs = 3
        obj._ham = 23
        fut = obj.refresh_async({'eggs': None, 'ham': None})
        self.assertEqual(fut.result(), {'eggs': 3, 'ham': 23})

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


if __name__ == '__main__':
    unittest.main()
