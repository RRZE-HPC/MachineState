#!/usr/bin/env python3

# =======================================================================================
#
#      Filename:  machinestate.py
#
#      Description:  Collect system settings
#
#      Author:   Thomas Gruber, thomas.roehl@googlemail.com
#      Project:  Artifact-description
#
#      Copyright (C) 2020 RRZE, University Erlangen-Nuremberg
#
#      This program is free software: you can redistribute it and/or modify it under
#      the terms of the GNU General Public License as published by the Free Software
#      Foundation, either version 3 of the License, or (at your option) any later
#      version.
#
#      This program is distributed in the hope that it will be useful, but WITHOUT ANY
#      WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
#      PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
#      You should have received a copy of the GNU General Public License along with
#      this program.  If not, see <http://www.gnu.org/licenses/>.
#
# =======================================================================================

# TODO: Should sizes like "32654660 kB" be transformed to number in bytes?

################################################################################
# Imports
################################################################################
import sys
import re
import json
import platform
from subprocess import check_output, DEVNULL
from glob import glob
import os
from os.path import join as pjoin
from os.path import exists as pexists
from os.path import getsize as psize
from locale import getpreferredencoding
from datetime import timedelta, datetime
import hashlib
import argparse
from copy import deepcopy
#from unittest.TestCase import assertAlmostEqual
import unittest

################################################################################
# Configuration
################################################################################
# Some classes call LIKWID to get the required information. With the DO_LIKWID
# switch, this can be de/activated.
DO_LIKWID = True
# The LIKWID_PATH is currently unused.
LIKWID_PATH = None
# The DmiDecodeFile class reads the whole content of this file and includes it
# as string to the JSON dict.
DMIDECODE_FILE = "/etc/dmidecode.txt"
# Currently unused option. The BiosInfo class uses information from sysfs
BIOS_XML_FILE = ""
# The ModulesInfo class requires this path to read the loaded modules. It will
# call 'tclsh MODULECMD_TCL_PATH' if tclsh and MODULECMD_TCL_PATH exist.
MODULECMD_TCL_PATH = "/apps/modules/modulecmd.tcl"
# The NecTsubasaInfo class requires this path to call the vecmd command
VEOS_BASE = "/opt/nec/ve/bin"

################################################################################
# Version information
################################################################################
MACHINESTATE_VERSION = "0.1"

################################################################################
# Constants
################################################################################
ENCODING = getpreferredencoding()


################################################################################
# Helper functions
################################################################################

# TODO switch to shutil.which
from shutil import which
def get_abspath(cmd):
    '''Returns absoulte path of executable using the which command.'''
    data = ""
    try:
        rawdata = check_output("which {}; exit 0".format(cmd), stderr=DEVNULL, shell=True)
        data = rawdata.decode(ENCODING).strip()
    except:
        raise Exception("Cannot expand filepath of '{}'".format(cmd))
    return data

################################################################################
# Parser Functions used in multiple places. If a parser function is used only
# in a single class, it is defined as static method in the class
################################################################################


def tostrlist(value):
    '''Returns string split at \s and , in list of strings. Strings might not be unique in list.

    :param value: string with sub-strings

    :returns: Expanded list
    :rtype: [str]
    '''
    if value:
        return re.split(r"[,\s]", value)

def tointlist(value):
    '''Returns string split at \s and , in list of integers. Supports lists like 0,1-4,7.

    :param value: string with lists like 5,6,8 or 1-4 or 0,1-4,7
    :raises: :class:`ValueError`: Element of the list cannot be casted to type int

    :returns: Expanded list
    :rtype: [int]
    '''
    outlist = []
    try:
        for part in [x for x in re.split(r"[,\s]", value) if x.strip()]:
            if '-' in part:
                start, end = part.split("-")
                outlist += [int(i) for i in range(int(start), int(end)+1)]
            else:
                outlist += [int(part)]
    except Exception:
        raise ValueError("Unable to cast value '{}' to intlist".format(value))
    return outlist

def totitle(value):
    '''Returns titleized split (string.title()) with _ and whitespaces removed.'''
    return value.title().replace("_", "").replace(" ", "")

def fopen(filename):
    if filename and pexists(filename) and os.path.isfile(filename):
        try:
            filefp = open(filename, "rb")
        except PermissionError:
            return None
        except BaseException as e:
            raise e
        return filefp

################################################################################
# Processing functions for single entries in class attributes files and commands
# TODO: Write function that processes all entries for a single file/cmd to
#       reduce runtime. Some commands are called multiple times to get different
#       information
################################################################################
def match_data(data, regex_str):
    out = data
    regex = re.compile(regex_str)
    nlregex = re.compile(r"\n")
    for line in nlregex.split(data):
        mat = regex.match(line)
        if mat:
            out = mat.group(1)
            break
        else:
            mat = regex.search(line)
            if mat:
                out = mat.group(1)
                break
    return out

def process_file(args):
    data = None
    fname, *matchconvert = args
    filefp = fopen(fname)
    if filefp:
        data = filefp.read().decode(ENCODING).strip()
        if matchconvert:
            fmatch, *convert = matchconvert
            if fmatch:
                data = match_data(data, fmatch)
            if convert:
                fconvert, = convert
                if fconvert:
                    try:
                        data = fconvert(data)
                    except:
                        pass
    return data

def process_cmd(args):
    data = None
    cmd, *optsmatchconvert = args
    if cmd:
        abspath = which(cmd)
        #which_cmd = "which {}; exit 0;".format(cmd)
        #data = check_output(which_cmd, stderr=DEVNULL, shell=True).decode(ENCODING).strip()
        if abspath and len(abspath) > 0:
            if optsmatchconvert:
                cmd_opts, *matchconvert = optsmatchconvert
                exe = "{} {}; exit 0;".format(cmd, cmd_opts)
                data = check_output(exe, stderr=DEVNULL, shell=True).decode(ENCODING).strip()
                if data and len(data) >= 0:
                    cmatch, *convert = matchconvert
                    if cmatch:
                        data = match_data(data, cmatch)
                    if convert:
                        cconvert, = convert
                        if cconvert:
                            try:
                                data = cconvert(data)
                            except:
                                pass
                else:
                    if len(matchconvert) == 2:
                        cmatch, cconvert = matchconvert
                        if cconvert:
                            try:
                                data = cconvert(None)
                            except:
                                pass

    return data

def get_config_file(args):
    outdict = {}
    fname, *matchconvert = args
    if fname:
        outdict["Filename"] = str(fname)
        if matchconvert:
            fmatch, *convert = matchconvert
            if fmatch:
                outdict["Regex"] = str(fmatch)
                if convert:
                    fconvert, = convert
                    if fconvert:
                        outdict["Parser"] = str(fconvert)
    return outdict

def get_config_cmd(args):
    outdict = {}
    cmd, *optsmatchconvert = args
    if cmd:
        outdict["Command"] = str(cmd)
        if optsmatchconvert:
            cmd_opts, *matchconvert = optsmatchconvert
            if cmd_opts:
                outdict["CommandOpts"] = str(cmd_opts)
                if matchconvert:
                    cmatch, *convert = matchconvert
                    if cmatch:
                        outdict["Regex"] = str(cmatch)
                        if convert:
                            cconvert, = convert
                            if cconvert:
                                outdict["Parser"] = str(cconvert)
    return outdict

def assert_relativly_equal(actual, desired, rel_diff=0.0):
    """
    Test for relative difference between actual and desired
    passes if abs(actual-desired)/abs(desired) % 1.0 < rel_diff
    """
    if actual == desired:
        # Catching NaN, inf and 0
        return
    if not abs(actual - desired) / abs(desired) % 1.0 <= rel_diff:
        raise AssertionError("relative difference was not met with {}. Expected {!r} with rel. "
                             "difference of {!r}.".format(actual, desired, rel_diff))

################################################################################
# Base Classes
################################################################################


class InfoGroup:
    def __init__(self, name=None, extended=False, anon=False):
        # Holds subclasses
        self._instances = []
        # Holds the data of this class instance
        self._data = {}
        # Space for file reads
        # Key -> (filename, regex_with_one_group, convert_function)
        # If regex_with_one_group is None, the whole content of filename is passed to convert_function
        # If convert_function is None, the output is saved as string
        self.files = {}
        # Space for commands for execution
        # Key -> (executable, exec_arguments, regex_with_one_group, convert_function)
        # If regex_with_one_group is None, the whole content of filename is passed to convert_function
        # If convert_function is None, the output is saved as string
        self.commands = {}
        # Space for constants
        # Key -> Value
        self.constants = {}
        # Keys in the group that are required to check equality
        self.required4equal = []
        self.name = name
        self.extended = extended
        self.anon = anon

    def generate(self):
        '''Generate subclasses, defined by derived classes'''
        pass

    def update(self):
        outdict = {}
        if len(self.files) > 0:
            for key in self.files:
                val = self.files.get(key, None)
                if val:
                    fdata = process_file(val)
                    outdict[key] = fdata
        if len(self.commands) > 0:
            for key in self.commands:
                val = self.commands.get(key, None)
                if val:
                    cdata = process_cmd(val)
                    outdict[key] = cdata
        if len(self.constants) > 0:
            for key in self.constants:
                outdict[key] = self.constants[key]
        for inst in self._instances:
            inst.update()
        self._data.update(outdict)
    def get(self):
        outdict = {}
        for inst in self._instances:
            clsout = inst.get()
            outdict.update({inst.name : clsout})
        outdict.update(self._data)
        return outdict
    def get_json(self, sort=False, intend=4):
        outdict = self.get()
        return json.dumps(outdict, sort_keys=sort, indent=intend)
    def get_config(self):
        outdict = {}
        #outdict["Name"] = self.name
        selfdict = {}
        selfdict["Type"] = str(self.__class__.__name__)
        selfdict["ClassType"] = "InfoGroup"
        if len(self.files) > 0:
            outfiles = {}
            for key in self.files:
                val = self.files.get(key, None)
                outfiles[key] = get_config_file(val)
            outdict.update({"Files" : outfiles})
        if len(self.commands) > 0:
            outcmds = {}
            for key in self.commands:
                val = self.commands.get(key, None)
                outcmds[key] = get_config_cmd(val)
            outdict.update({"Commands" : outcmds})

        if len(self.constants) > 0:
            outconst = {}
            for key in self.constants:
                outconst[key] = self.constants[key]
            outdict.update({"Constants" : outconst})
        outdict["Config"] = selfdict
        for inst in self._instances:
            outdict.update({inst.name : inst.get_config()})
        return outdict
    def __eq__(self, other):
        selfdict = self.get()
        tcase = unittest.TestCase()
        if isinstance(other, str):
            if pexists(other):
                try:
                    jsonfp = open(cliargs["json"])
                except BaseException as e:
                    print(e)
                    sys.exit(1)
                else:
                    with jsonfp:
                        other = json.load(jsonfp)
            else:
                other = json.loads(other)

        for key in self.required4equal:
            if key in other:
                ##
                selfval = selfdict[key]
                otherval = other[key]
                if isinstance(selfval, str) and re.match(r"^([\d\.]+).*", str(selfval)):
                    smatch = re.match(r"^([\d\.]+).*", selfval).group(1)
                    omatch = re.match(r"^([\d\.]+).*", otherval).group(1)
                    try:
                        selfval = float(smatch)
                        otherval = float(omatch)
                    except:
                        pass

                if isinstance(selfval, int) or isinstance(selfval, float):
                    if selfval != otherval:
                        try:
                            tcase.assertAlmostEqual(first=selfval, second=otherval, delta=selfval*0.2)
                        except BaseException as e:
                            print("Equality check failed for key {}: {}".format(key, e))
                            print("assertAlmostEqual('{}', '{}', delta={})".format(selfval, otherval, selfval*0.2))
                            return False
                elif selfval != otherval:
                    print("Equality check failed for key {}".format(key))
                    print("__eq__({}, '{}', '{}')".format(type(selfval), selfval, otherval))
                    return False
        for inst in self._instances:
            if inst.name in other:
                #print("__eq__('{}', '{}')".format(inst.name, other[inst.name]))
                instout = (inst.__eq__(other[inst.name]))
                if instout == False:
                    return False
        return True

class PathMatchInfoGroup(InfoGroup):
    '''Class for matching files in a folder and create subclasses for each path'''
    def __init__(self, name=None,
                       extended=False,
                       anon=False,
                       basepath=None,
                       match=None,
                       subclass=None,
                       subargs={}):
        super(PathMatchInfoGroup, self).__init__(extended=extended, name=name, anon=anon)
        self.basepath = basepath
        self.match = match
        self.subclass = subclass
        self.subargs = subargs
    def generate(self):
        glist = []
        if self.basepath and self.match and self.subclass:
            mat = re.compile(self.match)
            base = self.basepath
            try:
                glist += sorted([int(mat.match(f).group(1)) for f in glob(base) if mat.match(f)])
            except ValueError:
                glist += sorted([mat.match(f).group(1) for f in glob(base) if mat.match(f)])
            for item in glist:
                cls = self.subclass(item, extended=self.extended, anon=self.anon, **self.subargs)
                cls.generate()
                self._instances.append(cls)
    def get_config(self):
        outdict = super(PathMatchInfoGroup, self).get_config()
        selfdict = {}
        selfdict["Type"] = str(self.__class__.__name__)
        selfdict["ClassType"] = "PathMatchInfoGroup"
        if self.basepath:
            selfdict["SearchPath"] = str(self.basepath)
        if self.match:
            selfdict["Regex"] = str(self.match)
        if self.subclass:
            selfdict["SubClass"] = str(self.subclass)
        if self.subargs:
            selfdict["SubArgs"] = str(self.subargs)
        outdict["Config"] = selfdict
        for inst in self._instances:
            outdict.update({inst.name : inst.get_config()})
        return outdict


class ListInfoGroup(InfoGroup):
    '''Class for creating subclasses based on a list given by the user. All subclasses have the same
    class type.
    '''
    def __init__(self, name=None,
                       extended=False,
                       anon=False,
                       userlist=None,
                       subclass=None,
                       subargs={}):
        super(ListInfoGroup, self).__init__(extended=extended, name=name, anon=anon)
        self.userlist = userlist or []
        self.subclass = subclass
        self.subargs = subargs
    def generate(self):
        if self.userlist and self.subclass:
            for item in self.userlist:
                cls = self.subclass(item, extended=self.extended, anon=self.anon, **self.subargs)
                cls.generate()
                self._instances.append(cls)
    def get_config(self):
        outdict = super(ListInfoGroup, self).get_config()
        selfdict = {}
        selfdict["Type"] = str(self.__class__.__name__)
        selfdict["ClassType"] = "ListInfoGroup"
        if self.subclass:
            selfdict["SubClass"] = str(self.subclass)
        if self.subargs:
            selfdict["SubArgs"] = str(self.subargs)
        if self.userlist:
            selfdict["List"] = str(self.userlist)
        for inst in self._instances:
            outdict.update({inst.name : inst.get_config()})
        outdict["Config"] = selfdict
        return outdict

class MultiClassInfoGroup(InfoGroup):
    '''Class for creating subclasses based on a list of class types given by the user.
    '''
    def __init__(self, name=None,
                       extended=False,
                       anon=False,
                       classlist=None,
                       classargs={}):
        super(MultiClassInfoGroup, self).__init__(extended=extended, name=name, anon=anon)
        self.classlist = classlist
        self.classargs = classargs

    def generate(self):
        for cltype, clargs in zip(self.classlist, self.classargs):
            try:
                cls = cltype(extended=self.extended, anon=self.anon, **clargs)
            except BaseException as e:
                print(cltype, clargs)
                print(e)
            cls.generate()
            self._instances.append(cls)
    def get_config(self):
        outdict = super(MultiClassInfoGroup, self).get_config()
        outdict["Type"] = str(self.__class__.__name__)
        outdict["ClassType"] = "MultiClassInfoGroup"
        for cls, args in zip(self.classlist, self.classargs):
            outdict[str(cls)] = str(args)
        for inst in self._instances:
            outdict.update({inst.name : inst.get_config()})
        return outdict


class MachineState(MultiClassInfoGroup):
    def __init__(self, extended=False, executable=None, anon=False):
        super(MachineState, self).__init__(extended=extended, anon=anon)
        self.constants["MACHINESTATE_VERSION"] = MACHINESTATE_VERSION
        self.classlist = [
            HostInfo,
            CpuInfo,
            OSInfo,
            KernelInfo,
            Uptime,
            CpuTopology,
            NumaBalance,
            LoadAvg,
            MemInfo,
            CgroupInfo,
            Writeback,
            CpuFrequency,
            NumaInfo,
            CacheTopology,
            TransparentHugepages,
            PowercapInfo,
            Hugepages,
            CompilerInfo,
            MpiInfo,
            ShellEnvironment,
            PythonInfo,
            ClocksourceInfo,
            CoretempInfo,
            BiosInfo,
            ThermalZoneInfo,
            VulnerabilitiesInfo,
            UsersInfo,
            CpuAffinity,
            ModulesInfo,
            NvidiaSmiInfo,
        ]
        if which("nvidia-smi"):
            self.classlist.append(NvidiaSmiInfo)
        self.classargs = [{} for x in self.classlist]
        if pexists(VEOS_BASE):
            self.classlist.append(NecTsubasaInfo)
            self.classargs.append({"ve_base" : VEOS_BASE})
        if pexists(DMIDECODE_FILE):
            self.classlist.append(DmiDecodeFile)
            self.classargs.append({"dmifile" : DMIDECODE_FILE})
        if executable:
            self.classlist.append(ExecutableInfo)
            self.classargs.append({"executable" : executable})
        if DO_LIKWID:
            likwid_base = LIKWID_PATH
            if not likwid_base:
                path = which("likwid-topology")
                if path:
                    likwid_base = os.path.dirname(path)
            self.classlist += [PrefetcherInfo, TurboInfo]
            clargs = {"likwid_base" : likwid_base}
            self.classargs.append(clargs)
            self.classargs.append(clargs)
    def get_config(self, sort=False, intend=4):
        outdict = {}
        for inst in self._instances:
            clsout = inst.get_config()
            outdict.update({inst.name : clsout})
        return json.dumps(outdict, sort_keys=sort, indent=intend)

################################################################################
# Configuration Classes
################################################################################

################################################################################
# Infos about operating system
################################################################################
class OSInfo(InfoGroup):
    def __init__(self, extended=False, anon=False):
        super(OSInfo, self).__init__(anon=anon, extended=extended)
        self.name = "OperatingSystemInfo"
        self.files = {"Name" : ("/etc/os-release", "NAME=[\"]*([^\"]+)[\"]*\s*"),
                      "Version" : ("/etc/os-release", "VERSION=[\"]*([^\"]+)[\"]*\s*"),
                     }
        self.required4equal = self.files.keys()
        if extended:
            self.files["URL"] = ("/etc/os-release", "HOME_URL=[\"]*([^\"]+)[\"]*\s*")
            #self.files["Codename"] = ("/etc/os-release", "VERSION_CODENAME=[\"]*([^\"\n]+)[\"]*")

################################################################################
# Infos about NUMA balancing
################################################################################
class NumaBalance(InfoGroup):
    def __init__(self, extended=False, anon=False):
        super(NumaBalance, self).__init__(extended=extended, anon=anon)
        self.name = "NumaBalancing"
        base = "/proc/sys/kernel"
        regex = r"(\d+)"
        self.files = {"Enabled" : (pjoin(base, "numa_balancing"), regex, bool)}
        if extended:
            names = ["ScanDelayMs", "ScanPeriodMaxMs", "ScanPeriodMinMs", "ScanSizeMb"]
            files = ["numa_balancing_scan_delay_ms", "numa_balancing_scan_period_max_ms",
                     "numa_balancing_scan_period_min_ms", "numa_balancing_scan_size_mb"]
            for key, fname in zip(names, files):
                self.files[key] = (pjoin(base, fname), regex, int)
        self.required4equal = self.files.keys()

################################################################################
# Infos about the host
################################################################################
class HostInfo(InfoGroup):
    def __init__(self, extended=False, anon=False):
        super(HostInfo, self).__init__(anon=anon, extended=extended)
        self.name = "HostInfo"
        if not anon:
            self.commands = {"Hostname" : ("hostname", "-s", r"(.+)")}
            if extended:
                self.commands.update({"Domainname" : ("hostname", "-d", r"(.+)")})
                self.commands.update({"FQDN" : ("hostname", "-f", r"(.+)")})

################################################################################
# Infos about the CPU
################################################################################
class CpuInfo(InfoGroup):
    def __init__(self, extended=False, anon=False):
        super(CpuInfo, self).__init__(name="CpuInfo", extended=extended, anon=anon)
        if platform.machine() in ["x86_64", "i386"]:
            self.files = {"Vendor" : ("/proc/cpuinfo", r"vendor_id\s+:\s(.*)"),
                          "Name" : ("/proc/cpuinfo", r"model name\s+:\s(.+)"),
                          "Family" : ("/proc/cpuinfo", r"cpu family\s+:\s(.+)", int),
                          "Model" : ("/proc/cpuinfo", r"model\s+:\s(.+)", int),
                          "Stepping" : ("/proc/cpuinfo", r"stepping\s+:\s(.+)", int),
                         }
        elif platform.machine() in ["aarch64"]:
            self.files = {"Vendor" : ("/proc/cpuinfo", r"CPU implementer\s+:\s([x0-9a-fA-F]+)"),
                          #"Name" : ("/proc/cpuinfo", r"model name\s+:\s([]-)\n"),
                          "Family" : ("/proc/cpuinfo", r"CPU architecture\s*:\s([x0-9a-fA-F]+)", int),
                          "Model" : ("/proc/cpuinfo", r"CPU variant\s+:\s([x0-9a-fA-F]+)", int),
                          "Stepping" : ("/proc/cpuinfo", r"CPU revision\s+:\s([x0-9a-fA-F]+)", int),
                          "Variant" : ("/proc/cpuinfo", r"CPU part\s+:\s([x0-9a-fA-F]+)", int),
                         }
        elif platform.machine() in ["ppc64le", "ppc64"]:
            self.files = {"Vendor" : ("/proc/cpuinfo", r"vendor_id\s+:\s(.*)"),
                          "Name" : ("/proc/cpuinfo", r"model name\s+:\s(.+)"),
                          "Family" : ("/proc/cpuinfo", r"cpu family\s+:\s(.+)", int),
                          "Model" : ("/proc/cpuinfo", r"model\s+:\s(.+)", int),
                          "Stepping" : ("/proc/cpuinfo", r"stepping\s+:\s(.+)", int),
                         }
        self.required4equal = ["Vendor", "Family", "Model", "Stepping"]
        if pexists("/sys/devices/system/cpu/smt/active"):
            self.files["SMT"] = ("/sys/devices/system/cpu/smt/active", r"(\d+)", bool)
            self.required4equal.append("SMT")
        if extended:
            if platform.machine() in ["x86_64", "i386"]:
                self.files["Flags"] = ("/proc/cpuinfo", r"flags\s+:\s(.+)", tostrlist)
                self.files["Microcode"] = ("/proc/cpuinfo", r"microcode\s+:\s(.+)")
                self.files["Bugs"] = ("/proc/cpuinfo", r"bugs\s+:\s(.+)", tostrlist)
                self.required4equal.append("Microcode")
            elif platform.machine() in ["aarch64"]:
                self.files["Flags"] = ("/proc/cpuinfo", r"Features\s+:\s(.+)", tostrlist)


################################################################################
# CPU Topology
################################################################################
class CpuTopologyClass(InfoGroup):
    def __init__(self, ident, extended=False, anon=False):
        super(CpuTopologyClass, self).__init__(anon=anon, extended=extended)
        self.name = "Cpu{}".format(ident)
        base = "/sys/devices/system/cpu/cpu{}/topology".format(ident)
        self.files = {"CoreId" : (pjoin(base, "core_id"), r"(\d+)", int),
                      "PackageId" : (pjoin(base, "physical_package_id"), r"(\d+)", int),
                     }
        self.constants = {"HWThread" : ident,
                          "ThreadId" : CpuTopologyClass.getthreadid(ident)
                         }
        self.required4equal = list(self.files.keys()) + list(self.constants.keys())

    @staticmethod
    def getthreadid(hwthread):
        base = "/sys/devices/system/cpu/cpu{}/topology/thread_siblings_list".format(hwthread)
        with open(base, "rb") as outfp:
            tid = 0
            data = outfp.read().decode(ENCODING).strip()
            dlist = data.split(",")
            if len(dlist) > 1:
                tid = dlist.index(str(hwthread))
            else:
                dlist = data.split("-")
                if len(dlist) > 1:
                    trange = range(int(dlist[0]), int(dlist[1])+1)
                    tid = trange.index(hwthread)
            return tid


class CpuTopology(PathMatchInfoGroup):
    def __init__(self, extended=False, anon=False):
        super(CpuTopology, self).__init__(extended=extended, anon=anon)
        self.name = "CpuTopology"
        self.basepath = "/sys/devices/system/cpu/cpu*"
        self.match = r".*/cpu(\d+)$"
        self.subclass = CpuTopologyClass


################################################################################
# CPU Frequency
################################################################################
class CpuFrequencyClass(InfoGroup):
    def __init__(self, ident, extended=False, anon=False):
        super(CpuFrequencyClass, self).__init__(anon=anon, extended=extended)
        self.name = "Cpu{}".format(ident)
        base = "/sys/devices/system/cpu/cpu{}/cpufreq".format(ident)
        if pexists(pjoin(base, "scaling_max_freq")):
            self.files["MaxFreq"] = (pjoin(base, "scaling_max_freq"), r"(\d+)", int)
        if pexists(pjoin(base, "scaling_max_freq")):
            self.files["MinFreq"] = (pjoin(base, "scaling_min_freq"), r"(\d+)", int)
        if pexists(pjoin(base, "scaling_governor")):
            self.files["Governor"] = (pjoin(base, "scaling_governor"), r"(.+)")
        if pexists(pjoin(base, "energy_performance_preference")):
            self.files["EnergyPerfPreference"] = (pjoin(base, "energy_performance_preference"), r"(.+)")
        self.required4equal = self.files.keys()

class CpuFrequency(PathMatchInfoGroup):
    def __init__(self, extended=False, anon=False):
        super(CpuFrequency, self).__init__(extended=extended, anon=anon)
        self.name = "CpuFrequency"
        if pexists("/sys/devices/system/cpu/cpu0/cpufreq"):
            self.basepath = "/sys/devices/system/cpu/cpu*"
            self.match = r".*/cpu(\d+)$"
            self.subclass = CpuFrequencyClass
        if extended:
            base = "/sys/devices/system/cpu/cpu{}/cpufreq".format(0)
            if pexists(pjoin(base, "cpuinfo_transition_latency")):
                self.files["TransitionLatency"] = (pjoin(base, "cpuinfo_transition_latency"), r"(\d+)", int)
            if pexists(pjoin(base, "cpuinfo_max_freq")):
                self.files["MaxAvailFreq"] = (pjoin(base, "cpuinfo_max_freq"), r"(\d+)", int)
            if pexists(pjoin(base, "cpuinfo_min_freq")):
                self.files["MinAvailFreq"] = (pjoin(base, "cpuinfo_min_freq"), r"(\d+)", int)
            if pexists(pjoin(base, "scaling_driver")):
                self.files["Driver"] = (pjoin(base, "scaling_driver"), r"(.*)")
            if pexists(pjoin(base, "scaling_available_frequencies")):
                self.files["AvailFrequencies"] = (pjoin(base, "scaling_available_frequencies"), r"(.*)", tointlist)
            if pexists(pjoin(base, "scaling_available_governors")):
                self.files["AvailGovernors"] = (pjoin(base, "scaling_available_governors"), r"(.*)", tostrlist)
            if pexists(pjoin(base, "energy_performance_available_preferences")):
                self.files["AvailEnergyPerfPreferences"] = (pjoin(base, "energy_performance_available_preferences"), r"(.*)", tostrlist)
        self.required4equal = ["Driver"]

################################################################################
# NUMA Topology
################################################################################
class NumaInfoHugepagesClass(InfoGroup):
    def __init__(self, size, extended=False, anon=False, node=0):
        name = "Hugepages-{}".format(size)
        super(NumaInfoHugepagesClass, self).__init__(name=name, extended=extended, anon=anon)
        base = "/sys/devices/system/node/node{}/hugepages/hugepages-{}".format(node, size)
        self.files = {"Count" : (pjoin(base, "nr_hugepages"), r"(\d+)", int),
                      "Free" : (pjoin(base, "free_hugepages"), r"(\d+)", int),
                     }
        self.required4equal = ["Count"]

class NumaInfoClass(PathMatchInfoGroup):
    def __init__(self, node, anon=False, extended=False):
        super(NumaInfoClass, self).__init__(anon=anon, extended=extended)
        self.name = "NumaNode{}".format(node)
        base = "/sys/devices/system/node/node{}".format(node)
        self.files = {"MemTotal" : (pjoin(base, "meminfo"),
                                    r"Node {} MemTotal:\s+(\d+\s[kKMG][B])".format(node)),
                      "MemFree" : (pjoin(base, "meminfo"),
                                   r"Node {} MemFree:\s+(\d+\s[kKMG][B])".format(node)),
                      "MemUsed" : (pjoin(base, "meminfo"),
                                   r"Node {} MemUsed:\s+(\d+\s[kKMG][B])".format(node)),
                      "Distances" : (pjoin(base, "distance"), r"(.*)", tointlist),
                      "CpuList" : (pjoin(base, "cpulist"), r"(.*)", tointlist),
                     }
        if extended:
            if extended:
                self.files["Writeback"] = (pjoin(base, "meminfo"),
                                           r"Node {} Writeback:\s+(\d+\s[kKMG][B])".format(node))
        self.required4equal = ["MemFree", "CpuList"]
        self.basepath = "/sys/devices/system/node/node{}/hugepages/hugepages-*".format(node)
        self.match = r".*/hugepages-(\d+[kKMG][B])$"
        self.subclass = NumaInfoHugepagesClass
        self.subargs = {"node" : node}

class NumaInfo(PathMatchInfoGroup):
    def __init__(self, extended=False, anon=False):
        super(NumaInfo, self).__init__(name="NumaInfo", extended=extended, anon=anon)
        self.basepath = "/sys/devices/system/node/node*"
        self.match = r".*/node(\d+)$"
        self.subclass = NumaInfoClass

################################################################################
# Cache Topology
################################################################################
class CacheTopologyClass(InfoGroup):
    def __init__(self, ident, extended=False, anon=False):
        super(CacheTopologyClass, self).__init__(extended=extended, anon=anon)
        self.name = "L{}".format(ident)
        base = "/sys/devices/system/cpu/cpu0/cache/index{}".format(ident)
        self.files = {"Size" : (pjoin(base, "size"), r"(\d+)", int),
                      "Level" : (pjoin(base, "level"), r"(\d+)", int),
                      "Type" : (pjoin(base, "type"), r"(.+)"),
                     }
        self.constants = {"CpuList" : CacheTopologyClass.getcpulist(ident)}
        if extended:
            self.files["Sets"] = (pjoin(base, "number_of_sets"), r"(\d+)", int)
            self.files["Associativity"] = (pjoin(base, "ways_of_associativity"), r"(\d+)", int)
            self.files["CoherencyLineSize"] = (pjoin(base, "coherency_line_size"), r"(\d+)", int)
            phys_line_part = pjoin(base, "physical_line_partition")
            if pexists(phys_line_part):
                self.files["PhysicalLineSize"] = (phys_line_part, r"(\d+)", int)
            alloc_policy = pjoin(base, "allocation_policy")
            if pexists(alloc_policy):
                self.files["AllocPolicy"] = (alloc_policy, r"(.+)")
            write_policy = pjoin(base, "write_policy")
            if pexists(write_policy):
                self.files["WritePolicy"] = (write_policy, r"(.+)", int)
        self.required4equal = self.files.keys()
        #"CpuList" : (pjoin(self.basepath, "shared_cpu_list"), r"(.+)", tointlist),
    @staticmethod
    def getcpulist(arg):
        base = "/sys/devices/system/cpu/cpu*"
        cmat = re.compile(r".*/cpu(\d+)$")
        cpus = sorted([int(cmat.match(x).group(1)) for x in glob(base) if cmat.match(x)])
        cpulist = []
        slist = []
        cpath = "cache/index{}/shared_cpu_list".format(arg)
        for cpu in cpus:
            path = pjoin("/sys/devices/system/cpu/cpu{}".format(cpu), cpath)
            with open(path, "rb") as filefp:
                data = filefp.read().decode(ENCODING).strip()
                clist = tointlist(data)
                if str(clist) not in slist:
                    cpulist.append(clist)
                    slist.append(str(clist))
        return cpulist

    def update(self):
        super(CacheTopologyClass, self).update()
        if "Level" in self._data:
            self.name = "L{}".format(self._data["Level"])
            if "Type" in self._data:
                ctype = self._data["Type"]
                if ctype == "Data":
                    self.name += "D"
                elif ctype == "Instruction":
                    self.name += "I"

class CacheTopology(PathMatchInfoGroup):
    def __init__(self, extended=False, anon=False):
        super(CacheTopology, self).__init__(anon=anon, extended=extended)
        self.name = "CacheTopology"
        self.basepath = "/sys/devices/system/cpu/cpu0/cache/index*"
        self.match = r".*/index(\d+)$"
        self.subclass = CacheTopologyClass

################################################################################
# Infos about the uptime of the system
################################################################################
class Uptime(InfoGroup):
    def __init__(self, extended=False, anon=False):
        super(Uptime, self).__init__(name="Uptime", extended=extended, anon=anon)
        self.files = {"Uptime" : ("/proc/uptime", r"([\d\.]+)\s+[\d\.]+", float),
                      "UptimeReadable" : ("/proc/uptime", r"([\d\.]+)\s+[\d\.]+", Uptime.totimedelta)
                     }
        self.required4equal = ["Uptime"]
        if extended:
            self.files.update({"CpusIdle" : ("/proc/uptime", r"[\d\.]+\s+([\d\.]+)", float)})
    @staticmethod
    def totimedelta(value):
        ivalue = int(float(value))
        msec = int((float(value) - ivalue)*1000)
        minutes = int(ivalue/60)
        hours = int(minutes/60)
        days = int(hours/24)
        weeks = int(days/7)
        seconds = ivalue % 60
        date = datetime.now() - timedelta(weeks=weeks,
                                          days=days,
                                          hours=hours,
                                          minutes=minutes,
                                          seconds=seconds,
                                          milliseconds=msec)
        return date.ctime()

################################################################################
# Infos about the load of the system
################################################################################
class LoadAvg(InfoGroup):
    def __init__(self, extended=False, anon=False):
        super(LoadAvg, self).__init__(name="LoadAvg", extended=extended, anon=anon)
        self.files = {"LoadAvg1m" : ("/proc/loadavg", r"([\d\.]+)", float),
                      "LoadAvg5m" : ("/proc/loadavg", r"[\d\.]+\s+([\d+\.]+)", float),
                      "LoadAvg15m" : ("/proc/loadavg", r"[\d\.]+\s+[\d+\.]+\s+([\d+\.]+)", float),
                     }
        #self.required4equal = ["LoadAvg15m"]
        if extended:
            rpmatch = r"[\d+\.]+\s+[\d+\.]+\s+[\d+\.]+\s+(\d+)"
            self.files["RunningProcesses"] = ("/proc/loadavg", rpmatch, int)
            apmatch = r"[\d+\.]+\s+[\d+\.]+\s+[\d+\.]+\s+\d+/(\d+)"
            self.files["AllProcesses"] = ("/proc/loadavg", apmatch, int)


################################################################################
# Infos about the memory of the system
################################################################################
class MemInfo(InfoGroup):
    def __init__(self, extended=False, anon=False):
        super(MemInfo, self).__init__(name="MemInfo", extended=extended, anon=anon)
        self.files = {"MemTotal" : ("/proc/meminfo", r"MemTotal:\s+(\d+\s[kKMG][B])"),
                      "MemFree" : ("/proc/meminfo", r"MemFree:\s+(\d+\s[kKMG][B])"),
                      "MemAvailable" : ("/proc/meminfo", r"MemAvailable:\s+(\d+\s[kKMG][B])"),
                      "SwapTotal" : ("/proc/meminfo", r"SwapTotal:\s+(\d+\s[kKMG][B])"),
                      "SwapFree" : ("/proc/meminfo", r"SwapFree:\s+(\d+\s[kKMG][B])"),
                     }
        if extended:
            self.files.update({"Buffers" : ("/proc/meminfo", r"Buffers:\s+(\d+\s[kKMG][B])"),
                               "Cached" : ("/proc/meminfo", r"Cached:\s+(\d+\s[kKMG][B])"),
                              })
        self.required4equal = ["MemFree"]

################################################################################
# Infos about the kernel
################################################################################
class KernelInfo(InfoGroup):
    def __init__(self, extended=False, anon=False):
        super(KernelInfo, self).__init__(name="KernelInfo", extended=extended, anon=anon)
        self.files = {"Version" : ("/proc/sys/kernel/osrelease",),
                      "CmdLine" : ("/proc/cmdline",),
                     }
        self.required4equal = self.files.keys()

################################################################################
# Infos about CGroups
################################################################################
class CgroupInfo(InfoGroup):
    def __init__(self, extended=False, anon=False):
        super(CgroupInfo, self).__init__(name="Cgroups", extended=extended, anon=anon)
        csetmat = re.compile(r"\d+\:cpuset\:([/\w\d\-\._]*)\n")
        cset = process_file(("/proc/self/cgroup", csetmat))
        base = pjoin("/sys/fs/cgroup/cpuset", cset.strip("/"))
        self.files = {"CPUs" : (pjoin(base, "cpuset.cpus"), r"(.+)", tointlist),
                      "Mems" : (pjoin(base, "cpuset.mems"), r"(.+)", tointlist),
                     }
        if extended:
            names = ["CPUs.effective", "Mems.effective"]
            files = ["cpuset.effective_cpus", "cpuset.effective_mems"]
            for key, fname in zip(names, files):
                self.files[key] = (pjoin(base, fname), r"(.+)", tointlist)
        self.required4equal = self.files.keys()

################################################################################
# Infos about the writeback workqueue
################################################################################
class Writeback(InfoGroup):
    def __init__(self, extended=False, anon=False):
        super(Writeback, self).__init__(name="Writeback", extended=extended, anon=anon)
        base = "/sys/bus/workqueue/devices/writeback"
        self.files = {"CPUmask" : (pjoin(base, "cpumask"), r"(.+)"),
                      "MaxActive" : (pjoin(base, "max_active"), r"(\d+)", int),
                     }
        self.required4equal = self.files.keys()

################################################################################
# Infos about transparent hugepages
################################################################################
class TransparentHugepages(InfoGroup):
    def __init__(self, extended=False, anon=False):
        super(TransparentHugepages, self).__init__(name="TransparentHugepages", extended=extended, anon=anon)
        base = "/sys/kernel/mm/transparent_hugepage"
        self.files = {"State" : (pjoin(base, "enabled"), r".*\[(.*)\].*"),
                      "UseZeroPage" : (pjoin(base, "use_zero_page"), r"(\d+)", bool),
                     }
        self.required4equal = self.files.keys()


################################################################################
# Infos about powercapping
#################################################################################
class PowercapInfoConstraintClass(InfoGroup):
    def __init__(self, ident, extended=False, anon=False, package=0, domain=-1):
        super(PowercapInfoConstraintClass, self).__init__(extended=extended, anon=anon)
        base = "/sys/devices/virtual/powercap/intel-rapl/intel-rapl:{}".format(package)
        self.name = "Constraint{}".format(ident)
        with open(pjoin(base, "constraint_{}_name".format(ident)), "rb") as fptr:
            self.name = totitle(fptr.read().decode(ENCODING).strip())
        if domain >= 0:
            base = pjoin(base, "intel-rapl:{}:{}".format(package, domain))
        names = ["PowerLimitUw",
                 "TimeWindowUs"]
        files = ["constraint_{}_power_limit_uw".format(ident),
                 "constraint_{}_time_window_us".format(ident)]
        for key, fname in zip(names, files):
            self.files[key] = (pjoin(base, fname), r"(.+)", int)
        self.required4equal = names

class PowercapInfoClass(PathMatchInfoGroup):
    def __init__(self, ident, extended=False, anon=False, package=0):
        super(PowercapInfoClass, self).__init__(extended=extended, anon=anon)
        base = "/sys/devices/virtual/powercap/intel-rapl"
        base = pjoin(base, "intel-rapl:{}/intel-rapl:{}:{}".format(package, package, ident))
        with open(pjoin(base, "name"), "rb") as fptr:
            self.name = totitle(fptr.read().decode(ENCODING).strip())
        self.files = {"Enabled" : (pjoin(base, "enabled"), r"(\d+)", bool)}
        self.basepath = pjoin(base, "constraint_*_name")
        self.match = r".*/constraint_(\d+)_name"
        self.subclass = PowercapInfoConstraintClass
        self.subargs = {"package" : package, "domain" : ident}

class PowercapInfoPackageClass(PathMatchInfoGroup):
    def __init__(self, ident, extended=False, anon=False):
        super(PowercapInfoPackageClass, self).__init__(name="Package", extended=extended, anon=anon)
        base = "/sys/devices/virtual/powercap/intel-rapl/intel-rapl:{}".format(ident)
        self.files = {"Enabled" : (pjoin(base, "enabled"), r"(\d+)", bool)}
        self.basepath = pjoin(base, "constraint_*_name")
        self.match = r".*/constraint_(\d+)_name"
        self.subclass = PowercapInfoConstraintClass
        self.subargs = {"package" : ident}

class PowercapInfoPackage(PathMatchInfoGroup):
    def __init__(self, package, extended=False, anon=False):
        super(PowercapInfoPackage, self).__init__(name="TMP", extended=extended, anon=anon)
        base = "/sys/devices/virtual/powercap/intel-rapl/intel-rapl:{}".format(package)
        with open(pjoin(base, "name"), "rb") as fptr:
            self.name = totitle(fptr.read().decode(ENCODING).strip())
        self.basepath = pjoin(base, "intel-rapl:{}:*".format(package))
        self.match = r".*/intel-rapl\:\d+:(\d+)"
        self.package = package
        self.subargs = {"package" : package}
        self.subclass = PowercapInfoClass
    def generate(self):
        super(PowercapInfoPackage, self).generate()
        cls = PowercapInfoPackageClass(self.package, extended=self.extended)
        cls.generate()
        self._instances.append(cls)


class PowercapInfo(PathMatchInfoGroup):
    def __init__(self, extended=False, anon=False):
        super(PowercapInfo, self).__init__(name="PowercapInfo", extended=extended, anon=anon)
        self.subclass = PowercapInfoPackage
        self.basepath = "/sys/devices/virtual/powercap/intel-rapl/intel-rapl:*"
        self.match = r".*/intel-rapl\:(\d+)"


################################################################################
# Infos about hugepages
################################################################################
class HugepagesClass(InfoGroup):
    def __init__(self, size, extended=False, anon=False):
        name = "Hugepages-{}".format(size)
        super(HugepagesClass, self).__init__(name=name, extended=extended, anon=anon)
        base = "/sys/kernel/mm/hugepages/hugepages-{}".format(size)
        self.files = {"Count" : (pjoin(base, "nr_hugepages"), r"(\d+)", int),
                      "Free" : (pjoin(base, "free_hugepages"), r"(\d+)", int),
                      "Reserved" : (pjoin(base, "resv_hugepages"), r"(\d+)", int),
                     }

class Hugepages(PathMatchInfoGroup):
    def __init__(self, extended=False, anon=False):
        super(Hugepages, self).__init__(extended=extended, anon=anon)
        self.name = "Hugepages"
        self.basepath = "/sys/kernel/mm/hugepages/hugepages-*"
        self.match = r".*/hugepages-(\d+[kKMG][B])"
        self.subclass = HugepagesClass

################################################################################
# Infos about compilers (C, C++ and Fortran)
################################################################################
class CompilerInfoClass(InfoGroup):
    def __init__(self, executable, extended=False, anon=False):
        super(CompilerInfoClass, self).__init__(extended=extended, anon=anon)
        self.name = executable
        self.commands = {"Version" : (executable, "--version", r"(\d+\.\d+\.\d+)")}
        self.constants["Path"] = get_abspath(executable)
        self.required4equal.append("Version")


class CCompilerInfo(ListInfoGroup):
    def __init__(self, extended=False, anon=False):
        super(CCompilerInfo, self).__init__(name="C", extended=extended, anon=anon)
        self.compilerlist = ["gcc", "icc", "clang", "pgcc", "xlc", "armclang", "ncc"]
        self.subclass = CompilerInfoClass
        if "CC" in os.environ:
            comp = os.environ["CC"]
            if comp not in self.compilerlist:
                self.compilerlist.append(comp)
        self.userlist = [ c for c in self.compilerlist if which(c)]


class CPlusCompilerInfo(ListInfoGroup):
    def __init__(self, extended=False, anon=False):
        super(CPlusCompilerInfo, self).__init__(name="C++", extended=extended, anon=anon)
        self.compilerlist = ["g++", "icpc", "clang++", "pg++", "armclang++", "nc++"]
        self.subclass = CompilerInfoClass
        if "CXX" in os.environ:
            comp = os.environ["CXX"]
            if comp not in self.compilerlist:
                self.compilerlist.append(comp)
        self.userlist = [ c for c in self.compilerlist if which(c)]


class FortranCompilerInfo(ListInfoGroup):
    def __init__(self, extended=False, anon=False):
        super(FortranCompilerInfo, self).__init__(name="Fortran", extended=extended, anon=anon)
        self.compilerlist = ["gfortran", "ifort", "flang", "pgf90", "armflang", "nfort"]
        self.subclass = CompilerInfoClass
        if "FC" in os.environ:
            comp = os.environ["FC"]
            if comp not in self.compilerlist:
                self.compilerlist.append(comp)
        self.userlist = [ c for c in self.compilerlist if which(c)]


class CompilerInfo(MultiClassInfoGroup):
    def __init__(self, extended=False, anon=False):
        super(CompilerInfo, self).__init__(name="CompilerInfo", extended=extended, anon=anon)
        self.classlist = [CCompilerInfo, CPlusCompilerInfo, FortranCompilerInfo]
        self.classargs = [{} for i in range(len(self.classlist))]

################################################################################
# Infos about Python interpreters
################################################################################
class PythonInfoClass(InfoGroup):
    def __init__(self, executable, extended=False, anon=False):
        super(PythonInfoClass, self).__init__(extended=extended, anon=anon)
        self.name = executable
        abspath = which(executable)
        if abspath:
            self.commands = {"Version" : (abspath, "--version 2>&1", r"(\d+\.\d+\.\d+)")}
            self.constants = {"Path" : abspath}
        self.required4equal.append("Version")

class PythonInfo(ListInfoGroup):
    def __init__(self, extended=False, anon=False):
        super(PythonInfo, self).__init__(name="PythonInfo", extended=extended, anon=anon)
        self.interpreters = ["python2", "python3", "python"]
        self.userlist = [ i for i in self.interpreters if len(get_abspath(i)) > 0]
        self.subclass = PythonInfoClass

################################################################################
# Infos about MPI libraries
################################################################################
class MpiInfoClass(InfoGroup):
    def __init__(self, executable, extended=False, anon=False):
        super(MpiInfoClass, self).__init__(name=executable, extended=extended, anon=anon)
        self.commands = {"Version" : (executable, "--version", r"(.+)", MpiInfoClass.mpiversion),
                         "Implementor" : (executable, "--version", r"(.+)", MpiInfoClass.mpivendor)
                        }
        abscmd = which(executable)
        if abscmd and len(abscmd) > 0:
            self.constants["Path"] = get_abspath(executable)
        self.required4equal = ["Version", "Implementor"]

    @staticmethod
    def mpivendor(value):
        if "Open MPI" in value or "OpenRTE" in value:
            return "OpenMPI"
        elif "Intel" in value and "MPI" in value:
            return "IntelMPI"
        elif "slurm" in value:
            return "Slurm"
        return "Unknown"

    @staticmethod
    def mpiversion(value):
        for line in value.split("\n"):
            mat = re.search(r"(\d+\.\d+\.\d+)", line)
            if mat:
                return mat.group(1)
            mat = re.search(r"Version (\d+) Update (\d+) Build (\d+) \(id: (\d+)\)", line)
            if mat:
                return "{}.{}".format(mat.group(1), mat.group(2))

class MpiInfo(ListInfoGroup):
    def __init__(self, extended=False, anon=False):
        super(MpiInfo, self).__init__(name="MpiInfo", extended=extended)
        self.mpilist = ["mpiexec", "mpiexec.hydra", "mpirun", "srun", "aprun"]
        self.subclass = MpiInfoClass
        self.userlist = [ m for m in self.mpilist if len(get_abspath(m)) > 0]


################################################################################
# Infos about environ variables
################################################################################
class ShellEnvironment(InfoGroup):
    def __init__(self, extended=False, anon=False):
        super(ShellEnvironment, self).__init__(name="ShellEnvironment", extended=extended, anon=anon)
    def update(self):
        super(ShellEnvironment, self).update()
        outdict = {}
        for key in os.environ:
            outdict.update({key : os.environ[key]})
        self._data.update(outdict)

################################################################################
# Infos about CPU prefetchers (LIKWID only)
# TODO: Does it work on ARM and POWER?
################################################################################
class PrefetcherInfoClass(InfoGroup):
    def __init__(self, ident, extended=False, anon=False, likwid_base=None):
        super(PrefetcherInfoClass, self).__init__(name="Cpu{}".format(ident), extended=extended, anon=anon)
        names = ["HW_PREFETCHER", "CL_PREFETCHER", "DCU_PREFETCHER", "IP_PREFETCHER"]
        cmd_opts = "-c {} -l".format(ident)
        cmd = "likwid-features"
        if likwid_base and os.path.isdir(likwid_base):
            abscmd = pjoin(likwid_base, cmd)
        if abscmd:
            for name in names:
                self.commands[name] = (abscmd, cmd_opts, r"{}\s+(\w+)".format(name), bool)
        self.required4equal = names

class PrefetcherInfo(PathMatchInfoGroup):
    def __init__(self, extended=False, anon=False, likwid_base=None):
        super(PrefetcherInfo, self).__init__(name="PrefetcherInfo", extended=extended, anon=anon)
        cmd = "likwid-features"
        if likwid_base and os.path.isdir(likwid_base):
            abscmd = pjoin(likwid_base, cmd)
        else:
            abscmd = which(cmd)

        if abscmd:
            data = process_cmd((abscmd, "-l -c 0", r"Feature\s+CPU\s(\d+)", int))
            if data == 0:
                self.basepath = "/sys/devices/system/cpu/cpu*"
                self.match = r".*/cpu(\d+)$"
                self.subclass = PrefetcherInfoClass
                self.subargs = {"likwid_base" : likwid_base}

################################################################################
# Infos about the turbo frequencies (LIKWID only)
################################################################################
class TurboInfo(InfoGroup):
    def __init__(self, extended=False, anon=False, likwid_base=None):
        super(TurboInfo, self).__init__(name="TurboInfo", extended=extended, anon=anon)
        self.cmd = "likwid-powermeter"
        self.cmd_opts = "-i 2>&1"
        self.error_match = r"Cannot gather values"
        names = ["BaseClock", "MinClock", "MinUncoreClock", "MaxUncoreClock"]
        matches = [r"Base clock:\s+([\d\.]+ MHz)",
                   r"Minimal clock:\s+([\d\.]+ MHz)",
                   r"Minimal Uncore frequency:\s+([\d\.]+ MHz)",
                   r"Maximal Uncore frequency:\s+([\d\.]+ MHz)",
                  ]
        if likwid_base and os.path.isdir(likwid_base):
            abscmd = pjoin(likwid_base, self.cmd)
        else:
            abscmd = which(self.cmd)
        if abscmd:
            data = process_cmd((abscmd, self.cmd_opts, matches[0]))
            if len(data) > 0 and not self.error_match:
                for name, regex in zip(names, matches):
                    self.commands[name] = (abscmd, self.cmd_opts, regex)
                regex = r"Performance energy bias:\s+(\d+)\s.*"
                self.commands["PerfEnergyBias"] = (abscmd, self.cmd_opts, regex, int)
                regex = r"C(\d+) ([\d\.]+ MHz)"
                freqfunc = TurboInfo.getactivecores
                self.commands["TurboFrequencies"] = (abscmd, self.cmd_opts, None, freqfunc)
        self.required4equal = self.commands.keys()
    @staticmethod
    def getactivecores(indata):
        freqs = []
        for line in indata.split("\n"):
            mat = re.match(r"C(\d+) ([\d\.]+ MHz)", line)
            if mat:
                freqs.append(mat.group(2))
        return freqs

################################################################################
# Infos about the clock sources provided by the kernel
################################################################################
class ClocksourceInfoClass(InfoGroup):
    def __init__(self, ident, extended=False, anon=False):
        super(ClocksourceInfoClass, self).__init__(anon=anon, extended=extended)
        self.name = "Clocksource{}".format(ident)
        base = "/sys/devices/system/clocksource/clocksource{}".format(ident)
        self.files["Current"] = (pjoin(base, "current_clocksource"), r"(\s+)", str)
        if extended:
            self.files["Available"] = (pjoin(base, "available_clocksource"), r"(.+)", tostrlist)
        self.required4equal = ["Current"]

class ClocksourceInfo(PathMatchInfoGroup):
    def __init__(self, extended=False, anon=False):
        super(ClocksourceInfo, self).__init__(anon=anon, extended=extended)
        self.name = "ClocksourceInfo"
        self.basepath = "/sys/devices/system/clocksource/clocksource*"
        self.match = r".*/clocksource(\d+)$"
        self.subclass = ClocksourceInfoClass

################################################################################
# Infos about the executable (if given on cmdline)
################################################################################
class ExecutableInfoExec(InfoGroup):
    def __init__(self, executable, extended=False, anon=False):
        super(ExecutableInfoExec, self).__init__(anon=anon, extended=extended)
        self.name = "ExecutableInfo"
        self.executable = executable
        abspath = get_abspath(self.executable)
        self.constants = {"Name" : str(self.executable),
                          "Abspath" : abspath,
                          "Size" : psize(abspath)}
        if extended:
            self.constants["MD5sum"] = ExecutableInfoExec.getmd5sum(abspath)
        self.required4equal = self.constants.keys()
    @staticmethod
    def getmd5sum(filename):
        hash_md5 = hashlib.md5()
        with open(filename, "rb") as md5fp:
            for chunk in iter(lambda: md5fp.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

class ExecutableInfoLibraries(InfoGroup):
    def __init__(self, executable, extended=False, anon=False):
        super(ExecutableInfoLibraries, self).__init__(anon=anon, extended=extended)
        self.name = "LinkedLibraries"
        self.executable = get_abspath(executable)
        self.ldd = "ldd {}; exit 0".format(self.executable)
    def update(self):
        libdict = {}
        rawdata = check_output(self.ldd, stderr=DEVNULL, shell=True)
        data = rawdata.decode(ENCODING)
        libregex = re.compile(r"\s*([^\s]+)\s+.*")
        pathregex = re.compile(r"\s*[^\s]+\s+=>\s+([^\s(]+).*")
        for line in data.split("\n"):
            libmat = libregex.search(line)
            if libmat:
                lib = libmat.group(1)
                pathmat = pathregex.search(line)
                if pathmat:
                    libdict.update({lib : pathmat.group(1)})
                elif pexists(lib):
                    libdict.update({lib : lib})
                else:
                    libdict.update({lib : None})
        self.required4equal = libdict.keys()
        self._data = libdict

class ExecutableInfo(MultiClassInfoGroup):
    def __init__(self, executable, extended=False, anon=False):
        super(ExecutableInfo, self).__init__(extended=extended, anon=anon)
        self.name = "ExecutableInfo"
        self.executable = executable
        self.classlist = [ExecutableInfoExec, ExecutableInfoLibraries]
        clsargs = {"executable" : self.executable}
        self.classargs = [clsargs for i in range(len(self.classlist))]

################################################################################
# Infos about the temperature using coretemp
################################################################################
class CoretempInfoHwmonClassX86(InfoGroup):
    def __init__(self, sensor, extended=False, anon=False, socket=0, hwmon=0):
        super(CoretempInfoHwmonClassX86, self).__init__(extended=extended, anon=anon)
        base = "/sys/devices/platform/coretemp.{}/hwmon/hwmon{}/".format(socket, hwmon)
        self.name = process_file((pjoin(base, "temp{}_label".format(sensor)),))
        self.files["Input"] = (pjoin(base, "temp{}_input".format(sensor)), r"(\d+)", int)
        if extended:
            self.files["Critical"] = (pjoin(base, "temp{}_crit".format(sensor)), r"(\d+)", int)
            self.files["Alarm"] = (pjoin(base, "temp{}_crit_alarm".format(sensor)), r"(\d+)", int)
            self.files["Max"] = (pjoin(base, "temp{}_max".format(sensor)), r"(\d+)", int)

class CoretempInfoHwmonX86(PathMatchInfoGroup):
    def __init__(self, hwmon, extended=False, anon=False, socket=0):
        super(CoretempInfoHwmonX86, self).__init__(name="Hwmon{}".format(hwmon), extended=extended, anon=anon)
        self.subclass = CoretempInfoHwmonClassX86
        self.subargs = {"socket" : socket, "hwmon" : hwmon}
        base = "/sys/devices/platform/coretemp.{}".format(socket)
        self.basepath = pjoin(base, "hwmon/hwmon{}/temp*_label".format(hwmon))
        self.match = r".*/temp(\d+)_label$"

class CoretempInfoSocketX86(PathMatchInfoGroup):
    def __init__(self, socket, extended=False, anon=False):
        super(CoretempInfoSocketX86, self).__init__(name="Package{}".format(socket), extended=extended, anon=anon)
        self.socket = socket
        self.subargs = {"socket" : socket}
        self.subclass = CoretempInfoHwmonX86
        self.basepath = "/sys/devices/platform/coretemp.{}/hwmon/hwmon*".format(self.socket)
        self.match = r".*/hwmon(\d+)$"

class CoretempInfoHwmonClassARM(InfoGroup):
    def __init__(self, sensor, extended=False, anon=False, hwmon=0):
        super(CoretempInfoHwmonClassARM, self).__init__(extended=extended, anon=anon)
        base = "/sys/devices/virtual/hwmon/hwmon{}".format(hwmon)
        self.name = "Core{}".format(sensor)
        self.files["Input"] = (pjoin(base, "temp{}_input".format(sensor)), r"(\d+)", int)
        if extended:
            self.files["Critical"] = (pjoin(base, "temp{}_crit".format(sensor)), r"(\d+)", int)

class CoretempInfoSocketARM(PathMatchInfoGroup):
    def __init__(self, hwmon, extended=False, anon=False):
        super(CoretempInfoSocketARM, self).__init__(name="Hwmon{}".format(hwmon), extended=extended, anon=anon)
        self.basepath = "/sys/devices/virtual/hwmon/hwmon{}/temp*_input".format(hwmon)
        self.match = r".*/temp(\d+)_input$"
        self.subclass = CoretempInfoHwmonClassARM
        self.subargs = {"hwmon" : hwmon}

class CoretempInfo(PathMatchInfoGroup):
    def __init__(self, extended=False, anon=False):
        super(CoretempInfo, self).__init__(name="CoretempInfo", extended=extended, anon=anon)
        machine = platform.machine()
        if machine in ["x86_64", "i386"]:
            self.subclass = CoretempInfoSocketX86
            self.basepath = "/sys/devices/platform/coretemp.*"
            self.match = r".*/coretemp\.(\d+)$"
        elif machine in ["aarch64"]:
            self.subclass = CoretempInfoSocketARM
            self.basepath = "/sys/devices/virtual/hwmon/hwmon*"
            self.match = r".*/hwmon(\d+)$"


################################################################################
# Infos about the BIOS
################################################################################
class BiosInfo(InfoGroup):
    def __init__(self, extended=False, anon=False):
        super(BiosInfo, self).__init__(name="BiosInfo", extended=extended, anon=anon)
        base = "/sys/devices/virtual/dmi/id"
        if pexists(base):
            self.files["BiosDate"] = (pjoin(base, "bios_date"),)
            self.files["BiosVendor"] = (pjoin(base, "bios_vendor"),)
            self.files["BiosVersion"] = (pjoin(base, "bios_version"),)
            self.files["SystemVendor"] = (pjoin(base, "sys_vendor"),)
            self.files["ProductName"] = (pjoin(base, "product_name"),)
            if pexists(pjoin(base, "product_vendor")):
                self.files["ProductVendor"] = (pjoin(base, "product_vendor"),)
            self.required4equal = self.files.keys()

################################################################################
# Infos about the thermal zones
################################################################################
class ThermalZoneInfoClass(InfoGroup):
    def __init__(self, zone, extended=False, anon=False):
        name = "ThermalZone{}".format(zone)
        super(ThermalZoneInfoClass, self).__init__(name=name, extended=extended, anon=anon)
        base = "/sys/devices/virtual/thermal/thermal_zone{}".format(zone)
        if pexists(pjoin(base, "device/description")):
            with (open(pjoin(base, "device/description"), "rb")) as filefp:
                self.name = filefp.read().decode(ENCODING).strip()
        self.files["Temperature"] = (pjoin(base, "temp"), r"(\d+)", int)
        if extended:
            self.files["Policy"] = (pjoin(base, "policy"), r"(.+)")
            avpath = pjoin(base, "available_policies")
            self.files["AvailablePolicies"] = (avpath, r"(.+)", tostrlist)
            self.files["Type"] = (pjoin(base, "type"), r"(.+)")

class ThermalZoneInfo(PathMatchInfoGroup):
    def __init__(self, extended=False, anon=False):
        super(ThermalZoneInfo, self).__init__(name="ThermalZoneInfo", extended=extended, anon=anon)
        self.basepath = "/sys/devices/virtual/thermal/thermal_zone*"
        self.match = r".*/thermal_zone(\d+)$"
        self.subclass = ThermalZoneInfoClass

################################################################################
# Infos about CPU vulnerabilities
################################################################################
class VulnerabilitiesInfo(InfoGroup):
    def __init__(self, extended=False, anon=False):
        super(VulnerabilitiesInfo, self).__init__(name="VulnerabilitiesInfo", extended=extended, anon=anon)
        base = "/sys/devices/system/cpu/vulnerabilities"
        for vfile in glob(pjoin(base, "*")):
            vkey = totitle(os.path.basename(vfile))
            self.files[vkey] = (vfile,)
            self.required4equal.append(vkey)

################################################################################
# Infos about logged in users (only count to avoid logging user names)
################################################################################
class UsersInfo(InfoGroup):
    def __init__(self, extended=False, anon=False):
        super(UsersInfo, self).__init__(name="UsersInfo", extended=extended, anon=anon)
        self.commands["LoggedIn"] = ("users", "", r"(.*)", UsersInfo.countusers)
    @staticmethod
    def countusers(value):
        if not value or len(value) == 0:
            return 0
        return len(list(set(re.split(r"[,\s]", value))))

################################################################################
# Infos from the dmidecode file (if DMIDECODE_FILE is available)
################################################################################
class DmiDecodeFile(InfoGroup):
    def __init__(self, dmifile, extended=False, anon=False):
        super(DmiDecodeFile, self).__init__(name="DmiDecodeFile", extended=extended, anon=anon)
        if pexists(dmifile):
            self.files["DmiDecode"] = (dmifile, )

################################################################################
# Infos about the CPU affinity
# Some Python versions provide a os.get_schedaffinity()
# If not available, use LIKWID (if allowed)
################################################################################
class CpuAffinity(InfoGroup):
    def __init__(self, extended=False, anon=False):
        super(CpuAffinity, self).__init__(name="CpuAffinity", extended=extended, anon=anon)
        if "get_schedaffinity" in dir(os):
            self.constants["Affinity" : os.get_schedaffinity()]
        elif DO_LIKWID:
            abscmd = which("likwid-pin")
            if abscmd and len(abscmd) > 0:
                self.commands["Affinity"] = (abspath, "-c N -p 2>&1", r"(.*)", tointlist)
                self.required4equal.append("Affinity")

################################################################################
# Infos about this script
################################################################################
class MachineStateVersionInfo(InfoGroup):
    def __init__(self, extended=False, anon=False):
        super(MachineStateVersionInfo, self).__init__(name="MachineStateVersion", extended=extended, anon=anon)
        self.constants["Version"] = MACHINESTATE_VERSION

################################################################################
# Infos about loaded modules in the modules system
################################################################################
class ModulesInfo(InfoGroup):
    def __init__(self, extended=False, anon=False):
        super(ModulesInfo, self).__init__(name="ModulesInfo", extended=extended, anon=anon)
        parse = ModulesInfo.parsemodules
        cmd_opts = "{} sh list -t 2>&1".format(MODULECMD_TCL_PATH)
        cmd = "tclsh"
        if len(get_abspath(cmd)) > 0 and pexists(MODULECMD_TCL_PATH):
            self.commands["Loaded"] = (cmd, cmd_opts, None, parse)
            self.required4equal.append("Loaded")
    @staticmethod
    def parsemodules(value):
        slist = re.split("\n", value)
        return slist[1:]

################################################################################
# Infos about InfiniBand adapters
################################################################################
class InfinibandInfoClassPort(InfoGroup):
    def __init__(self, port, extended=False, anon=False, driver=""):
        super(InfinibandInfoClassPort, self).__init__(extended=extended, anon=anon)
        self.name = "Port{}".format(port)
        ibpath = "/sys/class/infiniband/{}/ports/{}".format(driver, port)
        self.files["Rate"] = (pjoin(ibpath, "rate"), r"(.+)")
        self.files["PhysState"] = (pjoin(ibpath, "phys_state"), r"(.+)")
        self.files["LinkLayer"] = (pjoin(ibpath, "link_layer"), r"(.+)")


class InfinibandInfoClass(PathMatchInfoGroup):
    def __init__(self, driver, extended=False, anon=False):
        super(InfinibandInfoClass, self).__init__(extended=extended, anon=anon)
        self.name = driver
        ibpath = "/sys/class/infiniband/{}".format(driver)
        self.files["BoardId"] = (pjoin(ibpath, "board_id"), r"(.+)")
        self.files["FirmwareVersion"] = (pjoin(ibpath, "fw_ver"), r"([\d\.]+)")
        self.files["HCAType"] = (pjoin(ibpath, "hca_type"), r"([\w\d\.]+)")
        self.files["HWRevision"] = (pjoin(ibpath, "hw_rev"), r"([\w\d\.]+)")
        self.files["NodeType"] = (pjoin(ibpath, "node_type"), r"(.+)")
        if not anon:
            self.files["NodeGUID"] = (pjoin(ibpath, "node_guid"), r"(.+)")
            self.files["NodeDescription"] = (pjoin(ibpath, "node_desc"), r"(.+)")
            self.files["SysImageGUID"] = (pjoin(ibpath, "sys_image_guid"), r"(.+)")
        self.basepath = "/sys/class/infiniband/{}/ports/*".format(driver)
        self.match = r".*/(\d+)$"
        self.subclass = InfinibandInfoClassPort
        self.subargs = {"driver" : driver}

class InfinibandInfo(PathMatchInfoGroup):
    def __init__(self, extended=False, anon=False):
        super(InfinibandInfo, self).__init__(extended=extended, anon=anon)
        self.name = "InfinibandInfo"
        if pexists("/sys/class/infiniband"):
            self.basepath = "/sys/class/infiniband/*"
            self.match = r".*/(.*)$"
            self.subclass = InfinibandInfoClass

################################################################################
# Infos from nvidia-smi (Nvidia GPUs)
################################################################################
class NvidiaSmiInfoClass(InfoGroup):
    def __init__(self, device, extended=False, anon=False):
        super(NvidiaSmiInfoClass, self).__init__(extended=extended, anon=anon)
        self.name = "Card{}".format(device)
        self.cmd = "nvidia-smi"
        self.cmd_opts = "-q -i {}".format(device)
        abscmd = which(self.cmd)
        if abscmd:
            self.commands["ProductName"] = (self.cmd, self.cmd_opts, r"\s+Product Name\s+:\s+(.+)")
            self.commands["VBiosVersion"] = (self.cmd, self.cmd_opts, r"\s+VBIOS Version\s+:\s+(.+)")
            self.commands["ComputeMode"] = (self.cmd, self.cmd_opts, r"\s+Compute Mode\s+:\s+(.+)")
            self.commands["GPUCurrentTemp"] = (self.cmd, self.cmd_opts, r"\s+GPU Current Temp\s+:\s+(\d+\sC)")
            self.commands["MemTotal"] = (self.cmd, self.cmd_opts, r"\s+Total\s+:\s+(\d+\sMiB)")
            self.commands["MemFree"] = (self.cmd, self.cmd_opts, r"\s+Free\s+:\s+(\d+\sMiB)")
            if extended:
                self.commands["PciDevice"] = (self.cmd, self.cmd_opts, r"^GPU\s+([0-9a-fA-F:]+)")
                self.commands["PciLinkWidth"] = (self.cmd, self.cmd_opts, r"\s+Current\s+:\s+(\d+x)")
                self.commands["GPUMaxOpTemp"] = (self.cmd, self.cmd_opts, r"\s+GPU Max Operating Temp\s+:\s+(\d+\sC)")

class NvidiaSmiInfo(ListInfoGroup):
    def __init__(self, extended=False, anon=False):
        super(NvidiaSmiInfo, self).__init__(name="NvidiaInfo", extended=extended, anon=anon)
        self.cmd = "nvidia-smi"
        self.cmd_opts = "-q"
        abscmd = which(self.cmd)
        if abscmd:
            num_gpus = process_cmd((self.cmd, self.cmd_opts, r"Attached GPUs\s+:\s+(\d+)", int))
            if num_gpus > 0:
                self.userlist = [i for i in range(num_gpus)]
                self.subclass = NvidiaSmiInfoClass
        self.commands["DriverVersion"] = (self.cmd, self.cmd_opts, r"Driver Version\s+:\s+([\d\.]+)")
        self.commands["CudaVersion"] = (self.cmd, self.cmd_opts, r"CUDA Version\s+:\s+([\d\.]+)")


################################################################################
# Infos from veosinfo (NEC Tsubasa)
################################################################################
class NecTsubasaInfoTemps(InfoGroup):
    def __init__(self, tempkeys, ve_base="", extended=False, anon=False, device=0):
        super(NecTsubasaInfoTemps, self).__init__(extended=extended, anon=anon)
        self.name = "Temperatures"
        vecmd = pjoin(ve_base, "vecmd")
        veargs = "-N {} info".format(device)
        for tempkey in tempkeys:
            self.commands[tempkey] = (vecmd, veargs, "\s+{}\s+:\s+([\d\.]+\sC)".format(tempkey))

class NecTsubasaInfoClass(InfoGroup):
    def __init__(self, device, ve_base="", extended=False, anon=False):
        super(NecTsubasaInfoClass, self).__init__(extended=extended, anon=anon)
        self.name = "Card{}".format(device)
        vecmd = pjoin(ve_base, "vecmd")
        veargs = "-N {} info".format(device)
        if pexists(vecmd):
            self.commands["State"] = (vecmd, veargs, r"VE State\s+:\s+(.+)", totitle)
            self.commands["Model"] = (vecmd, veargs, r"VE Model\s+:\s+(\d+)")
            self.commands["ProductType"] = (vecmd, veargs, r"Product Type\s+:\s+(\d+)")
            self.commands["DriverVersion"] = (vecmd, veargs, r"VE Driver Version\s+:\s+([\d\.]+)")
            self.commands["Cores"] = (vecmd, veargs, r"Cores\s+:\s+(\d+)")
            self.commands["MemTotal"] = (vecmd, veargs, r"Memory Size\s+:\s+(\d+)")
            if extended:
                self.commands["PciLinkWidth"] = (vecmd, veargs, r"Negotiated Link Width\s+:\s+(x\d+)")
            ve_temps = process_cmd((vecmd, veargs, None, NecTsubasaInfoClass.gettempkeys))
            tempargs = {"device" : device, "ve_base" : ve_base}
            self._instances.append(NecTsubasaInfoTemps(ve_temps, extended=extended, anon=anon, **tempargs))
    @staticmethod
    def gettempkeys(value):
        keys = []
        for line in re.split("\n", value):
            if re.match("(.+):\s+[\d\.]+\sC$", line):
                key = re.match("(.+):\s+[\d\.]+\sC$", line).group(1).strip()
                keys.append(key)
        return keys


class NecTsubasaInfo(ListInfoGroup):
    def __init__(self, ve_base="", extended=False, anon=False):
        super(NecTsubasaInfo, self).__init__(name="NecTsubasaInfo", extended=extended, anon=anon)
        vecmd = pjoin(ve_base, "vecmd")
        if pexists(vecmd):
            num_ves = process_cmd((vecmd, "info", r"Attached VEs\s+:\s+(\d+)", int))
            if num_ves > 0:
                self.userlist = [i for i in range(num_ves)]
                self.subclass = NecTsubasaInfoClass
                self.subargs = {"ve_base" : ve_base}


################################################################################
# Skript code
################################################################################

def read_cli():
    parser = argparse.ArgumentParser(description='Reads and outputs system information as JSON document')
    parser.add_argument('-e', '--extended', action='store_true', default=False, help='extended output (default: False)')
    parser.add_argument('-s', '--sort', action='store_true', default=False, help='sort JSON output (default: False)')

    parser.add_argument('-a', '--anonymous', action='store_true', default=False, help='Remove host-specific information (default: False)')
    parser.add_argument('-c', '--config', help='print configuration as JSON (files, commands, ...)', default=False, action='store_true')
    parser.add_argument('-j', '--json', help='compare given JSON with current state', default=None)
    parser.add_argument('-i', '--indent', default=4, type=int, help='indention in JSON output (default: 4)')
    parser.add_argument('-o', '--output', help='save JSON to file (default: stdout)', default=None)
    parser.add_argument('executable', help='analyze executable (optional)', nargs='?', default=None)
    pargs = vars(parser.parse_args(sys.argv[1:]))
    return pargs
    #return pargs["extended"], pargs["executable"], pargs["output"]

if __name__ == "__main__":
    cliargs = read_cli()
    mstate = MachineState(extended=cliargs["extended"],
                          executable=cliargs["executable"],
                          anon=cliargs["anonymous"])
    mstate.generate()
    mstate.update()
    if cliargs["json"]:
        print(mstate == cliargs["json"])
        sys.exit(0)
    jsonout = {}
    if not cliargs["config"]:
        jsonout = mstate.get_json(sort=cliargs["sort"], intend=cliargs["indent"])
    else:
        jsonout = mstate.get_config(sort=cliargs["sort"], intend=cliargs["indent"])
    if not cliargs["output"]:
        print(jsonout)
    else:
        with open(cliargs["output"], "w") as outfp:
            outfp.write(mstate.get_json(sort=cliargs["sort"], intend=cliargs["indent"]))
            outfp.write("\n")

#    n = NecTsubasaInfo(VEOS_BASE, extended=cliargs["extended"])
#    n.generate()
#    n.update()
#    ndict = n.get()
#    copydict = deepcopy(ndict)
#    print(n == copydict)
#    print(n.get_json(sort=cliargs["sort"], intend=cliargs["indent"]))
