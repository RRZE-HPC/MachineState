#!/usr/bin/env python3
"""
High-level tests for the class InfoGroup
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


class TestHelpers(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory
        self.test_input = "DMIDECODEFILECONTENT"
        tfp, self.temp_file = tempfile.mkstemp()
        if tfp > 0:
            os.pwrite(tfp, bytes("{}\n".format(self.test_input), ENCODING), 0)
            os.close(tfp)

    def tearDown(self):
        os.remove(self.temp_file)

    def testDmiDecodeFile(self):
        cls = machinestate.DmiDecodeFile(dmifile=self.temp_file)
        cls.generate()
        cls.update()
        outdict = cls.get()
        self.assertEqual(list(outdict.keys()), ["DmiDecode"])
        self.assertEqual(outdict["DmiDecode"], self.test_input)
    def testDmiDecodeFileNoExist(self):
        cls = machinestate.DmiDecodeFile(dmifile=self.temp_file+"1234")
        cls.generate()
        cls.update()
        outdict = cls.get()
        self.assertEqual(outdict, {})
    def testDmiDecodeFileNone(self):
        self.assertRaises(TypeError, machinestate.DmiDecodeFile, None, {"dmifile" : None})
    def testDmiDecodeFileNoArgs(self):
        self.assertRaises(TypeError, machinestate.DmiDecodeFile, None, {})