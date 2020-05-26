#!/usr/bin/env python3

from setuptools import setup

setup(name='MachineState',
    version='0.1',
    description='Gather machine state and dump it as JSON document',
    long_description='',
    author='Thomas Gruber',
    author_email='thomas.gruber@fau.de',
    url='https://github.com/RRZE-HPC/Artifact-description',
    license='GPLv3',
    py_modules=['machinestate'],
    entry_points = {
        'console_scripts': ['machinestate=machinestate:main'],
    },
    classifiers=[
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Environment :: Console',
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Topic :: Education :: Testing',
        'Topic :: System',
        'Topic :: System :: Benchmark',
        'Topic :: System :: Hardware',
        'Topic :: System :: Hardware :: Symmetric Multi-processing',
        'Topic :: System :: Operating System',
        'Topic :: System :: Systems Administration',
        ],
    keywords='benchmarking, linux, system state'
)
