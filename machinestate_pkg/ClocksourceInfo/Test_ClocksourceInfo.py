#!/usr/bin/env python3

import sys, os, os.path, json, glob as stdglob
sys.path.append("..")

from locale import getpreferredencoding
ENCODING = getpreferredencoding()

import unittest
from unittest.mock import patch

import ClocksourceInfo

def readfile(filename):
    data = None
    if os.path.exists(filename):
        with open(filename, "rb") as filefp:
            data = filefp.read().decode(ENCODING)
    return data

basedir = "./tests"
REAL_CLOCKSOURCE_PATH = "/sys/devices/system/clocksource"
REAL_CLOCKSOURCE_SEARCH = REAL_CLOCKSOURCE_PATH + "/clocksource*"

def redirect_path(path, fake_base):
    if path == REAL_CLOCKSOURCE_PATH:
        return fake_base
    if path == REAL_CLOCKSOURCE_SEARCH:
        return os.path.join(fake_base, "clocksource*")
    if path.startswith(REAL_CLOCKSOURCE_PATH + "/"):
        suffix = path[len(REAL_CLOCKSOURCE_PATH) + 1:]
        return os.path.join(fake_base, suffix)
    return path

def runtest(self, testfolder, extended=False):
    fake_base = os.path.join(testfolder, "sys/devices/system/clocksource")

    def fake_pjoin(a, *parts):
        path = os.path.join(a, *parts)
        return redirect_path(path, fake_base)

    def fake_glob(pattern):
        redirected_pattern = redirect_path(pattern, fake_base)
        return stdglob.glob(redirected_pattern)

    with patch("ClocksourceInfo.pjoin", side_effect=fake_pjoin), \
         patch("common.glob", side_effect=fake_glob):

        c = ClocksourceInfo.ClocksourceInfo(extended=extended)
        c.generate()
        c.update()
        j = c.get_json()

    ref = readfile(os.path.join(testfolder, "output"))
    self.assertEqual(json.loads(ref), json.loads(j))

class TestClocksourceInfo(unittest.TestCase):
    def test_full(self):
        runtest(self, os.path.join(basedir, "full"))

    def test_missing_current(self):
        runtest(self, os.path.join(basedir, "missing_current"))

    def test_extended(self):
        runtest(self, os.path.join(basedir, "extended"), extended=True)

if __name__ == "__main__":
    unittest.main()