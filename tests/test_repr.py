#!/usr/bin/env python3
"""
High-level tests for the all __repr__ functions
"""
import os
import sys
import unittest
import tempfile
import shutil
import stat
import machinestate
from locale import getpreferredencoding

ENCODING = getpreferredencoding()

def test_repr_sub(cls, level):
    for inst in cls._instances:
        print("{}{}".format(level*'\t',inst))
        if len(inst._instances) > 0:
            test_repr_sub(inst, level+1)

class TestRepr(unittest.TestCase):
    def test_repr(self):
        ms = machinestate.MachineState(extended=True)
        ms.generate()
        print("")
        print(ms)
        test_repr_sub(ms, 1)

