import unittest
from time import sleep

from lantz import Driver, Feat, DictFeat, Action, Q_
from lantz.feat import MISSING
from lantz.driver import Self

SLEEP = .1
WAIT = .2


class aDriver(Driver):

    def __init__(self, slow=False, *args, **kwargs):
        super().__init__()
        self.slow = slow
        self._eggs = None
        self._ham = None

    @Feat()
    def eggs(self):
        if self.slow:
            sleep(SLEEP)
        return self._eggs

    @eggs.setter
    def eggs(self, value):
        if self.slow:
            sleep(SLEEP)
        self._eggs = value

    @Feat()
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

    def test_derived_class(self):

        class X(Driver):

            _val1 = 1

            @Feat()
            def feat1(self):
                return 'feat1'

            @Feat()
            def val1(self):
                return self._val1

            @val1.setter
            def val1(self, value):
                self._val1 = value

            @Action()
            def action1(self):
                return 'action1'

        class Y(X):

            _val2 = 1

            @Feat()
            def feat2(self):
                return 'feat2'

            @Feat()
            def val2(self):
                return self._val2

            @val2.setter
            def val2(self, value):
                self._val2 = value

            @Action()
            def action2(self):
                return 'action2'

        class Z(X):

            @Feat()
            def feat1(self):
                return super().feat1 + ' in Z'

            @Feat()
            def val1(self):
                return super().val1

            @val1.setter
            def val1(self, value):
                self._val1 = 2 * value

            @Action()
            def action1(self):
                return super().action1() + ' in Z'

        class N(X):
            pass

        x = X()
        y = Y()
        z = Z()
        n = N()
        self.assertEqual(set(x._lantz_features.keys()), {'feat1', 'val1'})
        self.assertEqual(set(y._lantz_features.keys()), {'feat1', 'feat2', 'val1', 'val2'})
        self.assertEqual(set(z._lantz_features.keys()), {'feat1', 'val1'})
        self.assertEqual(set(n._lantz_features.keys()), {'feat1', 'val1'})

        self.assertEqual(set(x._lantz_actions.keys()), {'action1', })
        self.assertEqual(set(y._lantz_actions.keys()), {'action1', 'action2'})
        self.assertEqual(set(z._lantz_actions.keys()), {'action1', })
        self.assertEqual(set(n._lantz_actions.keys()), {'action1', })

        self.assertEqual(x.refresh(), {'feat1': 'feat1', 'val1': 1})
        x.val1 = 2
        self.assertEqual(x.refresh(), {'feat1': 'feat1', 'val1': 2})

        self.assertEqual(y.refresh(), {'feat1': 'feat1', 'feat2': 'feat2', 'val1': 1, 'val2': 1})
        y.val2 = 2
        self.assertEqual(y.refresh(), {'feat1': 'feat1', 'feat2': 'feat2', 'val1': 1, 'val2': 2})

        self.assertEqual(z.refresh(), {'feat1': 'feat1 in Z', 'val1': 1})
        z.val1 = 2
        self.assertEqual(z.refresh(), {'feat1': 'feat1 in Z', 'val1': 4})

        self.assertEqual(n.refresh(), {'feat1': 'feat1', 'val1': 1})

        self.assertEqual(x.action1(), 'action1')
        self.assertEqual(y.action1(), 'action1')
        self.assertEqual(y.action2(), 'action2')
        self.assertEqual(z.action1(), 'action1 in Z')
        self.assertEqual(n.action1(), 'action1')

    def test_derived_class_post(self):

        class X(object):

            @Feat()
            def feat1(self):
                return 'feat1'

            @Action()
            def action1(self):
                return 'action1'

        class Y(X, Driver):

            @Feat()
            def feat2(self):
                return 'feat2'

            @Action()
            def action2(self):
                return 'action2'

        class Z(X, Driver):

            @Feat()
            def feat1(self):
                return super().feat1 + ' in Z'

            @Action()
            def action1(self):
                return super().action1() + ' in Z'

        class N(X, Driver):
            pass

        y = Y()
        z = Z()
        n = N()
        self.assertEqual(set(y._lantz_features.keys()), {'feat1', 'feat2'})
        self.assertEqual(set(z._lantz_features.keys()), {'feat1', })
        self.assertEqual(set(n._lantz_features.keys()), {'feat1', })

        self.assertEqual(set(y._lantz_actions.keys()), {'action1', 'action2'})
        self.assertEqual(set(z._lantz_actions.keys()), {'action1', })
        self.assertEqual(set(n._lantz_actions.keys()), {'action1', })

        self.assertEqual(y.refresh(), {'feat1': 'feat1', 'feat2': 'feat2'})
        self.assertEqual(z.refresh(), {'feat1': 'feat1 in Z'})
        self.assertEqual(n.refresh(), {'feat1': 'feat1'})

        self.assertEqual(y.action1(), 'action1')
        self.assertEqual(y.action2(), 'action2')
        self.assertEqual(z.action1(), 'action1 in Z')
        self.assertEqual(n.action1(), 'action1')

    def test_Self_exceptions(self):

        class X(Driver):

            @Feat(units=Self.units)
            def value(self):
                return 1

            @value.setter
            def value(self, value):
                pass

            @Feat()
            def units(self):
                return self._units

            @units.setter
            def units(self, value):
                self._units = value

        x = X()
        self.assertRaises(Exception, getattr, x, 'value')
        self.assertRaises(Exception, setattr, x, 'value', 1)
        x.units = 'ms'
        self.assertEqual(x.feats.value.units, 'ms')
        self.assertEqual(x.value, Q_(1, 'ms'))


    def test_Self(self):

        class X(Driver):

            @Feat(units=Self.a_value_units('s'))
            def a_value(self):
                return 1

            @Feat()
            def a_value_units(self):
                return self._units

            @a_value_units.setter
            def a_value_units(self, new_units):
                self._units = new_units

        x = X()
        self.assertEqual(x.feats.a_value.units, 's')
        self.assertEqual(x.a_value, Q_(1, 's'))
        x.a_value_units = 'ms'
        self.assertEqual(x.feats.a_value.units, 'ms')
        self.assertEqual(x.a_value, Q_(1, 'ms'))


if __name__ == '__main__':
    unittest.main()
