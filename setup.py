#!/usr/bin/env python3

from setuptools import setup
import re

long_description='''Gathering the system state before benchmarking and other tests on compute
systems. MachineState reads common sysfs and procfs files as well as executes commands to get all
required data. For reproducibility, the once saved system state can be compared to the current state
before re-running a test.
'''

def find_version():
    with open("machinestate.py") as msfp:
        lines = msfp.read().split("\n")
        for line in lines:
            mat = re.search(r"^MACHINESTATE_VERSION = ['\"]([^'\"]*)['\"]", line)
            if mat:
                return mat.group(1)

setup(name='MachineState',
    version=find_version(),

    description='Gather machine state and dump it as JSON document',
    long_description=long_description,

    # Author details
    author='Thomas Gruber',
    author_email='thomas.gruber@fau.de',

    # The project's main homepage.
    url='https://github.com/RRZE-HPC/MachineState',

    # License
    license='GPLv3',
    py_modules=['machinestate'],
    entry_points = {
        'console_scripts': ['machinestate=machinestate:main'],
    },

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 3 - Alpha',

        'Intended Audience :: Science/Research',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',

        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',

        'Topic :: System :: Benchmark',
        'Topic :: System :: Hardware',
        'Topic :: System :: Operating System',
        'Topic :: System :: Systems Administration',
        'Topic :: Education :: Testing',

        'Operating System :: POSIX :: Linux',
        'Environment :: Console',

        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],

    keywords='benchmarking, linux, system state, topology'
)
