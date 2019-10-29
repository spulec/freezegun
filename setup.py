#!/usr/bin/env python

import sys
from setuptools import setup

requires = ['six', 'python-dateutil>=2.0']
tests_require = ['nose']

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
    package_data={'freezegun':['py.typed']},
    zip_safe=False,
    install_requires=requires,
    tests_require=tests_require,
    include_package_data=True,
    license='Apache 2.0',
    python_requires='>=3.5',
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
)
