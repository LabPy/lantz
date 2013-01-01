#!/usr/bin/env python
# -*- coding: utf-8 -*-

from distutils.core import setup

import os

folder = os.path.dirname(os.path.abspath(__file__))
folder = os.path.join(folder, 'lantz', 'drivers')
paths = os.listdir(folder)

companies = [path for path in paths
             if os.path.isdir(os.path.join(folder, path))
             and os.path.exists(os.path.join(folder, path, '__init__.py'))]

setup(name='Lantz',
      version='0.2',
      description='Instrumentation framework',
      long_description=('Lantz is an automation and instrumentation toolkit '
                        'with a clean, well-designed and consistent interface. '
                        'It provides a core of commonly used functionalities for '
                        'building applications that communicate with scientific '
                        'instruments allowing rapid application prototyping, '
                        'development and testing. Lantz benefits from Python’s '
                        'extensive library flexibility as a glue language to wrap '
                        'existing drivers and DLLs.'),
      author='Hernan E. Grecco',
      author_email='hernan.grecco@gmail.com',
      url='http://lantz.glugcen.dc.uba.ar/',
      packages=['lantz',
                'lantz.ui',
                'lantz.simulators',
                'lantz.drivers'] +
               ['lantz.drivers.' + company for company in companies],
      install_requires = [
        'pint',
        'stringparser',
      ],
      zip_safe=False,
      platforms='any',
      extra_require = {
                        'colorama':  ['colorama'],
                        'numpy': ['numpy'],
                        'ui': ['sip', 'pyqt4']
                        },
      classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering',
        'Topic :: Software Development :: Libraries'
      ],
      scripts=['scripts/lantz-monitor',
               'scripts/lantz-scan',
               'scripts/lantz-visa-shell',
               'scripts/lantz-sim']
)
