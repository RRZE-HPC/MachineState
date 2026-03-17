#!/usr/bin/env python3

import sys, os, os.path
sys.path.append("..")

from locale import getpreferredencoding
ENCODING = getpreferredencoding()

import unittest

import ModulesInfo

def readfile(filename):
    data = None
    if os.path.exists(filename):
        with open(filename, 'rb') as filefp:
            data = filefp.read().decode(ENCODING)
    return data

basedir = "./tests"


def runtest(self, testfolder):
    os.environ["MODULES_CMD"] = os.path.join(basedir, "fakemodules.sh")
    c = ModulesInfo.ModulesInfo(modulecmd=os.path.join(basedir, "fakemodules.sh"))
    c.generate()
    os.environ["FAKEMODULES_INPUT"] = os.path.join(testfolder, "input")
    c.update()
    j = c.get_json()
    ref = readfile(os.path.join(testfolder, "output"))
    self.assertEqual(ref.strip(), j.strip())
    if ref.strip() != j.strip():
        print(j.strip())


class TestModulesInfo(unittest.TestCase):
    def test_tcl_5_0_1(self):
        runtest(self, os.path.join(basedir, "tcl_5.0.1"))
    def test_tcl_5_5_0(self):
        runtest(self, os.path.join(basedir, "tcl_5.5.0"))
    def test_tcl_5_5_0_empty(self):
        runtest(self, os.path.join(basedir, "tcl_5.5.0_empty"))
    def test_tcl_5_6_0(self):
        runtest(self, os.path.join(basedir, "tcl_5.6.0"))

if __name__ == '__main__':
    unittest.main()
