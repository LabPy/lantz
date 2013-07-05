
import unittest
import doctest

from lantz import Q_

import lantz.processors as processors

mv = Q_(1, 'mV')
Hz = Q_(1, 'Hz')
V = Q_(1, 'V')

class TestProcessors(unittest.TestCase):

    def test_docs(self):
        doctest.testmod(processors)

    def test_invalid_arguments(self):
        self.assertRaises(ValueError, processors.convert_to, V, on_incompatible='na')
        self.assertRaises(ValueError, processors.convert_to, V, on_dimensionless='na')
        self.assertRaises(ValueError, processors.convert_to, list())

    def test_return_float(self):
        self.assertEqual(processors.convert_to(V, return_float=True)(1*mv), 0.001)

        self.assertRaises(ValueError, processors.convert_to(V, return_float=True, on_incompatible='raise'), Hz)
        self.assertWarns(processors.DimensionalityWarning, processors.convert_to(V, return_float=True, on_incompatible='warn'), Hz)
        self.assertEqual(processors.convert_to(V, return_float=True, on_incompatible='ignore')(Hz), 1)

        self.assertRaises(ValueError, processors.convert_to(V, return_float=True, on_dimensionless='raise'), 1000)
        self.assertWarns(processors.DimensionalityWarning, processors.convert_to(V, return_float=True, on_dimensionless='warn'), 1000)
        self.assertEqual(processors.convert_to(V, return_float=True, on_dimensionless='ignore')(1000), 1000)

    def test_return_quantity(self):
        self.assertEqual(processors.convert_to(V)(1*mv), 0.001 * V)

        self.assertRaises(ValueError, processors.convert_to(V, on_incompatible='raise'), Hz)
        self.assertWarns(processors.DimensionalityWarning, processors.convert_to(V, on_incompatible='warn'), Hz)
        self.assertEqual(processors.convert_to(V, on_incompatible='ignore')(Hz), 1 * V)

        self.assertRaises(ValueError, processors.convert_to(V, on_dimensionless='raise'), 1000)
        self.assertWarns(processors.DimensionalityWarning, processors.convert_to(V, on_dimensionless='warn'), 1000)
        self.assertEqual(processors.convert_to(V, on_dimensionless='ignore')(1000), 1000 * V)

        self.assertRaises(ValueError, processors.convert_to(V, on_dimensionless='raise'), 1000)

if __name__ == '__main__':
    unittest.main()
