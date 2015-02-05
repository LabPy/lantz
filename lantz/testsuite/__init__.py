# -*- coding: utf-8 -*-

import os
import unittest


def testsuite():
    """A testsuite that has all the lantz tests.
    """
    return unittest.TestLoader().discover(os.path.dirname(__file__))


def main():
    """Runs the testsuite as command line application.
    """
    try:
        unittest.main()
    except Exception as e:
        print('Error: %s' % e)


def run():
    """Run all tests.

    :return: a :class:`unittest.TestResult` object
    """
    test_runner = unittest.TextTestRunner()
    return test_runner.run(testsuite())
