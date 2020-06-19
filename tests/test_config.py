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
import json
import machinestate
from locale import getpreferredencoding

ENCODING = getpreferredencoding()

class TestCliParser(unittest.TestCase):
    def setUp(self):
        self.cmd = tempfile.NamedTemporaryFile(mode='w+b', delete=True)
        self.cmd.write(b"#!/bin/bash\n\necho Hello")
        self.cmd.flush()
        os.chmod(self.cmd.name, stat.S_IXUSR)
        self.readable = tempfile.NamedTemporaryFile(mode='rb', delete=True)

        pass
    def tearDown(self):
        self.cmd.close()
        self.readable.close()
        pass
    def test_emptyCli(self):
        cli = []
        conf = machinestate.read_cli(cli)
        self.assertEqual(conf["extended"], False)
        self.assertEqual(conf["sort"], False)
        self.assertEqual(conf["anonymous"], False)
        self.assertEqual(conf["config"], False)
        self.assertEqual(conf["configfile"], None)
        self.assertEqual(conf["json"], None)
        self.assertEqual(conf["output"], None)
        self.assertEqual(conf["executable"], None)
        self.assertEqual(conf["indent"], 4)
    def test_extended_short(self):
        cli = ["-e"]
        conf = machinestate.read_cli(cli)
        self.assertEqual(conf["extended"], True)
    def test_extended_long(self):
        cli = ["--extended"]
        conf = machinestate.read_cli(cli)
        self.assertEqual(conf["extended"], True)
    def test_sort_short(self):
        cli = ["-s"]
        conf = machinestate.read_cli(cli)
        self.assertEqual(conf["sort"], True)
    def test_sort_long(self):
        cli = ["--sort"]
        conf = machinestate.read_cli(cli)
        self.assertEqual(conf["sort"], True)
    def test_anonymous_short(self):
        cli = ["-a"]
        conf = machinestate.read_cli(cli)
        self.assertEqual(conf["anonymous"], True)
    def test_anonymous_long(self):
        cli = ["--anonymous"]
        conf = machinestate.read_cli(cli)
        self.assertEqual(conf["anonymous"], True)
    def test_configfile_long(self):
        cli = ["--configfile", self.readable.name]
        conf = machinestate.read_cli(cli)
        self.assertEqual(conf["configfile"], self.readable.name)
    def test_configfile_not_exist(self):
        fname = self.readable.name+"bla"
        cli = ["--configfile", fname]
        self.assertRaises(ValueError, machinestate.read_cli, cli)
    def test_configfile_not_readable(self):
        fname = self.cmd.name
        cli = ["--configfile", fname]
        self.assertRaises(ValueError, machinestate.read_cli, cli)
    def test_output_short(self):
        fname = "/tmp/machinestate.json"
        cli = ["-o", fname]
        conf = machinestate.read_cli(cli)
        self.assertEqual(conf["output"], fname)
    def test_output_long(self):
        fname = "/tmp/machinestate.json"
        cli = ["--output", fname]
        conf = machinestate.read_cli(cli)
        self.assertEqual(conf["output"], fname)
    def test_jsoncmp_short(self):
        fname = self.readable.name
        cli = ["-j", fname]
        conf = machinestate.read_cli(cli)
        self.assertEqual(conf["json"], fname)
    def test_jsoncmp_long(self):
        fname = self.readable.name
        cli = ["--json", fname]
        conf = machinestate.read_cli(cli)
        self.assertEqual(conf["json"], fname)
    def test_jsoncmp_not_exist(self):
        fname = self.readable.name+"bla"
        cli = ["--json", fname]
        self.assertRaises(ValueError, machinestate.read_cli, cli)
    def test_jsoncmp_not_readable(self):
        fname = self.cmd.name
        cli = ["--json", fname]
        self.assertRaises(ValueError, machinestate.read_cli, cli)
    def test_executable(self):
        fname = self.cmd.name
        cli = [fname]
        conf = machinestate.read_cli(cli)
        self.assertEqual(conf["executable"], fname)
    def test_executable_not_exist(self):
        fname = self.cmd.name+"bla"
        cli = [fname]
        self.assertRaises(ValueError, machinestate.read_cli, cli)
    def test_executable_not_executable(self):
        fname = self.readable.name
        cli = [fname]
        self.assertRaises(ValueError, machinestate.read_cli, cli)

#class TestConfigFile(unittest.TestCase):
#    def setUp(self):
#        self.cfgfile = tempfile.NamedTemporaryFile(mode='w+b', delete=True)
#        self.configdict = {   "dmifile" : machinestate.DMIDECODE_FILE,
#                              "likwid_enable" : machinestate.DO_LIKWID,
#                              "likwid_path" : machinestate.LIKWID_PATH,
#                              "modulecmd" : machinestate.MODULECMD_PATH,
#                              "vecmd_path" : machinestate.VEOS_BASE,
#                              "debug" : machinestate.DEBUG_OUTPUT,
#                             }
#        self.cfgfile.write(bytes(json.dumps(self.configdict), encoding=ENCODING))
#        self.cfgfile.flush()

#        self.invalid = tempfile.NamedTemporaryFile(mode='w+b', delete=True)
#        self.invalid.write(bytes("blabla", encoding=ENCODING))
#        self.invalid.flush()

#        self.readable = tempfile.NamedTemporaryFile(mode='rb', delete=True)

#        pass
#    def tearDown(self):
#        self.cfgfile.close()
#        self.readable.close()
#        self.invalid.close()
#        pass
#    def test_validConfig(self):
#        cdict = machinestate.read_config({"configfile" : self.cfgfile.name,
#                                          "extended" : False,
#                                          "anonymous" : False,
#                                          "executable": None})
#        self.assertEqual(cdict, self.configdict)
#    def test_invalidConfig(self):
#        self.assertRaises(ValueError, machinestate.read_config, {"configfile" : self.cfgfile.name})
#    def test_emptyConfig(self):
#        cdict = machinestate.read_config()
#        self.assertNotEqual(cdict, self.configdict)
