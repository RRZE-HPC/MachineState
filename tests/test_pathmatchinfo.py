#!/usr/bin/env python3
"""
High-level tests for the class PathMatchInfoGroup
"""
import os
import sys
import unittest
import tempfile
import shutil
import stat
from machinestate import PathMatchInfoGroup
from locale import getpreferredencoding

ENCODING = getpreferredencoding()

class TestClass:
    pass


class TestPathMatchInfoGroupBase(unittest.TestCase):
    def test_empty(self):
        cls = PathMatchInfoGroup()
        self.assertEqual(cls.name, None)
        self.assertEqual(cls.extended, False)
        self.assertEqual(cls.anon, False)
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
    def test_anon(self):
        cls = PathMatchInfoGroup(anon=True)
        self.assertEqual(cls.anon, True)
    def test_searchpathNotExist(self):
        cls = PathMatchInfoGroup(searchpath="/path/does/not/exist/*")
        self.assertEqual(cls.searchpath, None)
    def test_searchpathExist(self):
        cls = PathMatchInfoGroup(searchpath="/tmp/*")
        self.assertEqual(cls.searchpath, None)
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
        cls = PathMatchInfoGroup(subclass=TestClass)
        self.assertEqual(cls.subclass, TestClass)
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
