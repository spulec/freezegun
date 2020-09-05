#!/usr/bin/env python

from setuptools import setup

with open('README.rst') as f:
    readme = f.read()

setup(
    name='freezegun',
    version='1.0.0',
    description='Let your Python tests travel through time',
    long_description=readme,
    author='Steve Pulec',
    author_email='spulec@gmail.com',
    url='https://github.com/spulec/freezegun',
    packages=['freezegun'],
    install_requires=['python-dateutil>=2.7'],
    include_package_data=True,
    license='Apache 2.0',
    python_requires='>=3.5',
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
)
