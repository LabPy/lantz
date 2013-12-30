# -*- coding: utf-8 -*-

import os
import sys
import logging
import unittest


def testsuite():
    """A testsuite that has all the lantz tests.
    """
    return unittest.TestLoader().discover(os.path.dirname(__file__))


def main():
    """Runs the testsuite as command line application."""
    try:
        unittest.main()
    except Exception as e:
        print('Error: %s' % e)
