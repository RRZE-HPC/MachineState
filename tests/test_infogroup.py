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
from machinestate import InfoGroup
from locale import getpreferredencoding

ENCODING = getpreferredencoding()

class TestInfoGroupBase(unittest.TestCase):
    def test_empty(self):
        cls = InfoGroup()
        self.assertEqual(cls.name, None)
        self.assertEqual(cls.extended, False)
        self.assertEqual(cls.anonymous, False)
        self.assertEqual(cls.files, {})
        self.assertEqual(cls.commands, {})
        self.assertEqual(cls.constants, {})
        self.assertEqual(cls._instances, [])

    def test_named(self):
        cls = InfoGroup(name="Testname")
        self.assertEqual(cls.name, "Testname")
    def test_extended(self):
        cls = InfoGroup(extended=True)
        self.assertEqual(cls.extended, True)
    def test_anonymous(self):
        cls = InfoGroup(anonymous=True)
        self.assertEqual(cls.anonymous, True)
    def test_constant(self):
        testdict = {"Test1" : "Test", "Test2" : "Test", "Test3" : 3}
        cls = InfoGroup()
        for key, value in testdict.items():
            cls.const(key, value)
        cls.generate()
        cls.update()
        outdict = cls.get()
        for key in testdict:
            self.assertEqual(testdict[key], outdict[key])

class TestInfoGroupFiles(unittest.TestCase):
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

    def test_files(self):
        resdict = {"File{}".format(x) : "File{}".format(x) for x in range(4)}
        cls = InfoGroup()
        for tkey in self.temp_files:
            _, tfname = self.temp_files[tkey]
            cls.addf(tkey, tfname)
        cls.generate()
        cls.update()
        outdict = cls.get()
        for i,tkey in enumerate(resdict):
            self.assertEqual(resdict[tkey], outdict[tkey])
    def test_filesMatch(self):
        resdict = {"File{}".format(x) : "{}".format(x) for x in range(4)}
        match = r"File(\d+)"
        cls = InfoGroup()
        for tkey in self.temp_files:
            _, tfname = self.temp_files[tkey]
            cls.addf(tkey, tfname, match)
        cls.generate()
        cls.update()
        outdict = cls.get()
        for i,tkey in enumerate(resdict):
            self.assertEqual(resdict[tkey], outdict[tkey])
    def test_filesMatchConvert(self):
        resdict = {"File{}".format(x) : x for x in range(4)}
        match = r"File(\d+)"
        cls = InfoGroup()
        for tkey in self.temp_files:
            _, tfname = self.temp_files[tkey]
            cls.addf(tkey, tfname, match, int)
        cls.generate()
        cls.update()
        outdict = cls.get()
        for i,tkey in enumerate(resdict):
            self.assertEqual(resdict[tkey], outdict[tkey])
    def test_filesNotExist(self):
        resdict = {"File{}".format(x) : x for x in range(4)}
        match = r"File(\d+)"
        cls = InfoGroup()
        for tkey in self.temp_files:
            _, tfname = self.temp_files[tkey]
            cls.addf(tkey, "{}1234".format(tfname), match, int)
        cls.generate()
        cls.update()
        outdict = cls.get()
        for i,tkey in enumerate(resdict):
            self.assertNotEqual(resdict[tkey], outdict[tkey])
            self.assertEqual(outdict[tkey], None)

class TestInfoGroupCommands(unittest.TestCase):
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
    def test_commands(self):
        resdict = {"File{}".format(x) : "File{}".format(x) for x in range(4)}
        cls = InfoGroup()
        for tkey in self.temp_files:
            _, tfname = self.temp_files[tkey]
            cls.addc(tkey, "echo", "{}".format(tkey))
        cls.generate()
        cls.update()
        outdict = cls.get()
        for i,tkey in enumerate(resdict):
            self.assertEqual(resdict[tkey], outdict[tkey])
    def test_commandsMatch(self):
        resdict = {"File{}".format(x) : "{}".format(x) for x in range(4)}
        match = r"File(\d+)"
        cls = InfoGroup()
        for tkey in self.temp_files:
            _, tfname = self.temp_files[tkey]
            cls.addc(tkey, "echo", "{}".format(tkey), match)
        cls.generate()
        cls.update()
        outdict = cls.get()
        for i,tkey in enumerate(resdict):
            self.assertEqual(resdict[tkey], outdict[tkey])
    def test_commandsMatchConvert(self):
        resdict = {"File{}".format(x) : x for x in range(4)}
        match = r"File(\d+)"
        cls = InfoGroup()
        for tkey in self.temp_files:
            _, tfname = self.temp_files[tkey]
            cls.addc(tkey, "echo", "{}".format(tkey), match, int)
        cls.generate()
        cls.update()
        outdict = cls.get()
        for i,tkey in enumerate(resdict):
            self.assertEqual(resdict[tkey], outdict[tkey])
    def test_commandsNotExist(self):
        resdict = {"File{}".format(x) : x for x in range(4)}
        match = r"File(\d+)"
        cls = InfoGroup()
        for tkey in self.temp_files:
            _, tfname = self.temp_files[tkey]
            cls.addc(tkey, "echo{}".format(tfname), "{}".format(tkey), match, int)
        cls.generate()
        cls.update()
        outdict = cls.get()
        for i,tkey in enumerate(resdict):
            self.assertNotEqual(resdict[tkey], outdict[tkey])
            self.assertEqual(outdict[tkey], None)
