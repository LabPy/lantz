#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import os
import codecs


def read(filename):
    return codecs.open(filename, encoding='utf-8').read()


long_description = '\n\n'.join([read('README'),
                                read('AUTHORS'),
                                read('CHANGES')])

__doc__ = long_description
folder = os.path.dirname(os.path.abspath(__file__))
folder = os.path.join(folder, 'lantz', 'drivers')
paths = os.listdir(folder)

companies = [path for path in paths
             if os.path.isdir(os.path.join(folder, path))
             and os.path.exists(os.path.join(folder, path, '__init__.py'))]

setup(name='Lantz',
      version='0.3.dev0',
      license='BSD',
      description='Instrumentation framework',
      long_description=long_description,
      author='Hernan E. Grecco',
      author_email='hernan.grecco@gmail.com',
      url='http://lantz.glugcen.dc.uba.ar/',
      packages=['lantz',
                'lantz.ui',
                'lantz.simulators',
                'lantz.drivers'] +
               ['lantz.drivers.' + company for company in companies],
      test_suite='pint.testsuite.testsuite',
      install_requires=[
        'pint',
        'stringparser',
      ],
      zip_safe=False,
      platforms='any',
      extra_require={
                     'colorama':  ['colorama'],
                     'numpy': ['numpy'],
                     'ui': ['sip', 'pyqt4']
                    },
      entry_points={
           'zest.releaser.releaser.after_checkout': [
              'pyroma = lantz:run_pyroma',
           ],
           'console_scripts': [
              'lantz-shell = lantz.ui.shell:main',
           ]
        },
      classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Topic :: Scientific/Engineering',
        'Topic :: Software Development :: Libraries'
      ],
      scripts=['scripts/lantz-monitor',
               'scripts/lantz-scan',
               'scripts/lantz-visa-shell',
               'scripts/lantz-sim'],
)
