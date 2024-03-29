# !/usr/bin/env python
# encoding: utf-8

from setuptools import find_packages, setup

NAME = 'ginji'
DESCRIPTION = 'Raspberry Pi inputs and outputs. Mostly centred around motion detection and video capture.'
URL = 'https://github.com/alycejenni/catflap'
REQUIRES_PYTHON = '>=3.6.0'
VERSION = '0.1.1'

with open('requirements.txt', 'r') as req_file:
    REQUIRED = [r.strip() for r in req_file.readlines()]

setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=DESCRIPTION,
    python_requires=REQUIRES_PYTHON,
    url=URL,
    packages=find_packages(exclude=('tests',)),
    install_requires=REQUIRED,
    include_package_data=True,
    package_data={
        'ginji': []
        },
    entry_points='''
        [console_scripts]
        ginji=ginji.cli:cli
    ''',
    license='MIT',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython'
        ]
    )
