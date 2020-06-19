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


class TestToStrList(unittest.TestCase):
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

class TestToIntList(unittest.TestCase):
    # Tests for tointlist
    def test_tointlistNone(self):
        out = machinestate.tointlist(None)
        self.assertEqual(out, None)
    def test_tointlistInt(self):
        out = machinestate.tointlist(1)
        self.assertEqual(out, [1])
    def test_tointlistFloat(self):
        out = machinestate.tointlist(1.0)
        self.assertEqual(out, [1])
    def test_tointlistValidSpaces(self):
        out = machinestate.tointlist("1 2 3")
        self.assertEqual(out, [1, 2, 3])
    def test_tointlistValidTabs(self):
        out = machinestate.tointlist("1\t2\t3")
        self.assertEqual(out, [1, 2, 3])
    def test_tointlistValidFloats(self):
        out = machinestate.tointlist("1.0 2.0 3.0")
        self.assertEqual(out, [1, 2, 3])
    def test_tointlistValidComma(self):
        out = machinestate.tointlist("1,2,3")
        self.assertEqual(out, [1, 2, 3])
    def test_tointlistValidRange(self):
        out = machinestate.tointlist("1-3")
        self.assertEqual(out, [1, 2, 3])
    def test_tointlistValidMixed(self):
        out = machinestate.tointlist("1-3,4")
        self.assertEqual(out, [1, 2, 3, 4])
    def test_tostrlistInvalidNoNumbers(self):
        self.assertRaises(ValueError, machinestate.tointlist, "a b c")
    def test_tostrlistInvalidNoNumbersRange(self):
        self.assertRaises(ValueError, machinestate.tointlist, "a-c")
    def test_tostrlistInvalidNoNumbersMixed(self):
        self.assertRaises(ValueError, machinestate.tointlist, "a-b,c")

class TestToBytes(unittest.TestCase):
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
    def test_tobytesValidInvalidSuffix(self):
        out = machinestate.tobytes("1234abc")
    def test_tobytesNotValid(self):
        out = machinestate.tobytes("abc")
        self.assertEqual(out, None)
    def test_tobytesAlmostValid(self):
        self.assertRaises(ValueError, machinestate.tobytes, ". kb")

class TestMaskToList(unittest.TestCase):
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
    def test_masktolistIntValue(self):
        out = machinestate.masktolist(11)
        self.assertEqual(out, [0, 1, 3])
    def test_masktolistStrMask(self):
        out = machinestate.masktolist("ff")
        self.assertEqual(out, [x for x in range(8)])
    def test_masktolistStrMaskHex(self):
        out = machinestate.masktolist("0xff")
        self.assertEqual(out, [x for x in range(8)])
    def test_masktolistStrMaskComma(self):
        out = machinestate.masktolist("ff,FF")
        self.assertEqual(out, [x for x in range(16)])

class TestToHertz(unittest.TestCase):
    # Tests for tohertz
    def test_tohertzNone(self):
        out = machinestate.tohertz(None)
        self.assertEqual(out, None)
    def test_tohertzInt(self):
        out = machinestate.tohertz(1000)
        self.assertEqual(out, 1000)
    def test_tohertzIntStr(self):
        # string without unit are seen as kHz
        out = machinestate.tohertz("10000")
        self.assertEqual(out, 10000000)
    def test_tohertzStrHz(self):
        out = machinestate.tohertz("1234 Hz")
        self.assertEqual(out, 1234)
    def test_tohertzStrhz(self):
        out = machinestate.tohertz("1234hz")
        self.assertEqual(out, 1234)
    def test_tohertzStrkHz(self):
        out = machinestate.tohertz("1234 kHz")
        self.assertEqual(out, 1234*1000)
    def test_tohertzStrKHz(self):
        out = machinestate.tohertz("1234KHz")
        self.assertEqual(out, 1234*1000)
    def test_tohertzStrmHz(self):
        out = machinestate.tohertz("1234 mHz")
        self.assertEqual(out, 1234000000)
    def test_tohertzStrMHz(self):
        out = machinestate.tohertz("1234 MHz")
        self.assertEqual(out, 1234000000)
    def test_tohertzStrGHz(self):
        out = machinestate.tohertz("1234 GHz")
        self.assertEqual(out, 1234000000000)
    def test_tohertzStrgHz(self):
        out = machinestate.tohertz("1234gHz")
        self.assertEqual(out, 1234000000000)
    def test_tohertzFloat(self):
        out = machinestate.tohertz(1000.00)
        self.assertEqual(out, 1000)
    def test_tohertzFloatStr(self):
        # string without unit are seen as kHz
        out = machinestate.tohertz("10000.00")
        self.assertEqual(out, 10000000)
    def test_tohertzStrfHz(self):
        out = machinestate.tohertz("1234.00 Hz")
        self.assertEqual(out, 1234)
    def test_tohertzStrfhz(self):
        out = machinestate.tohertz("1234.00hz")
        self.assertEqual(out, 1234)
    def test_tohertzStrfkHz(self):
        out = machinestate.tohertz("1234.00 kHz")
        self.assertEqual(out, 1234*1000)
    def test_tohertzStrfKHz(self):
        out = machinestate.tohertz("1234.00KHz")
        self.assertEqual(out, 1234*1000)
    def test_tohertzStrfmHz(self):
        out = machinestate.tohertz("1234.00 mHz")
        self.assertEqual(out, 1234000000)
    def test_tohertzStrfMHz(self):
        out = machinestate.tohertz("1234.00 MHz")
        self.assertEqual(out, 1234000000)
    def test_tohertzStrfGHz(self):
        out = machinestate.tohertz("1234.00 GHz")
        self.assertEqual(out, 1234000000000)
    def test_tohertzStrfgHz(self):
        out = machinestate.tohertz("1234.00gHz")
        self.assertEqual(out, 1234000000000)
    def test_tohertzStrAlmostValid(self):
        self.assertRaises(ValueError, machinestate.tohertz, ".ghz")
    def test_tohertzStrNotValid(self):
        out = machinestate.tohertz("abc")
        self.assertEqual(out, None)

class TestToHertzList(unittest.TestCase):
    # Tests for tohertzlist
    def test_tohertzlistNone(self):
        out = machinestate.tohertzlist(None)
        self.assertEqual(out, None)
    def test_tohertzlistInt(self):
        out = machinestate.tohertzlist(1000)
        self.assertEqual(out, [1000])
    def test_tohertzlistFloatStrSpace(self):
        # string without unit are seen as kHz
        out = machinestate.tohertzlist("10000.00 20000.00 30000.00")
        self.assertEqual(out, [10000000, 20000000, 30000000])
    def test_tohertzlistFloatStrComma(self):
        # string without unit are seen as kHz
        out = machinestate.tohertzlist("10000.00,20000.00,30000.00")
        self.assertEqual(out, [10000000, 20000000, 30000000])
    def test_tohertzlistIntStrSpace(self):
        # string without unit are seen as kHz
        out = machinestate.tohertzlist("10000 20000 30000")
        self.assertEqual(out, [10000000, 20000000, 30000000])
    def test_tohertzlistIntStrComma(self):
        # string without unit are seen as kHz
        out = machinestate.tohertzlist("10000,20000,30000")
        self.assertEqual(out, [10000000, 20000000, 30000000])
    def test_tohertzlistFloatStrSpacekHz(self):
        # string without unit are seen as kHz
        out = machinestate.tohertzlist("10000.00kHz 20000.00kHz 30000.00KHz")
        self.assertEqual(out, [10000000, 20000000, 30000000])
    def test_tohertzlistFloatStrCommakHz(self):
        # string without unit are seen as kHz
        out = machinestate.tohertzlist("10000.00kHz, 20000.00kHz, 30000.00KHz")
        self.assertEqual(out, [10000000, 20000000, 30000000])
    def test_tohertzlistIntStrSpacekHz(self):
        # string without unit are seen as kHz
        out = machinestate.tohertzlist("10000khz 20000.00kHz 30000.00KHz")
        self.assertEqual(out, [10000000, 20000000, 30000000])
    def test_tohertzlistIntStrCommakHz(self):
        # string without unit are seen as kHz
        out = machinestate.tohertzlist("10000kHz,20000KHz,30000khz")
        self.assertEqual(out, [10000000, 20000000, 30000000])

class TestToTitle(unittest.TestCase):
    def test_totitleNone(self):
        out = machinestate.totitle(None)
        self.assertEqual(out, "None")
    def test_totitleInt(self):
        out = machinestate.totitle(1234)
        self.assertEqual(out, "1234")
    def test_totitleFloat(self):
        out = machinestate.totitle(1234.01)
        self.assertEqual(out, "1234.01")
    def test_totitleList(self):
        out = machinestate.totitle([1234.01, "123"])
        self.assertEqual(out, str([1234.01, "123"]))
    def test_totitleEmpty(self):
        out = machinestate.totitle("")
        self.assertEqual(out, "")
    def test_totitleSpace(self):
        out = machinestate.totitle("abc defg")
        self.assertEqual(out, "AbcDefg")
    def test_totitleDash(self):
        out = machinestate.totitle("abc-defg")
        self.assertEqual(out, "Abc-Defg")
    def test_totitleUnderscore(self):
        out = machinestate.totitle("abc_defg")
        self.assertEqual(out, "AbcDefg")
    def test_totitleMixed(self):
        out = machinestate.totitle("abc_defg-hij")
        self.assertEqual(out, "AbcDefg-Hij")

class TestToBool(unittest.TestCase):
    def test_toboolIntFalse(self):
        out = machinestate.tobool(0)
        self.assertEqual(out, False)
    def test_toboolIntTrue1(self):
        out = machinestate.tobool(1)
        self.assertEqual(out, True)
    def test_toboolIntTrue2(self):
        out = machinestate.tobool(2)
        self.assertEqual(out, True)
    def test_toboolIntTrueNeg4(self):
        out = machinestate.tobool(-4)
        self.assertEqual(out, True)
    def test_toboolFloatFalse(self):
        out = machinestate.tobool(0.0)
        self.assertEqual(out, False)
    def test_toboolFloatTruePos(self):
        out = machinestate.tobool(1.2)
        self.assertEqual(out, True)
    def test_toboolFloatTrueNeg(self):
        out = machinestate.tobool(-12.2)
        self.assertEqual(out, True)
    def test_toboolStrOn(self):
        out = machinestate.tobool("on")
        self.assertEqual(out, True)
        out = machinestate.tobool("On")
        self.assertEqual(out, True)
        out = machinestate.tobool("ON")
        self.assertEqual(out, True)
    def test_toboolStrOff(self):
        out = machinestate.tobool("off")
        self.assertEqual(out, False)
        out = machinestate.tobool("Off")
        self.assertEqual(out, False)
        out = machinestate.tobool("OFf")
        self.assertEqual(out, False)
        out = machinestate.tobool("OFF")
        self.assertEqual(out, False)
    def test_toboolStr0(self):
        out = machinestate.tobool("0")
        self.assertEqual(out, False)
    def test_toboolStr1(self):
        out = machinestate.tobool("1")
        self.assertEqual(out, True)
    def test_toboolStr2(self):
        out = machinestate.tobool("2")
        self.assertEqual(out, True)
    def test_toboolStrTrue(self):
        out = machinestate.tobool("true")
        self.assertEqual(out, True)
        out = machinestate.tobool("True")
        self.assertEqual(out, True)
        out = machinestate.tobool("TRue")
        self.assertEqual(out, True)
        out = machinestate.tobool("TRUe")
        self.assertEqual(out, True)
        out = machinestate.tobool("TRUE")
        self.assertEqual(out, True)
    def test_toboolStrFalse(self):
        out = machinestate.tobool("false")
        self.assertEqual(out, False)
        out = machinestate.tobool("False")
        self.assertEqual(out, False)
        out = machinestate.tobool("FAlse")
        self.assertEqual(out, False)
        out = machinestate.tobool("FALse")
        self.assertEqual(out, False)
        out = machinestate.tobool("FALSe")
        self.assertEqual(out, False)
        out = machinestate.tobool("FALSE")
        self.assertEqual(out, False)
    def test_toboolInvalid(self):
        out = machinestate.tobool("abc")
        self.assertEqual(out, False)
        out = machinestate.tobool("-1")
        self.assertEqual(out, False)
        out = machinestate.tobool("offf")
        self.assertEqual(out, False)
        out = machinestate.tobool("o")
        self.assertEqual(out, False)
