#!/usr/bin/env python

import sys
from setuptools import setup

requires = ['six']

if sys.version_info[0] == 2:
    requires += ['python-dateutil>=1.0, != 2.0']
else:
    # Py3k
    requires += ['python-dateutil>=2.0']

with open('README.rst') as f:
    readme = f.read()

setup(
    name='freezegun',
    version='0.3.10',
    description='Let your Python tests travel through time',
    long_desciption=readme,
    author='Steve Pulec',
    author_email='spulec@gmail.com',
    url='https://github.com/spulec/freezegun',
    packages=['freezegun'],
    install_requires=requires,
    include_package_data=True,
    license='Apache 2.0',
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.6',
    ],
)
