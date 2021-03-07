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
        outstr = cls.get_json(meta=False)
        self.assertEqual(outstr, "{}")
    def test_getJsonMeta(self):
        cls = MachineState()
        outstr = cls.get_json(meta=True)
        self.assertEqual(outstr, "{\n    \"_meta\": \"MachineState()\"\n}")
    def test_CompareJson(self):
        cls = MachineState()
        cls.generate()
        cls.update()
        outstr = cls.get_json()
        self.assertNotEqual(outstr, "{}")
        self.assertTrue(cls.get_json() == outstr)
    def test_fromDictCompare(self):
        ms = MachineState();
        ms.generate();
        ms.update()
        msdict = ms.get(meta=True)
        mscopy = MachineState.from_dict(msdict)
        self.assertEqual(ms, mscopy)
        self.assertEqual(ms.get(meta=False), mscopy.get(meta=False))
        self.assertEqual(ms.get(meta=True), mscopy.get(meta=True))
