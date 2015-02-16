#!/usr/bin/env python

import sys
from setuptools import setup, find_packages

requires = ['six']

if sys.version_info[0] == 2:
    requires += ['python-dateutil>=1.0, != 2.0']
else:
    # Py3k
    requires += ['python-dateutil>=2.0']

setup(
    name='freezegun',
    version='0.3.0',
    description='Let your Python tests travel through time',
    author='Steve Pulec',
    author_email='spulec@gmail',
    url='https://github.com/spulec/freezegun',
    packages=['freezegun'],
    install_requires=requires,
    include_package_data=True,
    classifiers=[
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
    ],
)
