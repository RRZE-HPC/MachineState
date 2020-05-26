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
from machinestate import MultiClassInfoGroup
from locale import getpreferredencoding

ENCODING = getpreferredencoding()

class TestClass:
    pass


class TestMultiClassInfoGroupBase(unittest.TestCase):
    def test_empty(self):
        cls = MultiClassInfoGroup()
        self.assertEqual(cls.name, None)
        self.assertEqual(cls.extended, False)
        self.assertEqual(cls.anon, False)
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
    def test_anon(self):
        cls = MultiClassInfoGroup(anon=True)
        self.assertEqual(cls.anon, True)
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
