
import time
import logging
import unittest

from lantz import Driver, Feat, Q_
from lantz.feat import MISSING
from lantz.log import get_logger

class MemHandler(logging.Handler):

    def __init__(self):
        super().__init__()
        self.setFormatter(logging.Formatter(style='{'))
        self.history = list()

    def emit(self, record):
        self.history.append(self.format(record))


class FeatTest(unittest.TestCase):

    # Modified from python quantities test suite
    def assertQuantityEqual(self, q1, q2, msg=None, delta=None):
        """
        Make sure q1 and q2 are the same quantities to within the given
        precision.
        """

        if isinstance(q1, (list, tuple)):
            for first, second in zip(q1, q2):
                self.assertQuantityEqual(first, second)
            return

        delta = 1e-5 if delta is None else delta
        msg = '' if msg is None else ' (%s)' % msg

        q1 = Q_(q1)
        q2 = Q_(q2)

        d1 = getattr(q1, '_dimensionality', None)
        d2 = getattr(q2, '_dimensionality', None)
        if (d1 or d2) and not (d1 == d2):
            raise self.failureException(
                "Dimensionalities are not equal (%s vs %s)%s" % (d1, d2, msg)
                )

    def test_readonly(self):

        class Spam(Driver):

            @Feat
            def eggs(self_):
                return 3

        obj = Spam()
        self.assertEqual(obj.eggs, 3)
        self.assertRaises(AttributeError, setattr, obj, "eggs", 3)
        self.assertRaises(AttributeError, delattr, obj, "eggs")

    def test_writeonly(self):

        class Spam(Driver):

            _eggs = None

            eggs = Feat()
            @eggs.setter
            def eggs(self_, value):
                self_._eggs = value

            _eggs2 = None

            @Feat(None)
            def eggs2(self_, value):
                self_._eggs2 = value

        obj = Spam()
        self.assertRaises(AttributeError, getattr, obj, "eggs")
        self.assertEqual(setattr(obj, "eggs", 3),  None)
        self.assertEqual(obj._eggs, 3)
        self.assertRaises(AttributeError, delattr, obj, "eggs")

        self.assertRaises(AttributeError, getattr, obj, "eggs2")
        self.assertEqual(setattr(obj, "eggs2", 3),  None)
        self.assertEqual(obj._eggs2, 3)
        self.assertRaises(AttributeError, delattr, obj, "eggs2")

    def test_readwrite(self):

        class Spam(Driver):

            _eggs = 8

            @Feat
            def eggs(self_):
                return self_._eggs

            @eggs.setter
            def eggs(self_, value):
                self_._eggs = value

        obj = Spam()
        self.assertEqual(obj.eggs, 8)
        self.assertEqual(setattr(obj, "eggs", 3), None)
        self.assertEqual(obj._eggs, 3)
        self.assertEqual(obj.eggs, 3)
        self.assertRaises(AttributeError, delattr, obj, "eggs")

    def test_read_once(self):

        class Spam(Driver):

            _serialno = 23199292

            @Feat(read_once=True)
            def serialno(self):
                if hasattr(self, '_read'):
                    raise Exception
                self._read = True
                return self._serialno

        obj = Spam()
        self.assertEqual(obj.serialno, 23199292)
        self.assertEqual(obj.serialno, 23199292)

    def test_limits(self):

        class Spam(Driver):

            _eggs = 8

            @Feat(limits=(1, 10, 1))
            def eggs(self_):
                return self_._eggs

            @eggs.setter
            def eggs(self_, value):
                self_._eggs = value

        obj = Spam()
        obj.eggs = 2.2
        self.assertEqual(obj.eggs, 2)
        self.assertRaises(ValueError, setattr, obj, "eggs", 11)
        self.assertRaises(ValueError, setattr, obj, "eggs", 0)

    def test_limits_tuple(self):

        class Spam(Driver):

            _eggs = 8

            @Feat(limits=((1, 10, 1), (3, 5, .5)))
            def eggs(self_):
                return self_._eggs

            @eggs.setter
            def eggs(self_, value1_value2):
                self_._eggs = value1_value2

        obj = Spam()
        obj.eggs = (2.2, 3.8)
        self.assertEqual(obj.eggs, (2, 4))
        self.assertRaises(ValueError, setattr, obj, "eggs", (11, 3))
        self.assertRaises(ValueError, setattr, obj, "eggs", (4, 7))

    def test_cache(self):

        class Spam(Driver):

            def __init__(self_):
                self_._eggs = 9

            @Feat
            def eggs(self_):
                return self_._eggs

            @eggs.setter
            def eggs(self_, value):
                self_._eggs = value

        obj = Spam()
        self.assertEqual(obj.recall("eggs"), MISSING)
        self.assertEqual(obj.eggs, 9)
        self.assertEqual(obj.recall("eggs"), 9)
        self.assertEqual(setattr(obj, "eggs", 10), None)
        self.assertEqual(obj._eggs, 10)
        self.assertEqual(obj.eggs, 10)
        self.assertEqual(obj.recall("eggs"), 10)
        obj._eggs = 0
        self.assertEqual(obj.recall("eggs"), 10)
        self.assertEqual(obj.eggs, 0)
        self.assertEqual(obj.recall("eggs"), 0)

    def test_logger(self):

        hdl = MemHandler()

        logger = get_logger('lantz.driver', False)
        logger.addHandler(hdl)
        logger.setLevel(logging.DEBUG)

        class Spam(Driver):

            @Feat
            def eggs(self_):
                return 9

            @eggs.setter
            def eggs(self_, value):
                pass

        obj = Spam()
        x = obj.eggs
        obj.eggs = x
        obj.eggs = x + 1

        self.assertEqual(hdl.history, ['Created',
                                       'Getting eggs',
                                       '(raw) Got 9 for eggs',
                                       'Got 9 for eggs',
                                       'No need to set eggs = 9 (current=9, force=False)',
                                       'Setting eggs = 10 (current=9, force=False)',
                                       '(raw) Setting eggs = 10',
                                       'eggs was set to 10'])

    def test_units(self):

        hdl = MemHandler()

        class Spam(Driver):
            _logger = get_logger('test.feat', False)
            _logger.addHandler(hdl)
            _logger.setLevel(logging.DEBUG)

            _eggs = 8

            @Feat(units='s')
            def eggs(self_):
                return self_._eggs

            @eggs.setter
            def eggs(self_, value):
                self.assertEqual(type(value), float)
                self.assertEqual(value, float(value))
                self_._eggs = value

            _eggs_str = '8'

            @Feat(units='s')
            def eggs_str(self_):
                return self_._eggs_str

            @eggs_str.setter
            def eggs_str(self_, value):
                self.assertEqual(type(value), float)
                self.assertEqual(value, float(value))
                self_._eggs_str = str(value)

            _eggs_adim = '8'

            @Feat(units=float)
            def eggs_adim(self_):
                return self_._eggs_adim

            @eggs_adim.setter
            def eggs_adim(self_, value):
                self.assertEqual(type(value), float)
                self.assertEqual(value, float(value))
                self_._eggs_adim = str(value)

        obj = Spam()
        self.assertQuantityEqual(obj.eggs, Q_(8, 's'))
        self.assertEqual(setattr(obj, "eggs", Q_(3, 'ms')), None)
        self.assertQuantityEqual(obj.eggs, Q_(3 / 1000, 's'))
        self.assertEqual(setattr(obj, "eggs", 3), None)

        self.assertQuantityEqual(obj.eggs_str, Q_(8, 's'))
        self.assertEqual(setattr(obj, "eggs_str", Q_(3, 'ms')), None)
        self.assertQuantityEqual(obj.eggs_str, Q_(3 / 1000, 's'))
        self.assertEqual(setattr(obj, "eggs_str", 3), None)

        self.assertQuantityEqual(obj.eggs_adim, 8)
        self.assertEqual(setattr(obj, "eggs_adim",3), None)
        self.assertQuantityEqual(obj.eggs_adim, 3)

    def test_units_tuple(self):

        hdl = MemHandler()

        class Spam(Driver):
            _logger = get_logger('test.feat', False)
            _logger.addHandler(hdl)
            _logger.setLevel(logging.DEBUG)

            _eggs = (8, 1)

            # Transform each element of the return vector
            # based on the set signature
            @Feat(units=('s', 's'))
            def eggs(self_):
                return self_._eggs

            @eggs.setter
            def eggs(self_, values):
                self_._eggs = values

        class Spam2(Driver):
            _logger = get_logger('test.feat', False)
            _logger.addHandler(hdl)
            _logger.setLevel(logging.DEBUG)

            _eggs = (8, 1)

            # Transform each element of the return vector
            # based on the set signature
            @Feat(units=('s', None))
            def eggs(self_):
                return self_._eggs

            @eggs.setter
            def eggs(self_, values):
                self_._eggs = values

        obj = Spam()
        self.assertQuantityEqual(obj.eggs, (Q_(8, 's'),  Q_(1, 's')))
        self.assertEqual(setattr(obj, "eggs", (Q_(3, 'ms'), Q_(4, 'ms'))), None)
        self.assertQuantityEqual(obj.eggs, (Q_(3 / 1000, 's'), Q_(4 / 1000, 's')))
        self.assertEqual(setattr(obj, "eggs", (3, 1)), None)

        obj = Spam2()
        self.assertQuantityEqual(obj.eggs, (Q_(8, 's'),  1))
        self.assertEqual(setattr(obj, "eggs", (Q_(3, 'ms'), 4)), None)
        self.assertQuantityEqual(obj.eggs, (Q_(3 / 1000, 's'), 4))

    def test_of_instance(self):

        class Spam(Driver):

            def __init__(self_):
                super().__init__()
                self_._eggs = 9

            @Feat()
            def eggs(self_):
                return self_._eggs

            @eggs.setter
            def eggs(self_, value):
                self_._eggs = value

        obj = Spam()
        obj2 = Spam()

        self.assertEqual(obj.recall("eggs"), MISSING)
        self.assertEqual(obj.eggs, 9)
        self.assertEqual(obj.recall("eggs"), 9)
        self.assertEqual(setattr(obj, "eggs", 10), None)
        self.assertEqual(obj._eggs, 10)
        self.assertEqual(obj.eggs, 10)
        self.assertEqual(obj.recall("eggs"), 10)
        obj._eggs = 0
        self.assertEqual(obj.recall("eggs"), 10)
        self.assertEqual(obj.eggs, 0)
        self.assertEqual(obj.recall("eggs"), 0)
        self.assertEqual(obj2.recall("eggs"), MISSING)

    def test_timming(self):

        class Spam(Driver):

            def __init__(self_):
                super().__init__()
                self_._eggs = 9

            @Feat
            def eggs(self_):
                time.sleep(.01)
                return self_._eggs

            @eggs.setter
            def eggs(self_, value):
                time.sleep(.02)
                self_._eggs = value

        obj = Spam()
        for n in range(50):
            x = obj.eggs
        for n in range(100):
            obj.eggs = n
        self.assertEqual(obj.timing.stats('get_eggs').count, 50)
        self.assertEqual(obj.timing.stats('set_eggs').count, 100)

    def test_in_instance(self):

        class Spam(Driver):

            @Feat(units='ms')
            def eggs(self_):
                return 9

        x = Spam()
        y = Spam()
        self.assertEqual(str(x.eggs.units), 'millisecond')
        self.assertEqual(x.feats.eggs.units, y.feats.eggs.units)
        self.assertEqual(x.eggs, y.eggs)
        x.feats.eggs.units = 's'
        self.assertNotEqual(x.feats.eggs.units, y.feats.eggs.units)
        self.assertNotEqual(x.eggs, y.eggs)
        self.assertEqual(str(x.eggs.units), 'second')



if __name__ == '__main__':
    unittest.main()
