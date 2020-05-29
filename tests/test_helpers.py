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
        self.temp_dir = tempfile.mkdtemp()
        self.temp_files = {"File{}".format(x) : tempfile.mkstemp(prefix=str(x), dir=self.temp_dir) for x in range(4)}

        for tkey in self.temp_files:
            tfp, tfname = self.temp_files[tkey]
            os.pwrite(tfp, bytes("{}\n".format(tkey), ENCODING), 0)
            os.close(tfp)

    def tearDown(self):
        # Remove the directory after the test
        shutil.rmtree(self.temp_dir)

    def test_fopen(self):
        fp = machinestate.fopen(self.temp_files["File0"][1])
        self.assertNotEqual(fp, None)
        if fp: fp.close()
    def test_fopenNone(self):
        fp = machinestate.fopen(None)
        self.assertEqual(fp, None)
        if fp: fp.close()
    def test_fopenDir(self):
        fp = machinestate.fopen(self.temp_dir)
        self.assertEqual(fp, None)
        if fp: fp.close()
    def test_fopenNotExist(self):
        fp = machinestate.fopen(self.temp_files["File0"][1]+"1234")
        self.assertEqual(fp, None)
        if fp: fp.close()
    def test_fopenNoPerm(self):
        os.chmod(self.temp_files["File0"][1], 0o0200)
        fp = machinestate.fopen(self.temp_files["File0"][1])
        self.assertEqual(fp, None)
        if fp: fp.close()
        os.chmod(self.temp_files["File0"][1], 0o0644)
