#!/usr/bin/env python

import sys
from setuptools import setup

requires = ['six']
tests_require = ['mock', 'nose']

if sys.version_info.major == 2:
    requires += ['python-dateutil>=1.0, != 2.0']
else:
    # Py3k
    requires += ['python-dateutil>=2.0']


with open('README.rst') as f:
    readme = f.read()

setup(
    name='freezegun',
    version='0.3.12',
    description='Let your Python tests travel through time',
    long_description=readme,
    author='Steve Pulec',
    author_email='spulec@gmail.com',
    url='https://github.com/spulec/freezegun',
    packages=['freezegun'],
    install_requires=requires,
    tests_require=tests_require,
    include_package_data=True,
    license='Apache 2.0',
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*',
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
)
