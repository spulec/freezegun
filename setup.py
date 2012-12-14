#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='freezegun',
    version='0.0.8',
    description='Let your Python tests travel through time',
    author='Steve Pulec',
    author_email='spulec@gmail',
    url='https://github.com/spulec/freezegun',
    packages=find_packages(),
    install_requires=['python-dateutil>=1.0, <2.0'],
    include_package_data=True,
)
