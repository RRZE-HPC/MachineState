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
import hashlib
import argparse


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


################################################################################
# Processing functions for single entries in class attributes files and commands
# TODO: Write function that processes all entries for a single file/cmd to
#       reduce runtime. Some commands are called multiple times to get different
#       information
################################################################################
def process_file(args):
    data = None
    fname, *matchconvert = args
    if fname and pexists(fname) and os.path.isfile(fname):
        with (open(fname, "rb")) as filefp:
            data = filefp.read().decode(ENCODING).strip()
            if matchconvert:
                fmatch, *convert = matchconvert
                if fmatch:
                    mat = re.search(fmatch, data)
                    if mat:
                        data = mat.group(1)
                if convert:
                    fconvert, = convert
                    if fconvert:
                        data = fconvert(data)
    return data

def process_cmd(args):
    data = None
    cmd, *optsmatchconvert = args
    if cmd:
        which_cmd = "which {}; exit 0;".format(cmd)
        data = check_output(which_cmd, stderr=DEVNULL, shell=True).decode(ENCODING).strip()
        if data and len(data) > 0:
            if optsmatchconvert:
                cmd_opts, *matchconvert = optsmatchconvert
                exe = "{} {}; exit 0;".format(cmd, cmd_opts)
                data = check_output(exe, stderr=DEVNULL, shell=True).decode(ENCODING).strip()
                if data and len(data) >= 0:
                    cmatch, *convert = matchconvert
                    if cmatch:
                        mat = re.match(cmatch, data)
                        if mat:
                            data = mat.group(1)
                        elif '\n' in data:
                            for l in data.split("\n"):
                                mat = re.match(cmatch, l)
                                if mat:
                                    data = mat.group(1)
                                    break
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


################################################################################
# Base Classes
################################################################################


class InfoGroup:
    def __init__(self, name=None, extended=False):
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
        self.name = name
        self.extended = extended

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

class PathMatchInfoGroup(InfoGroup):
    '''Class for matching files in a folder and create subclasses for each path'''
    def __init__(self, name=None,
                       extended=False,
                       basepath=None,
                       match=None,
                       subclass=None,
                       subargs={}):
        super(PathMatchInfoGroup, self).__init__(extended=extended, name=name)
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
                cls = self.subclass(item, extended=self.extended, **self.subargs)
                cls.generate()
                self._instances.append(cls)

class ListInfoGroup(InfoGroup):
    '''Class for creating subclasses based on a list given by the user. All subclasses have the same
    class type.
    '''
    def __init__(self, name=None,
                       extended=False,
                       userlist=None,
                       subclass=None,
                       subargs={}):
        super(ListInfoGroup, self).__init__(extended=extended, name=name)
        self.userlist = userlist or []
        self.subclass = subclass
        self.subargs = subargs
    def generate(self):
        if self.userlist and self.subclass:
            for item in self.userlist:
                cls = self.subclass(item, extended=self.extended, **self.subargs)
                cls.generate()
                self._instances.append(cls)

class MultiClassInfoGroup(InfoGroup):
    '''Class for creating subclasses based on a list of class types given by the user.
    '''
    def __init__(self, name=None,
                       extended=False,
                       classlist=None,
                       classargs={}):
        super(MultiClassInfoGroup, self).__init__(extended=extended, name=name)
        self.classlist = classlist
        self.classargs = classargs

    def generate(self):
        for cltype in self.classlist:
            cls = cltype(extended=self.extended, **self.classargs)
            cls.generate()
            self._instances.append(cls)

# This is basically a MultiClassInfoGroup but it does not have a name and no generate function
# but could be rewritten using a MultiClassInfoGroup
class MachineState():
    def __init__(self, extended=False, executable=None):
        self._instances = []
        self.extended = extended
        self.executable = executable
        self.subclasses = [
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
            MachineStateVersionInfo,
            ModulesInfo,
        ]

        for cls in self.subclasses:
            self._instances.append(cls(extended=extended))
        if pexists(DMIDECODE_FILE):
            self._instances.append(DmiDecodeFile(DMIDECODE_FILE, extended=self.extended))
        if self.executable:
            self._instances.append(ExecutableInfo(self.executable, extended=self.extended))
        if DO_LIKWID:
            likwid_base = LIKWID_PATH
            if not likwid_base:
                path = which("likwid-topology")
                if path:
                    likwid_base = os.path.dirname(path)
            self._instances.append(PrefetcherInfo(likwid_base=likwid_base, extended=self.extended))
            self._instances.append(TurboInfo(likwid_base=likwid_base, extended=self.extended))
    def update(self):
        for inst in self._instances:
            inst.generate()
            inst.update()
    def get(self):
        outdict = {}
        for inst in self._instances:
            clsout = inst.get()
            outdict.update({inst.name : clsout})
        return outdict
    def get_json(self, sort=False, intend=4):
        outdict = self.get()
        return json.dumps(outdict, sort_keys=sort, indent=intend)

################################################################################
# Configuration Classes
################################################################################

################################################################################
# Infos about operating system
################################################################################
class OSInfo(InfoGroup):
    def __init__(self, extended=False):
        super(OSInfo, self).__init__(name="OperatingSystemInfo", extended=extended)
        self.files = {"Name" : ("/etc/os-release", "NAME=[\"]*([^\"]+)[\"]*\s*"),
                      "Version" : ("/etc/os-release", "VERSION=[\"]*([^\"]+)[\"]*\s*"),
                     }
        if extended:
            self.files["URL"] = ("/etc/os-release", "HOME_URL=[\"]*([^\"]+)[\"]*\s*")
            self.files["Codename"] = ("/etc/os-release", "VERSION_CODENAME=[\"]*([^\"\d\s]+)[\"]*")

################################################################################
# Infos about NUMA balancing
################################################################################
class NumaBalance(InfoGroup):
    def __init__(self, extended=False):
        super(NumaBalance, self).__init__("NumaBalancing", extended)
        base = "/proc/sys/kernel"
        regex = r"(\d+)"
        self.files = {"Enabled" : (pjoin(base, "numa_balancing"), regex, bool)}
        if extended:
            names = ["ScanDelayMs", "ScanPeriodMaxMs", "ScanPeriodMinMs", "ScanSizeMb"]
            files = ["numa_balancing_scan_delay_ms", "numa_balancing_scan_period_max_ms",
                     "numa_balancing_scan_period_min_ms", "numa_balancing_scan_size_mb"]
            for key, fname in zip(names, files):
                self.files[key] = (pjoin(base, fname), regex, int)

################################################################################
# Infos about the host
################################################################################
class HostInfo(InfoGroup):
    def __init__(self, extended=False):
        super(HostInfo, self).__init__(name="HostInfo", extended=extended)
        self.commands = {"Hostname" : ("hostname", "-s", r"(.+)")}
        if extended:
            self.commands.update({"Domainname" : ("hostname", "-d", r"(.+)")})
            self.commands.update({"FQDN" : ("hostname", "-f", r"(.+)")})

################################################################################
# Infos about the CPU
################################################################################
class CpuInfo(InfoGroup):
    def __init__(self, extended=False):
        super(CpuInfo, self).__init__(name="CpuInfo", extended=extended)
        if platform.machine() in ["x86_64", "i386"]:
            self.files = {"Vendor" : ("/proc/cpuinfo", r"vendor_id\s+:\s(.*)"),
                          "Name" : ("/proc/cpuinfo", r"model name\s+:\s(.+)"),
                          "Family" : ("/proc/cpuinfo", r"cpu family\s+:\s(.+)", int),
                          "Model" : ("/proc/cpuinfo", r"model\s+:\s(.+)", int),
                          "Stepping" : ("/proc/cpuinfo", r"stepping\s+:\s(.+)", int),
                         }
        elif platform.machine() in ["armv7", "armv8"]:
            self.files = {"Vendor" : ("/proc/cpuinfo", r"CPU implementer\s+:\s(.*)"),
                          "Name" : ("/proc/cpuinfo", r"model name\s+:\s(.+)"),
                          "Family" : ("/proc/cpuinfo", r"CPU architecture\s+:\s(.+)", int),
                          "Model" : ("/proc/cpuinfo", r"CPU variant\s+:\s(.+)", int),
                          "Stepping" : ("/proc/cpuinfo", r"CPU revision\s+:\s(.+)", int),
                          "Variant" : ("/proc/cpuinfo", r"CPU part\s+:\s(.+)", int),
                         }
        elif platform.machine() in ["power"]:
            self.files = {"Vendor" : ("/proc/cpuinfo", r"vendor_id\s+:\s(.*)"),
                          "Name" : ("/proc/cpuinfo", r"model name\s+:\s(.+)"),
                          "Family" : ("/proc/cpuinfo", r"cpu family\s+:\s(.+)", int),
                          "Model" : ("/proc/cpuinfo", r"model\s+:\s(.+)", int),
                          "Stepping" : ("/proc/cpuinfo", r"stepping\s+:\s(.+)", int),
                         }
        if pexists("/sys/devices/system/cpu/smt/active"):
            self.files["SMT"] = ("/sys/devices/system/cpu/smt/active", r"(\d+)", bool)
        if extended:
            if platform.machine() in ["x86_64", "i386"]:
                self.files["Flags"] = ("/proc/cpuinfo", r"flags\s+:\s(.+)", tostrlist)
                self.files["Microcode"] = ("/proc/cpuinfo", r"microcode\s+:\s(.+)")
                self.files["Bugs"] = ("/proc/cpuinfo", r"bugs\s+:\s(.+)", tostrlist)
            elif platform.machine() in ["armv7", "armv8"]:
                self.files["Flags"] = ("/proc/cpuinfo", r"Features\s+:\s(.+)", tostrlist)

################################################################################
# CPU Topology
################################################################################
class CpuTopologyClass(InfoGroup):
    def __init__(self, ident, extended=False):
        super(CpuTopologyClass, self).__init__(name="Cpu{}".format(ident), extended=extended)
        base = "/sys/devices/system/cpu/cpu{}/topology".format(ident)
        self.files = {"CoreId" : (pjoin(base, "core_id"), r"(\d+)", int),
                      "PackageId" : (pjoin(base, "physical_package_id"), r"(\d+)", int),
                     }
        self.constants = {"HWThread" : ident,
                          "ThreadId" : CpuTopologyClass.getthreadid(ident)
                         }

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
    def __init__(self, extended=False):
        super(CpuTopology, self).__init__(extended=extended)
        self.name = "CpuTopology"
        self.basepath = "/sys/devices/system/cpu/cpu*"
        self.match = r".*/cpu(\d+)$"
        self.subclass = CpuTopologyClass


################################################################################
# CPU Frequency
################################################################################
class CpuFrequencyClass(InfoGroup):
    def __init__(self, ident, extended=False):
        super(CpuFrequencyClass, self).__init__(name="Cpu{}".format(ident), extended=extended)
        base = "/sys/devices/system/cpu/cpu{}/cpufreq".format(ident)
        if pexists(pjoin(base, "scaling_max_freq")):
            self.files["MaxFreq"] = (pjoin(base, "scaling_max_freq"), r"(\d+)", int)
        if pexists(pjoin(base, "scaling_max_freq")):
            self.files["MinFreq"] = (pjoin(base, "scaling_min_freq"), r"(\d+)", int)
        if pexists(pjoin(base, "scaling_governor")):
            self.files["Governor"] = (pjoin(base, "scaling_governor"), r"(.+)")
        if pexists(pjoin(base, "energy_performance_preference")):
            self.files["EnergyPerfPreference"] = (pjoin(base, "energy_performance_preference"), r"(.+)")
        if extended:
            if pexists(pjoin(base, "cpuinfo_transition_latency")):
                self.files["TransitionLatency"] = (pjoin(base, "cpuinfo_transition_latency"), r"(\d+)", int)


class CpuFrequency(PathMatchInfoGroup):
    def __init__(self, extended=False):
        super(CpuFrequency, self).__init__(extended=extended)
        self.name = "CpuFrequency"
        if pexists("/sys/devices/system/cpu/cpu0/cpufreq"):
            self.basepath = "/sys/devices/system/cpu/cpu*"
            self.match = r".*/cpu(\d+)$"
            self.subclass = CpuFrequencyClass
        if extended:
            base = "/sys/devices/system/cpu/cpu{}/cpufreq".format(0)
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

################################################################################
# NUMA Topology
################################################################################
class NumaInfoHugepagesClass(InfoGroup):
    def __init__(self, size, extended=False, node=0):
        name = "Hugepages-{}".format(size)
        super(NumaInfoHugepagesClass, self).__init__(name=name, extended=extended)
        base = "/sys/devices/system/node/node{}/hugepages/hugepages-{}".format(node, size)
        self.files = {"Count" : (pjoin(base, "nr_hugepages"), r"(\d+)", int),
                      "Free" : (pjoin(base, "free_hugepages"), r"(\d+)", int),
                     }

class NumaInfoClass(PathMatchInfoGroup):
    def __init__(self, node, extended=False):
        super(NumaInfoClass, self).__init__(name="NumaNode{}".format(node), extended=extended)
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
        self.basepath = "/sys/devices/system/node/node{}/hugepages/hugepages-*".format(node)
        self.match = r".*/hugepages-(\d+[kKMG][B])$"
        self.subclass = NumaInfoHugepagesClass
        self.subargs = {"node" : node}

class NumaInfo(PathMatchInfoGroup):
    def __init__(self, extended=False):
        super(NumaInfo, self).__init__(name="NumaInfo", extended=extended)
        self.basepath = "/sys/devices/system/node/node*"
        self.match = r".*/node(\d+)$"
        self.subclass = NumaInfoClass

################################################################################
# Cache Topology
################################################################################
class CacheTopologyClass(InfoGroup):
    def __init__(self, ident, extended=False):
        super(CacheTopologyClass, self).__init__(name="L{}".format(ident), extended=extended)
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
            self.files["PhysicalLineSize"] = (pjoin(base, "physical_line_partition"), r"(\d+)", int)

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
    def __init__(self, extended=False):
        super(CacheTopology, self).__init__(name="CacheTopology", extended=extended)
        self.basepath = "/sys/devices/system/cpu/cpu0/cache/index*"
        self.match = r".*/index(\d+)$"
        self.subclass = CacheTopologyClass

################################################################################
# Infos about the uptime of the system
################################################################################
class Uptime(InfoGroup):
    def __init__(self, extended=False):
        super(Uptime, self).__init__(name="Uptime", extended=extended)
        self.files = {"Uptime" : ("/proc/uptime", r"([\d\.]+)\s+[\d\.]+", float)}
        if extended:
            self.files.update({"CpusIdle" : ("/proc/uptime", r"[\d\.]+\s+([\d\.]+)", float)})

################################################################################
# Infos about the load of the system
################################################################################
class LoadAvg(InfoGroup):
    def __init__(self, extended=False):
        super(LoadAvg, self).__init__(name="LoadAvg", extended=extended)
        self.files = {"LoadAvg1m" : ("/proc/loadavg", r"([\d\.]+)", float),
                      "LoadAvg5m" : ("/proc/loadavg", r"[\d\.]+\s+([\d+\.]+)", float),
                      "LoadAvg15m" : ("/proc/loadavg", r"[\d\.]+\s+[\d+\.]+\s+([\d+\.]+)", float),
                     }
        if extended:
            rpmatch = r"[\d+\.]+\s+[\d+\.]+\s+[\d+\.]+\s+(\d+)"
            self.files["RunningProcesses"] = ("/proc/loadavg", rpmatch, int)
            apmatch = r"[\d+\.]+\s+[\d+\.]+\s+[\d+\.]+\s+\d+/(\d+)"
            self.files["AllProcesses"] = ("/proc/loadavg", apmatch, int)


################################################################################
# Infos about the memory of the system
################################################################################
class MemInfo(InfoGroup):
    def __init__(self, extended=False):
        super(MemInfo, self).__init__(name="MemInfo", extended=extended)
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

################################################################################
# Infos about the kernel
################################################################################
class KernelInfo(InfoGroup):
    def __init__(self, extended=False):
        super(KernelInfo, self).__init__(name="KernelInfo", extended=extended)
        self.files = {"Version" : ("/proc/sys/kernel/osrelease",),
                      "CmdLine" : ("/proc/cmdline",),
                     }

################################################################################
# Infos about CGroups
################################################################################
class CgroupInfo(InfoGroup):
    def __init__(self, extended=False):
        super(CgroupInfo, self).__init__(name="Cgroups", extended=extended)
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

################################################################################
# Infos about the writeback workqueue
################################################################################
class Writeback(InfoGroup):
    def __init__(self, extended=False):
        super(Writeback, self).__init__(name="Writeback", extended=extended)
        base = "/sys/bus/workqueue/devices/writeback"
        self.files = {"CPUmask" : (pjoin(base, "cpumask"), r"(.+)"),
                      "MaxActive" : (pjoin(base, "max_active"), r"(\d+)", int),
                     }

################################################################################
# Infos about transparent hugepages
################################################################################
class TransparentHugepages(InfoGroup):
    def __init__(self, extended=False):
        super(TransparentHugepages, self).__init__(name="TransparentHugepages", extended=extended)
        base = "/sys/kernel/mm/transparent_hugepage"
        self.files = {"State" : (pjoin(base, "enabled"), r".*\[(.*)\].*"),
                      "UseZeroPage" : (pjoin(base, "use_zero_page"), r"(\d+)", bool),
                     }


################################################################################
# Infos about powercapping
#################################################################################
class PowercapInfoConstraintClass(InfoGroup):
    def __init__(self, ident, extended=False, package=0, domain=-1):
        super(PowercapInfoConstraintClass, self).__init__(extended=extended)
        base = "/sys/devices/virtual/powercap/intel-rapl/intel-rapl:{}".format(package)
        self.name = "Constraint{}".format(ident)
        with open(pjoin(base, "constraint_{}_name".format(ident)), "rb") as fptr:
            self.name = totitle(fptr.read().decode(ENCODING).strip())
        if domain >= 0:
            base = pjoin(base, "intel-rapl:{}:{}".format(package, domain))
        names = ["PowerLimitUw".format(ident),
                 "TimeWindowUs".format(ident)]
        files = ["constraint_{}_power_limit_uw".format(ident),
                 "constraint_{}_time_window_us".format(ident)]
        for key, fname in zip(names, files):
            self.files[key] = (pjoin(base, fname), r"(.+)", int)

class PowercapInfoClass(PathMatchInfoGroup):
    def __init__(self, ident, extended=False, package=0):
        super(PowercapInfoClass, self).__init__(extended=extended)
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
    def __init__(self, ident, extended=False):
        super(PowercapInfoPackageClass, self).__init__(name="Package", extended=extended)
        base = "/sys/devices/virtual/powercap/intel-rapl/intel-rapl:{}".format(ident)
        self.files = {"Enabled" : (pjoin(base, "enabled"), r"(\d+)", bool)}
        self.basepath = pjoin(base, "constraint_*_name")
        self.match = r".*/constraint_(\d+)_name"
        self.subclass = PowercapInfoConstraintClass
        self.subargs = {"package" : ident}

class PowercapInfoPackage(PathMatchInfoGroup):
    def __init__(self, package, extended=False):
        super(PowercapInfoPackage, self).__init__(name="TMP", extended=extended)
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
    def __init__(self, extended=False):
        super(PowercapInfo, self).__init__(name="PowercapInfo", extended=extended)
        self.subclass = PowercapInfoPackage
        self.basepath = "/sys/devices/virtual/powercap/intel-rapl/intel-rapl:*"
        self.match = r".*/intel-rapl\:(\d+)"


################################################################################
# Infos about hugepages
################################################################################
class HugepagesClass(InfoGroup):
    def __init__(self, size, extended=False):
        name = "Hugepages-{}".format(size)
        super(HugepagesClass, self).__init__(name=name, extended=extended)
        base = "/sys/kernel/mm/hugepages/hugepages-{}".format(size)
        self.files = {"Count" : (pjoin(base, "nr_hugepages"), r"(\d+)", int),
                      "Free" : (pjoin(base, "free_hugepages"), r"(\d+)", int),
                      "Reserved" : (pjoin(base, "resv_hugepages"), r"(\d+)", int),
                     }

class Hugepages(PathMatchInfoGroup):
    def __init__(self, extended=False):
        super(Hugepages, self).__init__(extended=extended)
        self.name = "Hugepages"
        self.basepath = "/sys/kernel/mm/hugepages/hugepages-*"
        self.match = r".*/hugepages-(\d+[kKMG][B])"
        self.subclass = HugepagesClass

################################################################################
# Infos about compilers (C, C++ and Fortran)
################################################################################
class CompilerInfoClass(InfoGroup):
    def __init__(self, executable, extended=False):
        super(CompilerInfoClass, self).__init__(extended)
        self.name = executable
        self.commands = {"Version" : (executable, "--version", r"(\d+\.\d+\.\d+)")}
        self.constants["Path"] = get_abspath(executable)


class CCompilerInfo(ListInfoGroup):
    def __init__(self, extended=False):
        super(CCompilerInfo, self).__init__(name="C", extended=extended)
        self.compilerlist = ["gcc", "icc", "clang", "pgcc", "xlc", "armclang"]
        self.subclass = CompilerInfoClass
        if "CC" in os.environ:
            comp = os.environ["CC"]
            if comp not in self.compilerlist:
                self.compilerlist.append(comp)
        self.userlist = [ c for c in self.compilerlist if len(get_abspath(c)) > 0]


class CPlusCompilerInfo(ListInfoGroup):
    def __init__(self, extended=False):
        super(CPlusCompilerInfo, self).__init__(name="C++", extended=extended)
        self.compilerlist = ["g++", "icpc", "clang++", "pg++", "armclang++"]
        self.subclass = CompilerInfoClass
        if "CXX" in os.environ:
            comp = os.environ["CXX"]
            if comp not in self.compilerlist:
                self.compilerlist.append(comp)
        self.userlist = [ c for c in self.compilerlist if len(get_abspath(c)) > 0]


class FortranCompilerInfo(ListInfoGroup):
    def __init__(self, extended=False):
        super(FortranCompilerInfo, self).__init__(name="Fortran", extended=extended)
        self.compilerlist = ["gfortran", "ifort", "flang", "pgf90", "armflang"]
        self.subclass = CompilerInfoClass
        if "FC" in os.environ:
            comp = os.environ["FC"]
            if comp not in self.compilerlist:
                self.compilerlist.append(comp)
        self.userlist = [ c for c in self.compilerlist if len(get_abspath(c)) > 0]


class CompilerInfo(MultiClassInfoGroup):
    def __init__(self, extended=False):
        super(CompilerInfo, self).__init__(name="CompilerInfo", extended=extended)
        self.classlist = [CCompilerInfo, CPlusCompilerInfo, FortranCompilerInfo]

################################################################################
# Infos about Python interpreters
################################################################################
class PythonInfoClass(InfoGroup):
    def __init__(self, executable, extended=False):
        super(PythonInfoClass, self).__init__(extended)
        self.name = executable
        abspath = get_abspath(executable)
        self.commands = {"Version" : (abspath, "--version 2>&1", r"(\d+\.\d+\.\d+)")}
        self.constants = {"Path" : get_abspath(abspath)}

class PythonInfo(ListInfoGroup):
    def __init__(self, extended=False):
        super(PythonInfo, self).__init__(name="PythonInfo", extended=extended)
        self.interpreters = ["python2", "python3", "python"]
        self.userlist = [ i for i in self.interpreters if len(get_abspath(i)) > 0]
        self.subclass = PythonInfoClass

################################################################################
# Infos about MPI libraries
################################################################################
class MpiInfoClass(InfoGroup):
    def __init__(self, executable, extended=False):
        super(MpiInfoClass, self).__init__(name=executable, extended=extended)
        self.commands = {"Version" : (executable, "--version", r"(.+)", MpiInfoClass.mpiversion),
                         "Implementor" : (executable, "--version", r"(.+)", MpiInfoClass.mpivendor)
                        }
        self.constants["Path"] = get_abspath(executable)

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
    def __init__(self, extended=False):
        super(MpiInfo, self).__init__(name="MpiInfo", extended=extended)
        self.mpilist = ["mpiexec", "mpiexec.hydra", "mpirun", "srun", "aprun"]
        self.subclass = MpiInfoClass
        self.userlist = [ m for m in self.mpilist if len(get_abspath(m)) > 0]


################################################################################
# Infos about environ variables
################################################################################
class ShellEnvironment(InfoGroup):
    def __init__(self, extended=False):
        super(ShellEnvironment, self).__init__(name="ShellEnvironment", extended=extended)
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
    def __init__(self, ident, extended=False, likwid_base=None):
        super(PrefetcherInfoClass, self).__init__(name="Cpu{}".format(ident), extended=extended)
        names = ["HW_PREFETCHER", "CL_PREFETCHER", "DCU_PREFETCHER", "IP_PREFETCHER"]
        cmd_opts = "-c {} -l".format(ident)
        cmd = "likwid-features"
        if likwid_base and os.path.isdir(likwid_base):
            abscmd = pjoin(likwid_base, cmd)
        if abscmd:
            for name in names:
                self.commands[name] = (abscmd, cmd_opts, r"{}\s+(\w+)".format(name), bool)

class PrefetcherInfo(PathMatchInfoGroup):
    def __init__(self, extended=False, likwid_base=None):
        super(PrefetcherInfo, self).__init__(name="PrefetcherInfo", extended=extended)
        cmd = "likwid-features"
        if likwid_base and os.path.isdir(likwid_base):
            abscmd = pjoin(likwid_base, cmd)
        else:
            abscmd = which(cmd)
        if abscmd:
            self.basepath = "/sys/devices/system/cpu/cpu*"
            self.match = r".*/cpu(\d+)$"
            self.subclass = PrefetcherInfoClass
            self.subargs = {"likwid_base" : likwid_base}

################################################################################
# Infos about the turbo frequencies (LIKWID only)
################################################################################
class TurboInfo(InfoGroup):
    def __init__(self, extended=False, likwid_base=None):
        super(TurboInfo, self).__init__(name="TurboInfo", extended=extended)
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
    def __init__(self, ident, extended=False):
        name = "Clocksource{}".format(ident)
        super(ClocksourceInfoClass, self).__init__(name=name, extended=extended)
        base = "/sys/devices/system/clocksource/clocksource{}".format(ident)
        self.files["Current"] = (pjoin(base, "current_clocksource"), r"(\s+)", str)
        if extended:
            self.files["Available"] = (pjoin(base, "available_clocksource"), r"(.+)", tostrlist)

class ClocksourceInfo(PathMatchInfoGroup):
    def __init__(self, extended=False):
        super(ClocksourceInfo, self).__init__(name="ClocksourceInfo", extended=extended)
        self.basepath = "/sys/devices/system/clocksource/clocksource*"
        self.match = r".*/clocksource(\d+)$"
        self.subclass = ClocksourceInfoClass

################################################################################
# Infos about the executable (if given on cmdline)
################################################################################
class ExecutableInfoExec(InfoGroup):
    def __init__(self, executable, extended=False):
        super(ExecutableInfoExec, self).__init__(name="ExecutableInfo", extended=extended)
        self.executable = executable
        abspath = get_abspath(self.executable)
        self.constants = {"Name" : str(self.executable),
                          "Abspath" : abspath,
                          "Size" : psize(abspath)}
        if extended:
            self.constants["MD5sum"] = ExecutableInfoExec.getmd5sum(abspath)
    @staticmethod
    def getmd5sum(filename):
        hash_md5 = hashlib.md5()
        with open(filename, "rb") as md5fp:
            for chunk in iter(lambda: md5fp.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

class ExecutableInfoLibraries(InfoGroup):
    def __init__(self, executable, extended=False):
        super(ExecutableInfoLibraries, self).__init__(name="LinkedLibraries", extended=extended)
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
        self._data = libdict

class ExecutableInfo(MultiClassInfoGroup):
    def __init__(self, executable, extended=False):
        super(ExecutableInfo, self).__init__(extended=extended)
        self.name = "ExecutableInfo"
        self.executable = executable
        self.classlist = [ExecutableInfoExec, ExecutableInfoLibraries]
        self.classargs = {"executable" : self.executable}

################################################################################
# Infos about the temperature using coretemp
################################################################################
class CoretempInfoHwmonClass(InfoGroup):
    def __init__(self, sensor, extended=False, socket=0, hwmon=0):
        super(CoretempInfoHwmonClass, self).__init__(extended=extended)
        base = "/sys/devices/platform/coretemp.{}/hwmon/hwmon{}/".format(socket, hwmon)
        self.name = process_file((pjoin(base, "temp{}_label".format(sensor)),))
        self.files["Input"] = (pjoin(base, "temp{}_input".format(sensor)), r"(\d+)", int)
        if extended:
            self.files["Critical"] = (pjoin(base, "temp{}_crit".format(sensor)), r"(\d+)", int)
            self.files["Alarm"] = (pjoin(base, "temp{}_crit_alarm".format(sensor)), r"(\d+)", int)
            self.files["Max"] = (pjoin(base, "temp{}_max".format(sensor)), r"(\d+)", int)

class CoretempInfoHwmon(PathMatchInfoGroup):
    def __init__(self, hwmon, extended=False, socket=0):
        super(CoretempInfoHwmon, self).__init__(name="Hwmon{}".format(hwmon), extended=extended)
        self.subclass = CoretempInfoHwmonClass
        self.subargs = {"socket" : socket, "hwmon" : hwmon}
        base = "/sys/devices/platform/coretemp.{}".format(socket)
        self.basepath = pjoin(base, "hwmon/hwmon{}/temp*_label".format(hwmon))
        self.match = r".*/temp(\d+)_label$"

class CoretempInfoSocket(PathMatchInfoGroup):
    def __init__(self, socket, extended=False):
        super(CoretempInfoSocket, self).__init__(name="Package{}".format(socket), extended=extended)
        self.socket = socket
        self.subargs = {"socket" : socket}
        self.subclass = CoretempInfoHwmon
        self.basepath = "/sys/devices/platform/coretemp.{}/hwmon/hwmon*".format(self.socket)
        self.match = r".*/hwmon(\d+)$"

class CoretempInfo(PathMatchInfoGroup):
    def __init__(self, extended=False):
        super(CoretempInfo, self).__init__(name="CoretempInfo", extended=extended)
        self.subclass = CoretempInfoSocket
        self.basepath = "/sys/devices/platform/coretemp.*"
        self.match = r".*/coretemp\.(\d+)$"


################################################################################
# Infos about the BIOS
################################################################################
class BiosInfo(InfoGroup):
    def __init__(self, extended=False):
        super(BiosInfo, self).__init__(name="BiosInfo", extended=extended)
        base = "/sys/devices/virtual/dmi/id"
        if pexists(base):
            self.files["BiosDate"] = (pjoin(base, "bios_date"),)
            self.files["BiosVendor"] = (pjoin(base, "bios_vendor"),)
            self.files["BiosVersion"] = (pjoin(base, "bios_version"),)
            self.files["SystemVendor"] = (pjoin(base, "sys_vendor"),)
            self.files["ProductName"] = (pjoin(base, "product_name"),)
            if pexists(pjoin(base, "product_vendor")):
                self.files["ProductVendor"] = (pjoin(base, "product_vendor"),)

################################################################################
# Infos about the thermal zones
################################################################################
class ThermalZoneInfoClass(InfoGroup):
    def __init__(self, zone, extended=False):
        name = "ThermalZone{}".format(zone)
        super(ThermalZoneInfoClass, self).__init__(name=name, extended=extended)
        base = "/sys/devices/virtual/thermal/thermal_zone{}".format(zone)
        self.files["Temperature"] = (pjoin(base, "temp"), r"(\d+)", int)
        if extended:
            self.files["Policy"] = (pjoin(base, "policy"), r"(.+)")
            avpath = pjoin(base, "available_policies")
            self.files["AvailablePolicies"] = (avpath, r"(.+)", tostrlist)

class ThermalZoneInfo(PathMatchInfoGroup):
    def __init__(self, extended=False):
        super(ThermalZoneInfo, self).__init__(name="ThermalZoneInfo", extended=extended)
        self.basepath = "/sys/devices/virtual/thermal/thermal_zone*"
        self.match = r".*/thermal_zone(\d+)$"
        self.subclass = ThermalZoneInfoClass

################################################################################
# Infos about CPU vulnerabilities
################################################################################
class VulnerabilitiesInfo(InfoGroup):
    def __init__(self, extended=False):
        super(VulnerabilitiesInfo, self).__init__(name="VulnerabilitiesInfo", extended=extended)
        base = "/sys/devices/system/cpu/vulnerabilities"
        for vfile in glob(pjoin(base, "*")):
            self.files[totitle(os.path.basename(vfile))] = (vfile,)

################################################################################
# Infos about logged in users (only count to avoid logging user names)
################################################################################
class UsersInfo(InfoGroup):
    def __init__(self, extended=False):
        super(UsersInfo, self).__init__(name="UsersInfo", extended=extended)
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
    def __init__(self, dmifile, extended=False):
        super(DmiDecodeFile, self).__init__(name="DmiDecodeFile", extended=extended)
        if pexists(dmifile):
            self.files["DmiDecode"] = (dmifile, )

################################################################################
# Infos about the CPU affinity
# Some Python versions provide a os.get_schedaffinity()
# If not available, use LIKWID (if allowed)
################################################################################
class CpuAffinity(InfoGroup):
    def __init__(self, extended=False):
        super(CpuAffinity, self).__init__(name="CpuAffinity", extended=extended)
        if "get_schedaffinity" in dir(os):
            self.constants["Affinity" : os.get_schedaffinity()]
        elif DO_LIKWID:
            abspath = get_abspath("likwid-pin")
            if len(abspath) > 0:
                self.commands["Affinity"] = (abspath, "-c N -p 2>&1", r"(.*)", tointlist)

################################################################################
# Infos about this script
################################################################################
class MachineStateVersionInfo(InfoGroup):
    def __init__(self, extended=False):
        super(MachineStateVersionInfo, self).__init__(name="MachineStateVersion", extended=extended)
        self.constants["Version"] = MACHINESTATE_VERSION

################################################################################
# Infos about loaded modules in the modules system
################################################################################
class ModulesInfo(InfoGroup):
    def __init__(self, extended=False):
        super(ModulesInfo, self).__init__(name="ModulesInfo", extended=extended)
        parse = ModulesInfo.parsemodules
        cmd_opts = "{} sh list -t 2>&1".format(MODULECMD_TCL_PATH)
        cmd = "tclsh"
        if len(get_abspath(cmd)) > 0 and pexists(MODULECMD_TCL_PATH):
            self.commands["Loaded"] = (cmd, cmd_opts, None, parse)
    @staticmethod
    def parsemodules(value):
        slist = re.split("\n", value)
        return slist[1:]

################################################################################
# Infos from nvidia-smi (Nvidia GPUs)
# TODO
################################################################################
#class NvidiaSmiInfoClass(InfoGroup):
#    def __init__(self, device, extended=False):
#        super(NvidiaSmiInfoClass, self).__init__(name="Card".format(device), extended=extended)
#        self.cmd = "nvidia-smi"
#        self.cmd_opts = "dmon -c 1 -i {}".format(device)
#        matches = [r"\s+\d+\s+(\d+)",
#                   r"\s+\d+\s+\d+\s+(\d+)",
#                   r"\s+\d+\s+\d+\s+\d+\s+([\d-]+)",
#                   r"\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+(\d+)",
#                   r"\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+(\d+)",
#                  ]
#        names = ["Power", "GpuTemp", "MemTemp", "Mclk", "Pclk"]
#        for key, regex in zip(names, matches):
#            self.commands[key] = (self.cmd, self.cmd_opts, regex, int)

################################################################################
# Infos from veosinfo (NEC Tsubasa)
# TODO
################################################################################

def read_cli():
    parser = argparse.ArgumentParser(description='Reads and outputs system information as JSON document')
    parser.add_argument('-e', '--extended', action='store_true', default=False, help='extended output (default: False)')
    parser.add_argument('-s', '--sort', action='store_true', default=False, help='sort JSON output (default: False)')
    parser.add_argument('-i', '--intend', default=4, type=int, help='intention in JSON output (default: 4)')
    parser.add_argument('-o', '--output', help='save JSON to file (default: stdout)', default=None)
    parser.add_argument('executable', help='analyze executable (optional)', nargs='?', default=None)
    pargs = vars(parser.parse_args(sys.argv[1:]))
    return pargs
    #return pargs["extended"], pargs["executable"], pargs["output"]

if __name__ == "__main__":
    cliargs = read_cli()
    mstate = MachineState(extended=cliargs["extended"],
                          executable=cliargs["executable"])
    mstate.update()
    if not cliargs["output"]:
        print(mstate.get_json(sort=cliargs["sort"], intend=cliargs["intend"]))
    else:
        with open(cliargs["output"], "w") as outfp:
            outfp.write(mstate.get_json(sort=cliargs["sort"], intend=cliargs["intend"]))
            outfp.write("\n")

#    n = CoretempInfo(extended=extended)
#    n.generate()
#    n.update()
#    print(n.get_json())
