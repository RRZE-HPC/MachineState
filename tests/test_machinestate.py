#!/usr/bin/env python3
"""
High-level tests for the class PathMatchInfoGroup
"""
import os, os.path
import sys, glob
import unittest
import tempfile
import shutil
import stat
from machinestate import MachineState
from locale import getpreferredencoding

ENCODING = getpreferredencoding()


class TestMachineState(unittest.TestCase):
    def test_getJson(self):
        cls = MachineState()
        outstr = cls.get_json()
        self.assertEqual(outstr, "{}")
    def test_CompareJson(self):
        cls = MachineState()
        cls.generate()
        cls.update()
        outstr = cls.get_json()
        self.assertNotEqual(outstr, "{}")
        self.assertTrue(cls == outstr)