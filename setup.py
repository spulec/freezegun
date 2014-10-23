#!/usr/bin/env python

import sys
import freezegun
from setuptools import setup, find_packages

requires = ['six']

if sys.version_info[0] == 2:
    requires += ['python-dateutil>=1.0, <2.0, >=2.1']
else:
    # Py3k
    requires += ['python-dateutil>=2.0']

setup(
    name=freezegun.__title__,
    version=freezegun.__version__,
    description='Let your Python tests travel through time',
    author=freezegun.__author__,
    author_email='spulec@gmail',
    url='https://github.com/spulec/freezegun',
    packages=find_packages(exclude=("tests", "tests.*",)),
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
