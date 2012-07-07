#!/usr/bin/env python

from distutils.core import setup

setup(name='Lantz',
      version='0.0',
      description='Instrumentation framework',
      author='Hernan E. Grecco',
      author_email='hernan.grecco@gmail.com',
      url='',
      packages=['lantz'],
      extras_require = {
                        'colorama':  ['colorama'],
                        'numpy': ['numpy'],
                        'ui': ['sip', 'pyqt4']
                        }
)
