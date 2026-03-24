#!/usr/bin/env python3

import sys, os, os.path, json
sys.path.append("..")

from locale import getpreferredencoding
ENCODING = getpreferredencoding()

import unittest
from unittest.mock import patch

import BiosInfo

def readfile(filename):
    data = None
    if os.path.exists(filename):
        with open(filename, 'rb') as filefp:
            data = filefp.read().decode(ENCODING)
    return data

basedir = "./tests"
REAL_BIOS_PATH = "/sys/devices/virtual/dmi/id"

def redirect_bios_path(path, fake_base):
    if path == REAL_BIOS_PATH:
        return fake_base
    if path.startswith(REAL_BIOS_PATH + "/"):
        suffix = path[len(REAL_BIOS_PATH) + 1:]
        return os.path.join(fake_base, suffix)
    return path

def runtest(self, testfolder):
    fake_base = os.path.join(testfolder, "sys/devices/virtual/dmi/id")

    def fake_pexists(path):
        redirected_path = redirect_bios_path(path, fake_base)
        return os.path.exists(redirected_path)
    
    def fake_pjoin(a, *parts):
        joined = os.path.join(a, *parts)
        return redirect_bios_path(joined, fake_base)
    
    with patch('BiosInfo.pexists', side_effect=fake_pexists), \
         patch('BiosInfo.pjoin', side_effect=fake_pjoin):
        c = BiosInfo.BiosInfo()
        c.update()
        j = c.get_json()

    ref = readfile(os.path.join(testfolder, "output"))
    self.assertEqual(json.loads(ref), json.loads(j))

class TestBiosInfo(unittest.TestCase):
    def test_full(self):
        runtest(self, os.path.join(basedir, "full"))

    def test_no_product_vendor(self):
        runtest(self, os.path.join(basedir, "no_product_vendor"))

    def test_missing_base(self):
        runtest(self, os.path.join(basedir, "missing_base"))


if __name__ == '__main__':
    unittest.main()