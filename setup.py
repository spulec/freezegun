#!/usr/bin/env python

from setuptools import setup, find_packages

import freezegun

setup(
    name='freezegun',
    version=freezegun.__version__,
    description='Let your Python tests travel through time',
    author='Steve Pulec',
    author_email='spulec@gmail',
    url='https://github.com/spulec/freezegun',
    packages=find_packages(),
    include_package_data=True,
)