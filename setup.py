#!/usr/bin/env python

import sys
from setuptools import setup, find_packages

requires = ['six']

if sys.version_info[0] == 2:
    requires += ['python-dateutil>=1.0, <2.0, >=2.1']
else:
    # Py3k
    requires += ['python-dateutil>=2.0']

setup(
    name='freezegun',
    version='0.1.18',
    description='Let your Python tests travel through time',
    author='Steve Pulec',
    author_email='spulec@gmail',
    url='https://github.com/spulec/freezegun',
    packages=find_packages(exclude=("tests", "tests.*",)),
    install_requires=requires,
    include_package_data=True,
)
