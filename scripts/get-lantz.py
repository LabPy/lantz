#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys

if not sys.version_info >= (3, 2, 1):
    print('Lantz requires Python >= 3.2.1')
    sys.exit(1)

import os
import time
import platform
import argparse
import subprocess
import urllib.request
import concurrent.futures

if platform.architecture()[0] != '32bit' or not sys.platform.startswith('win'):
    print('Only 32bit Python running on Windows is currently supported by get-lantz.py')
    sys.exit(2)

parser = argparse.ArgumentParser('Get Lantz!')
parser.add_argument('-e', '--editable', action='store_true',
                    help='Install Lantz as an editable package')
args = parser.parse_args()



URLS = {'setuptools': ('distribute_setup.py', 'http://python-distribute.org/{}'),
        'pip': ('get-pip.py', 'https://raw.github.com/pypa/pip/master/contrib/{}'),
        'PyQt4': ('PyQt-Py3.2-x86-gpl-4.9.4-1.exe', 'http://www.riverbankcomputing.co.uk/static/Downloads/PyQt4/{}'),
        'numpy': ('numpy-1.6.2-win32-superpack-python3.2.exe', 'http://sourceforge.net/projects/numpy/files/NumPy/1.6.2/{}/download'),
        'scipy': ('scipy-0.10.1-win32-superpack-python3.2.exe', 'http://sourceforge.net/projects/scipy/files/scipy/0.10.1/{}/download'),
        'git': ('Git-1.7.11-preview20120710.exe', 'http://msysgit.googlecode.com/files/{}'),
        'matplotlib': ('', ''),
        'visa': ('visa520full.exe', 'http://ftp.ni.com/support/softlib/visa/NI-VISA/5.2/win/{}')}

if not args.editable:
    del URLS['git']

def download(filename, url):

    if os.path.exists(filename):
        print('File found {}'.format(filename))
        return

    if '{}' in url:
        url = url.format(filename)

    start = time.time()
    print('Downloading {}'.format(filename))
    urllib.request.urlretrieve(url, filename)
    print('Downloaded {} in {:.2f} secs'.format(filename, time.time() - start))


print(' Checking '.center(20, '-'))
INSTALL = []
for check in ('setuptools', 'pip', 'PyQt4', 'numpy', 'scipy'):
    try:
        __import__(check)
        print('No need to install {}'.format(check))
    except ImportError:
        INSTALL.append(check)
        print('Adding {} to install list'.format(check))

if args.editable:
    try:
        subprocess.call(['git', '--version'])
        print('No need to install git')
    except Exception as e:
        print('Adding git to install list')
        INSTALL.append('git')


INSTALL.append('visa')

os.chdir(os.path.dirname(os.path.abspath(__file__)))
print('Working directory: {}'.format(os.getcwd()))


print(' Downloading '.center(20, '-'))
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    futs = [executor.submit(download, *filename_url)
            for filename, filename_url in URLS.items()
            if filename in INSTALL]
    concurrent.futures.wait(futs)


print(' Installing '.center(20, '-'))
for key in ('setuptools', 'pip', ):
    if key in INSTALL:
        subprocess.call([sys.executable, URLS[key][0]])

for key in ('PyQt4', 'numpy', 'scipy', 'git', 'visa'):
    if key in INSTALL:
        subprocess.call([URLS[key][0], ])

PIP = os.path.join(os.path.dirname(sys.executable), 'Scripts', 'pip')

REQS = ['colorama', 'pyserial', 'sphinx', 'pyyaml']

if args.editable:
    subprocess.call([PIP, 'install', ] + REQS)
    subprocess.call([PIP, 'install', '-e', 'lantz'])
else:
    subprocess.call([PIP, 'install', ] + REQS + ['lantz'])
