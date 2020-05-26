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
from machinestate import ListInfoGroup
from locale import getpreferredencoding

ENCODING = getpreferredencoding()

class TestClass:
    pass

class TestListInfoGroupBase(unittest.TestCase):
    def test_empty(self):
        cls = ListInfoGroup()
        self.assertEqual(cls.name, None)
        self.assertEqual(cls.extended, False)
        self.assertEqual(cls.anon, False)
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
    def test_anon(self):
        cls = ListInfoGroup(anon=True)
        self.assertEqual(cls.anon, True)
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
