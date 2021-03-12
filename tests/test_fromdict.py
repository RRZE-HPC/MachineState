#!/usr/bin/env python3
"""
Tests for from_dict() function
"""

import unittest
import machinestate
from tempfile import NamedTemporaryFile
from locale import getpreferredencoding

ENCODING = getpreferredencoding()

class TestFromDict(unittest.TestCase):
    def setUp(self):
        self.ms = machinestate.MachineState()
        self.ms.generate()
        self.ms.update()
        data = self.ms.get()
        if data["OperatingSystemInfo"]["Type"] == "Linux":
            self.ci = machinestate.CpuInfo()
            self.ci.generate()
            self.ci.update()
        else:
            self.ci = machinestate.CpuInfoMacOS()
            self.ci.generate()
            self.ci.update()
    def test_fromdictCompareClass(self):
        mscopy = machinestate.MachineState.from_dict(self.ms.get(meta=True))
        self.assertEqual(self.ms, mscopy)
    def test_fromdictCompareDict(self):
        mscopy = machinestate.MachineState.from_dict(self.ms.get(meta=True))
        self.assertEqual(self.ms, mscopy.get())
    def test_fromdictCompareDictMeta(self):
        mscopy = machinestate.MachineState.from_dict(self.ms.get(meta=True))
        self.assertEqual(self.ms, mscopy.get(meta=True))
    def test_fromdictCompareJSON(self):
        mscopy = machinestate.MachineState.from_dict(self.ms.get(meta=True))
        self.assertEqual(self.ms, mscopy.get_json())
    def test_fromdictCompareJSONFile(self):
        mscopy = machinestate.MachineState.from_dict(self.ms.get(meta=True))
        jsonfp = NamedTemporaryFile(mode="wb", delete=True)
        jsonfp.write(bytes(mscopy.get_json(), ENCODING))
        jsonfp.seek(0)
        self.assertEqual(self.ms, jsonfp.name)
        jsonfp.close()
    def test_fromdictCompareDictDict(self):
        mscopy = machinestate.MachineState.from_dict(self.ms.get(meta=True))
        self.assertEqual(self.ms.get(), mscopy.get())
    def test_fromdictCompareDictMetaDictMeta(self):
        mscopy = machinestate.MachineState.from_dict(self.ms.get(meta=True))
        self.assertEqual(self.ms.get(meta=True), mscopy.get(meta=True))
    def test_fromdictCompareDictMetaDict(self):
        mscopy = machinestate.MachineState.from_dict(self.ms.get(meta=True))
        self.assertNotEqual(self.ms.get(), mscopy.get(meta=True))
    def test_fromdictLoadFaulty(self):
        cicopy = {}
        for k,v in self.ci.get(meta=True).items():
            cicopy[k] = v
        cicopy["Model"] = cicopy["Model"] - 1
        faulty = machinestate.CpuInfo.from_dict(cicopy)
        self.assertNotEqual(self.ci.get(), faulty.get())
    def test_fromdictNoMeta(self):
        #mscopy = machinestate.MachineState.from_dict(self.ms.get())
        self.assertRaises(ValueError, machinestate.MachineState.from_dict, self.ms.get())
    def test_fromdictClass(self):
        mscopy = machinestate.MachineState.from_dict(self.ms)
        self.assertEqual(self.ms, mscopy.get(meta=True))
    def test_fromdictEmptyDict(self):
        self.assertRaises(ValueError, machinestate.MachineState.from_dict, {})
    def test_fromdictFaultyNoMetaDict(self):
        faulty = { "1" : 3, "2" : 24, "5" : 45}
        self.assertRaises(ValueError, machinestate.MachineState.from_dict, faulty)
    def test_fromdictFaultyMetaDict(self):
        faulty = { "1" : 3, "2" : 24, "5" : 45, "_meta" : "foobar"}
        self.assertRaises(ValueError, machinestate.MachineState.from_dict, faulty)
    def test_fromdictFaultyMetaMachineStateDict(self):
        faulty = { "1" : 3, "2" : 24, "5" : 45, "_meta" : "MachineState()"}
        mscopy = machinestate.MachineState.from_dict(faulty)
        self.assertEqual(mscopy.get(), {})
    def test_fromdictFaultyMetaCpuInfoDict(self):
        self.assertRaises(ValueError, machinestate.MachineState.from_dict, self.ci.get(meta=True))
