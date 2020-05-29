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
import machinestate
from locale import getpreferredencoding

ENCODING = getpreferredencoding()


class TestParsers(unittest.TestCase):
    # Tests for tostrlist
    def test_tostrlistNone(self):
        out = machinestate.tostrlist(None)
        self.assertEqual(out, None)
    def test_tostrlistInt(self):
        out = machinestate.tostrlist(1)
        self.assertEqual(out, ["1"])
    def test_tostrlistValidSpaces(self):
        out = machinestate.tostrlist("a b c")
        self.assertEqual(out, ["a", "b", "c"])
    def test_tostrlistValidTabs(self):
        out = machinestate.tostrlist("a\tb\tc")
        self.assertEqual(out, ["a", "b", "c"])
    def test_tostrlistValidComma(self):
        out = machinestate.tostrlist("a,b,c")
        self.assertEqual(out, ["a", "b", "c"])
    # Tests for tointlist
    def test_tointlistNone(self):
        out = machinestate.tointlist(None)
        self.assertEqual(out, None)
    def test_tointlistInt(self):
        out = machinestate.tointlist(1)
        self.assertEqual(out, [1])
    def test_tointlistValidSpaces(self):
        out = machinestate.tointlist("1 2 3")
        self.assertEqual(out, [1, 2, 3])
    def test_tointlistValidTabs(self):
        out = machinestate.tointlist("1\t2\t3")
        self.assertEqual(out, [1, 2, 3])
    def test_tointlistValidComma(self):
        out = machinestate.tointlist("1,2,3")
        self.assertEqual(out, [1, 2, 3])
    # def test_tostrlistInvalidNoNumbers(self):
    #     self.assertRaises(ValueError, machinestate.tointlist("a b c"))
    # Tests for tobytes
    def test_tobytesNone(self):
        out = machinestate.tobytes(None)
        self.assertEqual(out, None)
    def test_tobytesInt(self):
        out = machinestate.tobytes(1)
        self.assertEqual(out, 1)
    def test_tobytesValidStrPlain(self):
        out = machinestate.tobytes("1234")
        self.assertEqual(out, 1234)
    def test_tobytesValidStrB(self):
        out = machinestate.tobytes("1234 B")
        self.assertEqual(out, 1234)
    def test_tobytesValidStrBNoSpace(self):
        out = machinestate.tobytes("1234B")
    def test_tobytesValidStrkB(self):
        out = machinestate.tobytes("1234 kB")
        self.assertEqual(out, 1234*1024)
    def test_tobytesValidStrkBNoSpace(self):
        out = machinestate.tobytes("1234kB")
        self.assertEqual(out, 1234*1024)
    def test_tobytesValidStrKB(self):
        out = machinestate.tobytes("1234 KB")
        self.assertEqual(out, 1234*1024)
    def test_tobytesValidStrKBNoSpace(self):
        out = machinestate.tobytes("1234KB")
        self.assertEqual(out, 1234*1024)
    def test_tobytesValidStrmB(self):
        out = machinestate.tobytes("1234 mB")
        self.assertEqual(out, 1234*1024*1024)
    def test_tobytesValidStrmBNoSpace(self):
        out = machinestate.tobytes("1234mB")
        self.assertEqual(out, 1234*1024*1024)
    def test_tobytesValidStrMB(self):
        out = machinestate.tobytes("1234 MB")
        self.assertEqual(out, 1234*1024*1024)
    def test_tobytesValidStrMBNoSpace(self):
        out = machinestate.tobytes("1234MB")
        self.assertEqual(out, 1234*1024*1024)
    def test_tobytesValidStrgB(self):
        out = machinestate.tobytes("1234 gB")
        self.assertEqual(out, 1234*1024*1024*1024)
    def test_tobytesValidStrgBNoSpace(self):
        out = machinestate.tobytes("1234gB")
        self.assertEqual(out, 1234*1024*1024*1024)
    def test_tobytesValidStrGB(self):
        out = machinestate.tobytes("1234 GB")
        self.assertEqual(out, 1234*1024*1024*1024)
    def test_tobytesValidStrGBNoSpace(self):
        out = machinestate.tobytes("1234GB")
        self.assertEqual(out, 1234*1024*1024*1024)
    def test_tobytesValidStrkiB(self):
        out = machinestate.tobytes("1234 kiB")
        self.assertEqual(out, 1234*1000)
    def test_tobytesValidStrkiBNoSpace(self):
        out = machinestate.tobytes("1234kiB")
        self.assertEqual(out, 1234*1000)
    def test_tobytesValidStrKiB(self):
        out = machinestate.tobytes("1234 KiB")
        self.assertEqual(out, 1234*1000)
    def test_tobytesValidStrKiBNoSpace(self):
        out = machinestate.tobytes("1234KiB")
        self.assertEqual(out, 1234*1000)
    def test_tobytesValidStrmiB(self):
        out = machinestate.tobytes("1234 miB")
        self.assertEqual(out, 1234*1000*1000)
    def test_tobytesValidStrmiBNoSpace(self):
        out = machinestate.tobytes("1234miB")
        self.assertEqual(out, 1234*1000*1000)
    def test_tobytesValidStrMiB(self):
        out = machinestate.tobytes("1234 MiB")
        self.assertEqual(out, 1234*1000*1000)
    def test_tobytesValidStrMiBNoSpace(self):
        out = machinestate.tobytes("1234MiB")
        self.assertEqual(out, 1234*1000*1000)
    def test_tobytesValidStrgiB(self):
        out = machinestate.tobytes("1234 giB")
        self.assertEqual(out, 1234*1000*1000*1000)
    def test_tobytesValidStrgiBNoSpace(self):
        out = machinestate.tobytes("1234giB")
        self.assertEqual(out, 1234*1000*1000*1000)
    def test_tobytesValidStrGiB(self):
        out = machinestate.tobytes("1234 GiB")
        self.assertEqual(out, 1234*1000*1000*1000)
    def test_tobytesValidStrGiBNoSpace(self):
        out = machinestate.tobytes("1234GiB")
        self.assertEqual(out, 1234*1000*1000*1000)
    def test_tobytesNotValid(self):
        out = machinestate.tobytes("1234abc")
        self.assertEqual(out, 1234)
    # Tests for masktolist
    def test_masktolistNone(self):
        out = machinestate.masktolist(None)
        self.assertEqual(out, None)
    def test_masktolistInt(self):
        out = machinestate.masktolist(1)
        self.assertEqual(out, [0])
    def test_masktolistIntMask(self):
        out = machinestate.masktolist(0xff)
        self.assertEqual(out, [x for x in range(8)])
    def test_masktolistStrMask(self):
        out = machinestate.masktolist("ff")
        self.assertEqual(out, [x for x in range(8)])
    def test_masktolistStrMaskHex(self):
        out = machinestate.masktolist("0xff")
        self.assertEqual(out, [x for x in range(8)])
    def test_masktolistStrMaskComma(self):
        out = machinestate.masktolist("ff,FF")
        self.assertEqual(out, [x for x in range(16)])
    # Tests for kHztoHz
    def test_kHztoHzNone(self):
        out = machinestate.kHztoHz(None)
        self.assertEqual(out, None)
    def test_kHztoHzInt(self):
        out = machinestate.kHztoHz(1000)
        self.assertEqual(out, 1000)
    def test_kHztoHzIntStr(self):
        # string without unit are seen as kHz
        out = machinestate.kHztoHz("10000")
        self.assertEqual(out, 10000000)
    def test_kHztoHzStrHz(self):
        out = machinestate.kHztoHz("1234 Hz")
        self.assertEqual(out, 1234)
    def test_kHztoHzStrhz(self):
        out = machinestate.kHztoHz("1234hz")
        self.assertEqual(out, 1234)
    def test_kHztoHzStrkHz(self):
        out = machinestate.kHztoHz("1234 kHz")
        self.assertEqual(out, 1234*1000)
    def test_kHztoHzStrKHz(self):
        out = machinestate.kHztoHz("1234KHz")
        self.assertEqual(out, 1234*1000)
    def test_kHztoHzStrmHz(self):
        out = machinestate.kHztoHz("1234 mHz")
        self.assertEqual(out, 1234000000)
    def test_kHztoHzStrMHz(self):
        out = machinestate.kHztoHz("1234 MHz")
        self.assertEqual(out, 1234000000)
    def test_kHztoHzStrGHz(self):
        out = machinestate.kHztoHz("1234 GHz")
        self.assertEqual(out, 1234000000000)
    def test_kHztoHzStrgHz(self):
        out = machinestate.kHztoHz("1234gHz")
        self.assertEqual(out, 1234000000000)
    def test_kHztoHzFloat(self):
        out = machinestate.kHztoHz(1000.00)
        self.assertEqual(out, 1000)
    def test_kHztoHzFloatStr(self):
        # string without unit are seen as kHz
        out = machinestate.kHztoHz("10000.00")
        self.assertEqual(out, 10000000)
    def test_kHztoHzStrfHz(self):
        out = machinestate.kHztoHz("1234.00 Hz")
        self.assertEqual(out, 1234)
    def test_kHztoHzStrfhz(self):
        out = machinestate.kHztoHz("1234.00hz")
        self.assertEqual(out, 1234)
    def test_kHztoHzStrfkHz(self):
        out = machinestate.kHztoHz("1234.00 kHz")
        self.assertEqual(out, 1234*1000)
    def test_kHztoHzStrfKHz(self):
        out = machinestate.kHztoHz("1234.00KHz")
        self.assertEqual(out, 1234*1000)
    def test_kHztoHzStrfmHz(self):
        out = machinestate.kHztoHz("1234.00 mHz")
        self.assertEqual(out, 1234000000)
    def test_kHztoHzStrfMHz(self):
        out = machinestate.kHztoHz("1234.00 MHz")
        self.assertEqual(out, 1234000000)
    def test_kHztoHzStrfGHz(self):
        out = machinestate.kHztoHz("1234.00 GHz")
        self.assertEqual(out, 1234000000000)
    def test_kHztoHzStrfgHz(self):
        out = machinestate.kHztoHz("1234.00gHz")
        self.assertEqual(out, 1234000000000)

    # Tests for kHzlisttoHzlist
    def test_kHzlisttoHzlistNone(self):
        out = machinestate.kHzlisttoHzlist(None)
        self.assertEqual(out, None)
    def test_kHzlisttoHzlistInt(self):
        out = machinestate.kHzlisttoHzlist(1000)
        self.assertEqual(out, [1000])
    def test_kHzlisttoHzlistFloatStrSpace(self):
        # string without unit are seen as kHz
        out = machinestate.kHzlisttoHzlist("10000.00 20000.00 30000.00")
        self.assertEqual(out, [10000000, 20000000, 30000000])
    def test_kHzlisttoHzlistFloatStrComma(self):
        # string without unit are seen as kHz
        out = machinestate.kHzlisttoHzlist("10000.00,20000.00,30000.00")
        self.assertEqual(out, [10000000, 20000000, 30000000])
    def test_kHzlisttoHzlistIntStrSpace(self):
        # string without unit are seen as kHz
        out = machinestate.kHzlisttoHzlist("10000 20000 30000")
        self.assertEqual(out, [10000000, 20000000, 30000000])
    def test_kHzlisttoHzlistIntStrComma(self):
        # string without unit are seen as kHz
        out = machinestate.kHzlisttoHzlist("10000,20000,30000")
        self.assertEqual(out, [10000000, 20000000, 30000000])

    def test_kHzlisttoHzlistFloatStrSpacekHz(self):
        # string without unit are seen as kHz
        out = machinestate.kHzlisttoHzlist("10000.00kHz 20000.00kHz 30000.00KHz")
        self.assertEqual(out, [10000000, 20000000, 30000000])
    def test_kHzlisttoHzlistFloatStrCommakHz(self):
        # string without unit are seen as kHz
        out = machinestate.kHzlisttoHzlist("10000.00kHz, 20000.00kHz, 30000.00KHz")
        self.assertEqual(out, [10000000, 20000000, 30000000])
    def test_kHzlisttoHzlistIntStrSpacekHz(self):
        # string without unit are seen as kHz
        out = machinestate.kHzlisttoHzlist("10000khz 20000.00kHz 30000.00KHz")
        self.assertEqual(out, [10000000, 20000000, 30000000])
    def test_kHzlisttoHzlistIntStrCommakHz(self):
        # string without unit are seen as kHz
        out = machinestate.kHzlisttoHzlist("10000kHz,20000KHz,30000khz")
        self.assertEqual(out, [10000000, 20000000, 30000000])