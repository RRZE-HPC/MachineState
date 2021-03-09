#!/usr/bin/env python3
"""
High-level tests for the class ListInfoGroup
"""
import os
import sys
import unittest
import tempfile
import shutil
import stat
import glob
from machinestate import ListInfoGroup, InfoGroup
from locale import getpreferredencoding

ENCODING = getpreferredencoding()

class TestClass:
    pass

class TestInfoGroup(InfoGroup):
    def __init__(self, ident, name=None, extended=False, anonymous=False, basepath=""):
        super(TestInfoGroup, self).__init__(extended=extended, name=name, anonymous=anonymous)
        self.name = "File{}".format(ident)
        self.ident = ident
        self.basepath = basepath
        path = os.path.join(basepath, "{}*".format(ident))
        files = glob.glob(path)
        self.addf("File{}".format(ident), files[0], r"(.+)")

class TestListInfoGroupBase(unittest.TestCase):
    def test_empty(self):
        cls = ListInfoGroup()
        self.assertEqual(cls.name, None)
        self.assertEqual(cls.extended, False)
        self.assertEqual(cls.anonymous, False)
        self.assertEqual(cls.files, {})
        self.assertEqual(cls.commands, {})
        self.assertEqual(cls.constants, {})
        self.assertEqual(cls._instances, [])
        self.assertEqual(cls.userlist, [])
        self.assertEqual(cls.subclass, None)
        self.assertEqual(cls.subargs, {})

    def test_named(self):
        cls = ListInfoGroup(name="Testname")
        self.assertEqual(cls.name, "Testname")
    def test_extended(self):
        cls = ListInfoGroup(extended=True)
        self.assertEqual(cls.extended, True)
    def test_anonymous(self):
        cls = ListInfoGroup(anonymous=True)
        self.assertEqual(cls.anonymous, True)
    def test_userlistNone(self):
        cls = ListInfoGroup(userlist=None)
        self.assertEqual(cls.userlist, [])
    def test_userlistEmpty(self):
        cls = ListInfoGroup(userlist=[])
        self.assertEqual(cls.userlist, [])
    def test_userlistFilled(self):
        testl = ["a", "b", "c"]
        cls = ListInfoGroup(userlist=testl)
        self.assertEqual(cls.userlist, testl)
    def test_subclassString(self):
        cls = ListInfoGroup(subclass="abc")
        self.assertEqual(cls.subclass, None)
    def test_subclassNone(self):
        cls = ListInfoGroup(subclass=None)
        self.assertEqual(cls.subclass, None)
    def test_subclassClass(self):
        cls = ListInfoGroup(subclass=TestClass)
        self.assertEqual(cls.subclass, TestClass)
    def test_subargsNone(self):
        cls = ListInfoGroup(subargs=None)
        self.assertEqual(cls.subargs, {})
    def test_subargsDict(self):
        cls = ListInfoGroup(subargs={})
        self.assertEqual(cls.subargs, {})
    def test_subargsBool(self):
        cls = ListInfoGroup(subargs=True)
        self.assertEqual(cls.subargs, {})
    def test_subargsList(self):
        cls = ListInfoGroup(subargs=[])
        self.assertEqual(cls.subargs, {})

class TestListInfoGroupFunction(unittest.TestCase):
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
    def test_validCreate(self):
        userlist = [x for x in range(len(self.temp_files))]
        cls = ListInfoGroup(userlist=userlist, subclass=TestInfoGroup, subargs={"basepath": self.temp_dir})
        self.assertEqual(cls._instances, [])
        self.assertEqual(cls.userlist, userlist)
        self.assertEqual(cls.subclass, TestInfoGroup)
        self.assertEqual(cls.subargs, {"basepath": self.temp_dir})
    def test_validGenerate(self):
        userlist = [x for x in range(len(self.temp_files))]
        cls = ListInfoGroup(userlist=userlist, subclass=TestInfoGroup, subargs={"basepath": self.temp_dir})
        cls.generate()
        self.assertEqual(len(cls._instances), 4)
        self.assertEqual(cls._data, {})
        for inst in cls._instances:
            self.assertEqual(inst._instances, [])
            self.assertEqual(inst._data, {})
    def test_validUpdate(self):
        userlist = [x for x in range(len(self.temp_files))]
        cls = ListInfoGroup(userlist=userlist, subclass=TestInfoGroup, subargs={"basepath": self.temp_dir})
        cls.generate()
        cls.update()
        self.assertEqual(len(cls._instances), 4)
        self.assertEqual(cls._data, {})
        for inst in cls._instances:
            self.assertEqual(inst._instances, [])
            self.assertNotEqual(inst._data, {})
    def test_validGet(self):
        userlist = [x for x in range(len(self.temp_files))]
        cls = ListInfoGroup(userlist=userlist, subclass=TestInfoGroup, subargs={"basepath": self.temp_dir})
        cls.generate()
        cls.update()
        outdict = cls.get()
        self.assertEqual(cls._data, {})
        for inst in cls._instances:
            self.assertEqual(inst._instances, [])
            self.assertNotEqual(inst._data, {})
        for i, key in enumerate(self.temp_files.keys()):
            for subkey in outdict[key]:
                self.assertEqual(key, subkey)
                self.assertEqual(key, outdict[key][subkey])
    def test_invalidCreate(self):
        userlist = [x+100 for x in range(len(self.temp_files))]
        cls = ListInfoGroup(userlist=userlist, subclass=TestInfoGroup, subargs={"basepath": self.temp_dir})
        self.assertEqual(cls._instances, [])
        self.assertEqual(cls._data, {})
        self.assertEqual(cls.userlist, userlist)
    def test_invalidGenerate(self):
        userlist = [x+100 for x in range(len(self.temp_files))]
        cls = ListInfoGroup(userlist=userlist, subclass=TestInfoGroup, subargs={"basepath": self.temp_dir})
        #cls.generate()
        self.assertRaises(IndexError, cls.generate)
        self.assertEqual(cls._instances, [])
        self.assertEqual(cls._data, {})
        self.assertEqual(cls.userlist, userlist)
    def test_invalidUpdate(self):
        userlist = [x+100 for x in range(len(self.temp_files))]
        cls = ListInfoGroup(userlist=userlist, subclass=TestInfoGroup, subargs={"basepath": self.temp_dir})
        self.assertRaises(IndexError, cls.generate)
        cls.update()
        self.assertEqual(cls._instances, [])
        self.assertEqual(cls._data, {})
        self.assertEqual(cls.userlist, userlist)
    def test_invalidGet(self):
        userlist = [x+100 for x in range(len(self.temp_files))]
        cls = ListInfoGroup(userlist=userlist, subclass=TestInfoGroup, subargs={"basepath": self.temp_dir})
        self.assertRaises(IndexError, cls.generate)
        cls.update()
        outdict = cls.get()
        self.assertEqual(outdict, {})
        self.assertEqual(cls._instances, [])
        self.assertEqual(cls._data, {})
        self.assertEqual(cls.userlist, userlist)
    def test_validCreateInvalidClass(self):
        userlist = [x for x in range(len(self.temp_files))]
        cls = ListInfoGroup(userlist=userlist, subclass=unittest.TestCase, subargs={"basepath": self.temp_dir})
        self.assertEqual(cls._instances, [])
        self.assertEqual(cls.subclass, unittest.TestCase)
    def test_validGenerateInvalidClass(self):
        userlist = [x for x in range(len(self.temp_files))]
        cls = ListInfoGroup(userlist=userlist, subclass=unittest.TestCase, subargs={"basepath": self.temp_dir})
        self.assertRaises(TypeError, cls.generate)
    def test_validUpdateInvalidClass(self):
        userlist = [x for x in range(len(self.temp_files))]
        cls = ListInfoGroup(userlist=userlist, subclass=unittest.TestCase, subargs={"basepath": self.temp_dir})
        try:
            cls.generate()
        except:
            pass
        cls.update()
        self.assertEqual(cls._instances, [])
        self.assertEqual(cls._data, {})
    def test_validGetInvalidClass(self):
        userlist = [x for x in range(len(self.temp_files))]
        cls = ListInfoGroup(userlist=userlist, subclass=unittest.TestCase, subargs={"basepath": self.temp_dir})
        try:
            cls.generate()
        except:
            pass
        cls.update()
        outdict = cls.get()
        self.assertEqual(cls._instances, [])
        self.assertEqual(cls._data, {})
        self.assertEqual(outdict, {})
