import logging
import unittest

from lantz import Driver, DictFeat, Q_


from lantz.log import get_logger
from lantz.feat import  MISSING

class MemHandler(logging.Handler):

    def __init__(self):
        super().__init__()
        self.setFormatter(logging.Formatter(style='{'))
        self.history = list()

    def emit(self, record):
        self.history.append(self.format(record))


class DictFeatTest(unittest.TestCase):

    # Modified from python quantities test suite
    def assertQuantityEqual(self, q1, q2, msg=None, delta=None):
        """
        Make sure q1 and q2 are the same quantities to within the given
        precision.
        """

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

            _eggs = {'answer': 42}

            @DictFeat()
            def eggs(self_, key):
                return self_._eggs[key]

        obj = Spam()
        self.assertEqual(obj.eggs['answer'], 42)
        self.assertRaises(AttributeError, setattr, obj, "eggs", 3)
        self.assertRaises(AttributeError, delattr, obj, "eggs")

    def test_writeonly(self):

        class Spam(Driver):

            _eggs = {'answer': 42}

            eggs = DictFeat()

            @eggs.setter
            def eggs(self_, key, value):
                self_._eggs[key] = value

            _eggs2 = {'answer': 42}

            @DictFeat(None)
            def eggs2(self_, key, value):
                self_._eggs2[key] = value

        obj = Spam()
        self.assertRaises(AttributeError, lambda x: obj.eggs['answer'], 1)
        obj.eggs['answer'] = 46
        self.assertEqual(obj._eggs['answer'], 46)
        self.assertRaises(AttributeError, delattr, obj, "eggs")

        self.assertRaises(AttributeError, lambda x: obj.eggs2['answer'], 1)
        obj.eggs2['answer'] = 46
        self.assertEqual(obj._eggs2['answer'], 46)
        self.assertRaises(AttributeError, delattr, obj, "eggs2")


    def test_readwrite(self):

        class Spam(Driver):

            _eggs = {'answer': 42}

            @DictFeat()
            def eggs(self_, key):
                return self_._eggs[key]

            @eggs.setter
            def eggs(self_, key, value):
                self_._eggs[key] = value

        obj = Spam()
        self.assertEqual(obj.eggs['answer'], 42)
        obj.eggs['answer'] = 46
        self.assertEqual(obj._eggs['answer'], 46)
        self.assertEqual(obj.eggs['answer'], 46)
        self.assertRaises(AttributeError, delattr, obj, "eggs")

    def test_cache(self):

        class Spam(Driver):

            _eggs = {'answer': 42}

            @DictFeat()
            def eggs(self_, key):
                return self_._eggs[key]

            @eggs.setter
            def eggs(self_, key, value):
                self_._eggs[key] = value

        obj = Spam()
        self.assertEqual(obj.recall("eggs"), {})
        self.assertEqual(obj.eggs['answer'], 42)
        # After reading 1 element, it is stored in the cache
        self.assertEqual(obj.recall("eggs"), {'answer': 42})
        obj.eggs['answer'] = 46
        self.assertEqual(obj._eggs['answer'], 46)
        self.assertEqual(obj.eggs['answer'], 46)
        self.assertEqual(obj.recall("eggs"), {'answer': 46})
        obj._eggs['answer'] = 0
        self.assertEqual(obj.recall("eggs"), {'answer': 46})
        self.assertEqual(obj.eggs['answer'], 0)
        self.assertEqual(obj.recall("eggs"), {'answer': 0})

    def test_logger(self):

        hdl = MemHandler()

        logger = get_logger('lantz.driver')
        logger.addHandler(hdl)
        logger.setLevel(logging.DEBUG)
        class Spam(Driver):

            _eggs = {'answer': 42}

            @DictFeat()
            def eggs(self_, key):
                return self_._eggs[key]

            @eggs.setter
            def eggs(self_, key, value):
                self_._eggs[key] = value

        obj = Spam()
        x = obj.eggs['answer']
        obj.eggs['answer'] = x
        obj.eggs['answer'] = x + 1
        self.assertEqual(hdl.history, ['Created',
                                       "Getting eggs['answer']",
                                       "(raw) Got 42 for eggs['answer']",
                                       "Got 42 for eggs['answer']",
                                       "No need to set eggs['answer'] = 42 (current=42, force=False)",
                                       "Setting eggs['answer'] = 43 (current=42, force=False)",
                                       "(raw) Setting eggs['answer'] = 43",
                                       "eggs['answer'] was set to 43"])

    def test_units(self):

        hdl = MemHandler()

        class Spam(Driver):
            _logger = get_logger('test.feat')
            _logger.addHandler(hdl)
            _logger.setLevel(logging.DEBUG)

            _eggs = {'answer': 42}

            @DictFeat(units='s')
            def eggs(self_, key):
                return self_._eggs[key]

            @eggs.setter
            def eggs(self_, key, value):
                self_._eggs[key] = value

        obj = Spam()
        self.assertQuantityEqual(obj.eggs['answer'], Q_(42, 's'))
        obj.eggs['answer'] = Q_(46, 'ms')
        self.assertQuantityEqual(obj.eggs['answer'], Q_(46 / 1000, 's'))
        obj.eggs['answer'] = 42

    def test_keys(self):

        class Spam(Driver):
            _eggs = {'answer': 42}

            @DictFeat(keys=('answer', ))
            def eggs(self_, key):
                return self_._eggs[key]

            @eggs.setter
            def eggs(self_, key, value):
                self_._eggs[key] = value

        obj = Spam()
        self.assertEqual(obj.eggs['answer'], 42)
        obj.eggs['answer'] = 46
        self.assertEqual(obj.eggs['answer'], 46)
        self.assertRaises(KeyError, lambda x: obj.eggs['spam'], None)

        def test(x):
            x.eggs['spam'] = 1
        self.assertRaises(KeyError, test, obj)

    def test_keys_mapping(self):

        class Spam(Driver):
            _eggs = {'answer': 42}

            @DictFeat(keys={28: 'answer'})
            def eggs(self_, key):
                return self_._eggs[key]

            @eggs.setter
            def eggs(self_, key, value):
                self_._eggs[key] = value

        obj = Spam()
        self.assertEqual(obj.eggs[28], 42)
        obj.eggs[28] = 46
        self.assertEqual(obj.eggs[28], 46)
        self.assertRaises(KeyError, lambda x: obj.eggs['spam'], None)
        self.assertRaises(KeyError, lambda x: obj.eggs['answer'], None)

    def test_of_instance(self):

        class Spam(Driver):

            def __init__(self_):
                super().__init__()
                self_._eggs = {1: 9}

            @DictFeat()
            def eggs(self_, key):
                return self_._eggs[key]

            @eggs.setter
            def eggs(self_, key, value):
                self_._eggs[key] = value

        obj = Spam()
        obj2 = Spam()

        self.assertEqual(obj.eggs.instance, obj)
        self.assertEqual(obj2.eggs.instance, obj2)

        self.assertEqual(obj.recall("eggs"), {})
        self.assertEqual(obj.eggs[1], 9)
        self.assertEqual(obj.recall("eggs"), {1: 9})
        obj.eggs[1] = 10
        self.assertEqual(obj._eggs[1], 10)
        self.assertEqual(obj.eggs[1], 10)
        self.assertEqual(obj.recall("eggs")[1], 10)
        obj._eggs = {1: 0}
        self.assertEqual(obj.recall("eggs")[1], 10)
        self.assertEqual(obj.eggs[1], 0)
        self.assertEqual(obj.recall("eggs")[1], 0)
        self.assertEqual(obj2.recall("eggs"), {})


    def test_in_instance(self):

        class Spam(Driver):

            @DictFeat(keys=(1, 2, 3), units='ms')
            def eggs(self_, key):
                return 9

        x = Spam()
        y = Spam()
        self.assertEqual(str(x.eggs[1].units), 'millisecond')
        self.assertEqual(x.feats.eggs[1].units, y.feats.eggs[1].units)
        self.assertEqual(x.eggs[1], y.eggs[1])
        x.feats.eggs[1].units = 's'
        self.assertNotEqual(x.feats.eggs[1].units, y.feats.eggs[1].units)
        self.assertNotEqual(x.eggs[1], y.eggs[1])
        self.assertEqual(str(x.eggs[1].units), 'second')
        self.assertEqual(str(x.eggs[2].units), 'millisecond')

if __name__ == '__main__':
    unittest.main()
