#!/usr/bin/env python3
"""
High-level tests for the class MultiClassInfoGroup
"""
import os
import sys
import unittest
import tempfile
import shutil
import stat
import glob
from machinestate import MultiClassInfoGroup, InfoGroup
from locale import getpreferredencoding

ENCODING = getpreferredencoding()

class TestClass:
    pass

class TestInfoGroup(InfoGroup):
    def __init__(self, name=None, extended=False, anonymous=False, basepath="", ident=-1):
        super(TestInfoGroup, self).__init__(extended=extended, name=name, anonymous=anonymous)
        self.name = "File{}".format(ident)
        self.basepath = basepath
        self.ident = ident
        path = os.path.join(basepath, "{}*".format(ident))
        files = glob.glob(path)
        self.addf("File{}".format(ident), files[0], r"(.+)")


class TestMultiClassInfoGroupBase(unittest.TestCase):
    def test_empty(self):
        cls = MultiClassInfoGroup()
        self.assertEqual(cls.name, None)
        self.assertEqual(cls.extended, False)
        self.assertEqual(cls.anonymous, False)
        self.assertEqual(cls.files, {})
        self.assertEqual(cls.commands, {})
        self.assertEqual(cls.constants, {})
        self.assertEqual(cls._instances, [])

    def test_named(self):
        cls = MultiClassInfoGroup(name="Testname")
        self.assertEqual(cls.name, "Testname")
    def test_extended(self):
        cls = MultiClassInfoGroup(extended=True)
        self.assertEqual(cls.extended, True)
    def test_anonymous(self):
        cls = MultiClassInfoGroup(anonymous=True)
        self.assertEqual(cls.anonymous, True)
    def test_listempty(self):
        cls = MultiClassInfoGroup(classlist=[], classargs=[])
        self.assertEqual(cls.classlist, [])
        self.assertEqual(cls.classargs, [])
    def test_listonlyclass(self):
        cls = MultiClassInfoGroup(classlist=[TestClass], classargs=[])
        self.assertEqual(cls.classlist, [])
        self.assertEqual(cls.classargs, [])
    def test_listvalid(self):
        cls = MultiClassInfoGroup(classlist=[TestClass, TestClass], classargs=[{}, {}])
        self.assertEqual(cls.classlist, [TestClass, TestClass])
        self.assertEqual(cls.classargs, [{}, {}])


class TestMultiClassInfoGroupFunction(unittest.TestCase):
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
        classlist = [TestInfoGroup for x in range(4)]
        classargs = [{"ident" : x, "basepath" : self.temp_dir} for x in range(4)]
        cls = MultiClassInfoGroup(classlist=classlist, classargs=classargs)
        self.assertEqual(cls._instances, [])
        for i in range(4):
            self.assertEqual(cls.classlist[i], TestInfoGroup)
            self.assertEqual(cls.classargs[i]["ident"], i)
            self.assertEqual(cls.classargs[i]["basepath"], self.temp_dir)
        self.assertEqual(cls._data, {})

    def test_validGenerate(self):
        classlist = [TestInfoGroup for x in range(4)]
        classargs = [{"ident" : x, "basepath" : self.temp_dir} for x in range(4)]
        cls = MultiClassInfoGroup(classlist=classlist, classargs=classargs)
        cls.generate()
        self.assertNotEqual(cls._instances, [])
        self.assertEqual(len(cls._instances), 4)
        self.assertEqual(cls._data, {})
        for inst in cls._instances:
            self.assertEqual(inst._instances, [])
            self.assertEqual(inst._data, {})
    def test_validUpdate(self):
        classlist = [TestInfoGroup for x in range(4)]
        classargs = [{"ident" : x, "basepath" : self.temp_dir} for x in range(4)]
        cls = MultiClassInfoGroup(classlist=classlist, classargs=classargs)
        cls.generate()
        cls.update()
        self.assertEqual(cls._data, {})
        for inst in cls._instances:
            self.assertEqual(inst._instances, [])
            self.assertNotEqual(inst._data, {})
    def test_validGet(self):
        classlist = [TestInfoGroup for x in range(4)]
        classargs = [{"ident" : x, "basepath" : self.temp_dir} for x in range(4)]
        cls = MultiClassInfoGroup(classlist=classlist, classargs=classargs)
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
        classlist = [TestInfoGroup for x in range(4)]
        classargs = [{"ident" : x+100, "basepath" : self.temp_dir} for x in range(4)]
        cls = MultiClassInfoGroup(classlist=classlist, classargs=classargs)
        self.assertEqual(cls._instances, [])
        self.assertEqual(cls._data, {})
        for i in range(4):
            self.assertEqual(cls.classlist[i], TestInfoGroup)
            self.assertEqual(cls.classargs[i]["ident"], i+100)
            self.assertEqual(cls.classargs[i]["basepath"], self.temp_dir)
    def test_invalidGenerate(self):
        classlist = [TestInfoGroup for x in range(4)]
        classargs = [{"ident" : x+100, "basepath" : self.temp_dir} for x in range(4)]
        cls = MultiClassInfoGroup(classlist=classlist, classargs=classargs)
        #cls.generate()
        self.assertRaises(IndexError, cls.generate)
        self.assertEqual(cls._instances, [])
        self.assertEqual(cls._data, {})
        self.assertEqual(cls.classlist, classlist)
        self.assertEqual(cls.classargs, classargs)
    def test_invalidUpdate(self):
        classlist = [TestInfoGroup for x in range(4)]
        classargs = [{"ident" : x+100, "basepath" : self.temp_dir} for x in range(4)]
        cls = MultiClassInfoGroup(classlist=classlist, classargs=classargs)
        self.assertRaises(IndexError, cls.generate)
        cls.update()
        self.assertEqual(cls._instances, [])
        self.assertEqual(cls._data, {})
        self.assertEqual(cls.classlist, classlist)
        self.assertEqual(cls.classargs, classargs)
    def test_invalidGet(self):
        classlist = [TestInfoGroup for x in range(4)]
        classargs = [{"ident" : x+100, "basepath" : self.temp_dir} for x in range(4)]
        cls = MultiClassInfoGroup(classlist=classlist, classargs=classargs)
        self.assertRaises(IndexError, cls.generate)
        cls.update()
        outdict = cls.get()
        self.assertEqual(outdict, {})
        self.assertEqual(cls._instances, [])
        self.assertEqual(cls._data, {})
        self.assertEqual(cls.classlist, classlist)
        self.assertEqual(cls.classargs, classargs)
    def test_validCreateInvalidClass(self):
        classlist = [unittest.TestCase for x in range(4)]
        classargs = [{"ident" : x, "basepath" : self.temp_dir} for x in range(4)]
        cls = MultiClassInfoGroup(classlist=classlist, classargs=classargs)
        for i in range(4):
            self.assertEqual(cls.classlist[i], unittest.TestCase)
            self.assertEqual(cls.classargs[i]["ident"], i)
            self.assertEqual(cls.classargs[i]["basepath"], self.temp_dir)
    def test_validGenerateInvalidClass(self):
        classlist = [unittest.TestCase for x in range(4)]
        classargs = [{"ident" : x, "basepath" : self.temp_dir} for x in range(4)]
        cls = MultiClassInfoGroup(classlist=classlist, classargs=classargs)
        self.assertRaises(TypeError, cls.generate)
    def test_validUpdateInvalidClass(self):
        classlist = [unittest.TestCase for x in range(4)]
        classargs = [{"ident" : x, "basepath" : self.temp_dir} for x in range(4)]
        cls = MultiClassInfoGroup(classlist=classlist, classargs=classargs)
        try:
            cls.generate()
        except:
            pass
        cls.update()
        self.assertEqual(cls._instances, [])
        self.assertEqual(cls._data, {})
    def test_validGetInvalidClass(self):
        classlist = [unittest.TestCase for x in range(4)]
        classargs = [{"ident" : x, "basepath" : self.temp_dir} for x in range(4)]
        cls = MultiClassInfoGroup(classlist=classlist, classargs=classargs)
        try:
            cls.generate()
        except:
            pass
        cls.update()
        outdict = cls.get()
        self.assertEqual(cls._instances, [])
        self.assertEqual(cls._data, {})
        self.assertEqual(outdict, {})
