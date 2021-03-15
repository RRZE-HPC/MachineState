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
from machinestate import PathMatchInfoGroup, InfoGroup
from locale import getpreferredencoding

ENCODING = getpreferredencoding()

class TestPathMatchInfoGroup(InfoGroup):
    def __init__(self, ident, extended=False, anonymous=False, searchpath=""):
        super(TestPathMatchInfoGroup, self).__init__(
            anonymous=anonymous, extended=extended, name="File{}".format(ident))
        self.ident = ident
        self.searchpath = searchpath
        path = os.path.join(searchpath, "{}*".format(ident))
        files = glob.glob(path)
        self.addf("File{}".format(ident), files[0], r"(.+)")


class TestPathMatchInfoGroupBase(unittest.TestCase):
    def test_empty(self):
        cls = PathMatchInfoGroup()
        self.assertEqual(cls.name, None)
        self.assertEqual(cls.extended, False)
        self.assertEqual(cls.anonymous, False)
        self.assertEqual(cls.files, {})
        self.assertEqual(cls.commands, {})
        self.assertEqual(cls.constants, {})
        self.assertEqual(cls._instances, [])
        self.assertEqual(cls.searchpath, None)
        self.assertEqual(cls.match, None)
        self.assertEqual(cls.subclass, None)
        self.assertEqual(cls.subargs, {})

    def test_named(self):
        cls = PathMatchInfoGroup(name="Testname")
        self.assertEqual(cls.name, "Testname")
    def test_extended(self):
        cls = PathMatchInfoGroup(extended=True)
        self.assertEqual(cls.extended, True)
    def test_anonymous(self):
        cls = PathMatchInfoGroup(anonymous=True)
        self.assertEqual(cls.anonymous, True)
    def test_searchpathNotExist(self):
        cls = PathMatchInfoGroup(searchpath="/path/does/not/exist/*")
        self.assertEqual(cls.searchpath, None)
    def test_searchpathExist(self):
        cls = PathMatchInfoGroup(searchpath="/tmp/*")
        self.assertEqual(cls.searchpath, "/tmp/*")
    def test_searchpathNone(self):
        cls = PathMatchInfoGroup(searchpath=None)
        self.assertEqual(cls.searchpath, None)
    def test_searchpathBool(self):
        cls = PathMatchInfoGroup(searchpath=True)
        self.assertEqual(cls.searchpath, None)
    def test_searchpathInt(self):
        cls = PathMatchInfoGroup(searchpath=True)
        self.assertEqual(cls.searchpath, None)
    def test_subclassString(self):
        cls = PathMatchInfoGroup(subclass="abc")
        self.assertEqual(cls.subclass, None)
    def test_subclassNone(self):
        cls = PathMatchInfoGroup(subclass=None)
        self.assertEqual(cls.subclass, None)
    def test_subclassClass(self):
        cls = PathMatchInfoGroup(subclass=TestPathMatchInfoGroup)
        self.assertEqual(cls.subclass, TestPathMatchInfoGroup)
    def test_subargsNone(self):
        cls = PathMatchInfoGroup(subargs=None)
        self.assertEqual(cls.subargs, {})
    def test_subargsDict(self):
        cls = PathMatchInfoGroup(subargs={})
        self.assertEqual(cls.subargs, {})
    def test_subargsBool(self):
        cls = PathMatchInfoGroup(subargs=True)
        self.assertEqual(cls.subargs, {})
    def test_subargsList(self):
        cls = PathMatchInfoGroup(subargs=[])
        self.assertEqual(cls.subargs, {})

class TestPathMatchInfoGroupFunction(unittest.TestCase):
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
        searchpath = os.path.join(self.temp_dir, "*")
        cls = PathMatchInfoGroup(searchpath=searchpath, match=r".*/(\d).*", subclass=TestPathMatchInfoGroup, subargs={"searchpath": self.temp_dir})
        self.assertEqual(cls._instances, [])
        self.assertEqual(cls._data, {})

    def test_validGenerate(self):
        searchpath = os.path.join(self.temp_dir, "*")
        cls = PathMatchInfoGroup(searchpath=searchpath, match=r".*/(\d).*", subclass=TestPathMatchInfoGroup, subargs={"searchpath": self.temp_dir})
        cls.generate()
        self.assertNotEqual(cls._instances, [])
        self.assertEqual(len(cls._instances), 4)
        self.assertEqual(cls._data, {})
        for inst in cls._instances:
            self.assertEqual(inst._instances, [])
            self.assertEqual(inst._data, {})
    def test_validUpdate(self):
        searchpath = os.path.join(self.temp_dir, "*")
        cls = PathMatchInfoGroup(searchpath=searchpath, match=r".*/(\d).*", subclass=TestPathMatchInfoGroup, subargs={"searchpath": self.temp_dir})
        cls.generate()
        cls.update()
        self.assertEqual(cls._data, {})
        for inst in cls._instances:
            self.assertEqual(inst._instances, [])
            self.assertNotEqual(inst._data, {})
    def test_validGet(self):
        searchpath = os.path.join(self.temp_dir, "*")
        cls = PathMatchInfoGroup(searchpath=searchpath, match=r".*/(\d).*", subclass=TestPathMatchInfoGroup, subargs={"searchpath": self.temp_dir})
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
        searchpath = os.path.join(self.temp_dir, "*abc")
        cls = PathMatchInfoGroup(searchpath=searchpath, match=r".*/(\d).*", subclass=TestPathMatchInfoGroup, subargs={"searchpath": self.temp_dir})
        self.assertEqual(cls._instances, [])
        self.assertEqual(cls._data, {})
        self.assertEqual(cls.searchpath, searchpath)
    def test_invalidGenerate(self):
        searchpath = os.path.join(self.temp_dir, "*abc")
        cls = PathMatchInfoGroup(searchpath=searchpath, match=r".*/(\d).*", subclass=TestPathMatchInfoGroup, subargs={"searchpath": self.temp_dir})
        cls.generate()
        self.assertEqual(cls._instances, [])
        self.assertEqual(cls._data, {})
        self.assertEqual(cls.searchpath, searchpath)
    def test_invalidUpdate(self):
        searchpath = os.path.join(self.temp_dir, "*abc")
        cls = PathMatchInfoGroup(searchpath=searchpath, match=r".*/(\d).*", subclass=TestPathMatchInfoGroup, subargs={"searchpath": self.temp_dir})
        cls.generate()
        cls.update()
        self.assertEqual(cls._instances, [])
        self.assertEqual(cls._data, {})
        self.assertEqual(cls.searchpath, searchpath)
    def test_invalidGet(self):
        searchpath = os.path.join(self.temp_dir, "*abc")
        cls = PathMatchInfoGroup(searchpath=searchpath, match=r".*/(\d).*", subclass=TestPathMatchInfoGroup, subargs={"searchpath": self.temp_dir})
        cls.generate()
        cls.update()
        outdict = cls.get()
        self.assertEqual(outdict, {})
        self.assertEqual(cls._instances, [])
        self.assertEqual(cls._data, {})
        self.assertEqual(cls.searchpath, searchpath)
    def test_validCreateInvalidClass(self):
        searchpath = os.path.join(self.temp_dir, "*")
        cls = PathMatchInfoGroup(searchpath=searchpath, match=r".*/(\d).*", subclass=unittest.TestCase, subargs={"searchpath": self.temp_dir})
        self.assertEqual(cls._instances, [])
        self.assertEqual(cls.subclass, unittest.TestCase)
    def test_validGenerateInvalidClass(self):
        searchpath = os.path.join(self.temp_dir, "*")
        cls = PathMatchInfoGroup(searchpath=searchpath, match=r".*/(\d).*", subclass=unittest.TestCase, subargs={"searchpath": self.temp_dir})
        self.assertRaises(TypeError, cls.generate)
    def test_validUpdateInvalidClass(self):
        searchpath = os.path.join(self.temp_dir, "*")
        cls = PathMatchInfoGroup(searchpath=searchpath, match=r".*/(\d).*", subclass=unittest.TestCase, subargs={"searchpath": self.temp_dir})
        try:
            cls.generate()
        except:
            pass
        cls.update()
        self.assertEqual(cls._instances, [])
        self.assertEqual(cls._data, {})
    def test_validGetInvalidClass(self):
        searchpath = os.path.join(self.temp_dir, "*")
        cls = PathMatchInfoGroup(searchpath=searchpath, match=r".*/(\d).*", subclass=unittest.TestCase, subargs={"searchpath": self.temp_dir})
        try:
            cls.generate()
        except:
            pass
        cls.update()
        outdict = cls.get()
        self.assertEqual(cls._instances, [])
        self.assertEqual(cls._data, {})
        self.assertEqual(outdict, {})
