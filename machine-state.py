#!/usr/bin/env python3

# =======================================================================================
#
#      Filename:  machine-state.py
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

# kein - in Dateinamen
# Fill structure als Klasse
# Base ist ein doofer Name
# nicht None zurück sondern ein raise
# pathlib.path ?

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

################################################################################
# Configuration
################################################################################
DO_LIKWID = 1
LIKWID_PATH = ""
DMIDECODE_FILE = "/etc/dmidecode.txt"
BIOS_XML_FILE = ""

################################################################################
# Constants
################################################################################
ENCODING = getpreferredencoding()

################################################################################
# Helper Functions
################################################################################


def tostrlist(value):
    outlist = []
    try:
        outlist = re.split(r"\s+", value)
    except Exception:
        raise ValueError("Unable to cast value '{}' to strlist".format(value))
    return outlist

def tointlist(value):
    outlist = []
    try:
        for part in [x for x in re.split(r"[,\ ]", value) if x.strip()]:
            if '-' in part:
                start, end = part.split("-")
                outlist += [int(i) for i in range(int(start), int(end)+1)]
            else:
                outlist += [int(part)]
    except Exception:
        raise ValueError("Unable to cast value '{}' to intlist".format(value))
    return outlist

def read_file(filename):
    try:
        with open(filename, "rb") as fptr:
            return fptr.read().decode(ENCODING).strip()
    except Exception as excep:
        raise excep

def totitle(value):
    return value.title().replace("_", "").replace(" ", "")

def get_abspath(cmd):
    data = ""
    try:
        rawdata = check_output("which {}; exit 0".format(cmd), stderr=DEVNULL, shell=True)
        data = rawdata.decode(ENCODING).strip()
    except:
        raise Exception("Cannot expand filepath of '{}'".format(cmd))
    return data

def process_file(args):
    data = None
    fname, *matchconvert = args
    if fname and pexists(fname):
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
        which = "which {}; exit 0;".format(cmd)
        data = check_output(which, stderr=DEVNULL, shell=True).decode(ENCODING).strip()
        if data and len(data) > 0:
            if optsmatchconvert:
                cmd_opts, *matchconvert = optsmatchconvert
                exe = "{} {}; exit 0;".format(cmd, cmd_opts)
                data = check_output(exe, stderr=DEVNULL, shell=True).decode(ENCODING).strip()
                cmatch, *convert = matchconvert
                if cmatch:
                    mat = re.search(cmatch, data)
                    if mat:
                        data = mat.group(1)
                if convert:
                    cconvert, = convert
                    if cconvert:
                        data = cconvert(data)
    return data

def process_function(args):
    data = None
    func, *funcargs = args
    if func:
        if funcargs:
            fargs, = funcargs
            data = func(fargs)
        else:
            data = func()
    return data

################################################################################
# Base Classes
################################################################################

class BaseInfo:
    def __init__(self, name=None, extended=False):
        self.extended = extended
        self.name = name
        self.data = {}
        self.files = {}
        self.commands = {}
        self.functions = {}
        self.constants = {}

    def update(self):
        outdict = {}
        if len(self.files) > 0:
            for key in self.files:
                val = self.files.get(key, (None,))
                fdata = process_file(val)
                outdict[key] = fdata
        if len(self.commands) > 0:
            for key in self.commands:
                val = self.commands.get(key, (None,))
                cdata = process_cmd(val)
                outdict[key] = cdata
        if len(self.functions) > 0:
            for key in self.functions:
                val = self.functions.get(key, (None,))
                mdata = process_function(val)
                outdict[key] = mdata
        if len(self.constants) > 0:
            for key in self.constants:
                outdict[key] = self.constants[key]
        #if len(d) == len(self.files)+len(self.commands):
        self.data = outdict
    def generate(self):
        pass
    def get(self):
        return self.data
    def get_json(self):
        outdict = self.get()
        return json.dumps(outdict, sort_keys=False, indent=4)


class BaseInfoGroup():
    def __init__(self, subclass=BaseInfo, name=None, extended=False):
        self.instances = []
        self.name = name
        self.extended = extended
        self.subclass = subclass
    def generate(self):
        pass
    def update(self):
        for inst in self.instances:
            inst.update()
    def get(self):
        outdict = {}
        for inst in self.instances:
            clsout = inst.get()
            outdict.update({inst.name : clsout})
        return outdict
    def get_json(self):
        outdict = self.get()
        return json.dumps(outdict, sort_keys=False, indent=4)

class MachineState():
    def __init__(self, extended=False):
        self.extended = extended
        self.additional = {}
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
            CCompilerInfo,
            CPlusCompilerInfo,
            FortranCompilerInfo,
            MpiInfo,
            ShellEnvironment,
            TurboInfo,
            PythonInfo,
            ClocksourceInfo,
        ]
        self.instances = []
        for cls in self.subclasses:
            self.instances.append(cls(extended=extended))
    def update(self):
        for inst in self.instances:
            inst.generate()
            inst.update()
    def get(self):
        outdict = {}
        for inst in self.instances:
            clsout = inst.get()
            outdict.update({inst.name : clsout})
        for k in self.additional:
            outdict.update({k : self.additional[k]})
        return outdict
    def add_data(self, name, datadict):
        self.additional.update({name : datadict})
    def get_json(self):
        outdict = self.get()
        return json.dumps(outdict, sort_keys=False, indent=4)

################################################################################
# Configuration Classes
################################################################################

class OSInfo(BaseInfo):
    def __init__(self, extended=False):
        super(OSInfo, self).__init__(name="OperatingSystemInfo", extended=extended)
        self.files = {"Name" : ("/etc/os-release", "NAME=[\"]*(?P<Name>[^\"]+)[\"]*"),
                      "Version" : ("/etc/os-release", "VERSION=[\"]*(?P<Version>[^\"]+)[\"]*"),
                     }
        if extended:
            self.files["URL"] = ("/etc/os-release", "HOME_URL=[\"]*([^\"]+)[\"]*")
            self.files["Codename"] = ("/etc/os-release", "VERSION_CODENAME=[\"]*([^\"]+)[\"]*")

class NumaBalance(BaseInfo):
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

class HostInfo(BaseInfo):
    def __init__(self, extended=False):
        super(HostInfo, self).__init__(name="HostInfo", extended=extended)
        self.commands = {"Hostname" : ("hostname", "-s", r"(.+)")}
        if extended:
            self.commands.update({"Domainname" : ("hostname", "-d", r"(.+)")})
            self.commands.update({"FQDN" : ("hostname", "-f", r"(.+)")})

class CpuInfo(BaseInfo):
    def __init__(self, extended=False):
        super(CpuInfo, self).__init__(name="CpuInfo", extended=extended)
        if platform.machine() in ["x86_64", "i386"]:
            self.files = {"Vendor" : ("/proc/cpuinfo", r"vendor_id\s+:\s(.*)"),
                          "Name" : ("/proc/cpuinfo", r"model name\s+:\s(.+)"),
                          "Family" : ("/proc/cpuinfo", r"cpu family\s+:\s(.+)"),
                          "Model" : ("/proc/cpuinfo", r"model\s+:\s(.+)"),
                          "Stepping" : ("/proc/cpuinfo", r"stepping\s+:\s(.+)"),
                         }
        elif platform.machine() in ["armv7", "amdv8"]:
            self.files = {"Vendor" : ("/proc/cpuinfo", r"CPU implementer\s+:\s(.*)"),
                          "Name" : ("/proc/cpuinfo", r"model name\s+:\s(.+)"),
                          "Family" : ("/proc/cpuinfo", r"CPU architecture\s+:\s(.+)"),
                          "Model" : ("/proc/cpuinfo", r"CPU variant\s+:\s(.+)"),
                          "Stepping" : ("/proc/cpuinfo", r"CPU revision\s+:\s(.+)"),
                          "Variant" : ("/proc/cpuinfo", r"CPU part\s+:\s(.+)"),
                         }
        elif platform.machine() in ["power"]:
            self.files = {"Vendor" : ("/proc/cpuinfo", r"vendor_id\s+:\s(.*)"),
                          "Name" : ("/proc/cpuinfo", r"model name\s+:\s(.+)"),
                          "Family" : ("/proc/cpuinfo", r"cpu family\s+:\s(.+)"),
                          "Model" : ("/proc/cpuinfo", r"model\s+:\s(.+)"),
                          "Stepping" : ("/proc/cpuinfo", r"stepping\s+:\s(.+)"),
                         }
        if extended:
            self.files.update({"Flags" : ("/proc/cpuinfo", r"flags\s+:\s(.+)", tostrlist),
                               "Bugs" : ("/proc/cpuinfo", r"bugs\s+:\s(.+)", tostrlist),
                               "Microcode" : ("/proc/cpuinfo", r"microcode\s+:\s(.+)"),})

class CpuTopologyClass(BaseInfo):
    def __init__(self, ident, extended=False):
        super(CpuTopologyClass, self).__init__(name="Cpu{}".format(ident), extended=extended)
        base = "/sys/devices/system/cpu/cpu{}/topology".format(ident)
        self.files = {"CoreId" : (pjoin(base, "core_id"), r"(\d+)", int),
                      "PackageId" : (pjoin(base, "physical_package_id"), r"(\d+)", int),
                     }
        self.constants = {"HWThread" : ident}
        self.functions = {"ThreadId" : (CpuTopologyClass.getthreadid, ident)}

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


class CpuTopology(BaseInfoGroup):
    def __init__(self, extended=False):
        super(CpuTopology, self).__init__(subclass=CpuTopologyClass, extended=extended)
        self.name = "CpuTopology"
    def generate(self):
        basepath = "/sys/devices/system/cpu/cpu*"
        cmat = re.compile(r".*/cpu(\d+)$")
        cpus = sorted([int(cmat.match(x).group(1)) for x in glob(basepath) if cmat.match(x)])
        for cpu in cpus:
            cls = self.subclass(ident=cpu, extended=self.extended)
            cls.name = "cpu{}".format(cpu)
            self.instances.append(cls)

class CpuFrequencyClass(BaseInfo):
    def __init__(self, ident, extended=False):
        super(CpuFrequencyClass, self).__init__(name="Cpu{}".format(ident), extended=extended)
        self.hwthread = ident
        base = "/sys/devices/system/cpu/cpu{}/cpufreq".format(self.hwthread)

        self.files = {"MaxFreq" : (pjoin(base, "scaling_max_freq"), r"(\d+)", int),
                      "MinFreq" : (pjoin(base, "scaling_min_freq"), r"(\d+)", int),
                      "Governor" : (pjoin(base, "scaling_governor"),),
                     }



class CpuFrequency(BaseInfoGroup):
    def __init__(self, extended=False):
        super(CpuFrequency, self).__init__(subclass=CpuFrequencyClass, extended=extended)
        self.name = "CpuFrequency"
    def generate(self):
        base = "/sys/devices/system/cpu/cpu*"
        cmat = re.compile(r".*/cpu(\d+)$")
        cpus = sorted([int(cmat.match(x).group(1)) for x in glob(base) if cmat.match(x)])
        for cpu in cpus:
            cls = self.subclass(cpu, self.extended)
            self.instances.append(cls)

class NumaInfoHugepagesClass(BaseInfo):
    def __init__(self, node, size, extended=False):
        name = "Hugepages-{}".format(size)
        super(NumaInfoHugepagesClass, self).__init__(name=name, extended=extended)
        base = "/sys/devices/system/node/node{}/hugepages/hugepages-{}".format(node, size)
        self.files = {"Count" : (pjoin(base, "nr_hugepages"), r"(\d+)", int),
                      "Free" : (pjoin(base, "free_hugepages"), r"(\d+)", int),
                     }

class NumaInfoClass(BaseInfo):
    def __init__(self, node, extended=False):
        super(NumaInfoClass, self).__init__(name="Node{}".format(node), extended=extended)
        self.hugepages = []
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
            self.files["Writeback"] = (pjoin(base, "meminfo"),
                                       r"Node {} Writeback:\s+(\d+\s[kKMG][B])".format(node))
        sizepath = "/sys/devices/system/node/node{}/hugepages/hugepages-*".format(node)
        smat = re.compile(r".*/hugepages-(\d+[kKMG][B])$")
        sizes = sorted([smat.match(x).group(1) for x in glob(sizepath) if smat.match(x)])
        for size in sizes:
            cls = NumaInfoHugepagesClass(node, size)
            self.hugepages.append(cls)
    def generate(self):
        super(NumaInfoClass, self).generate()
        for cls in self.hugepages:
            cls.generate()
    def update(self):
        super(NumaInfoClass, self).update()
        for cls in self.hugepages:
            cls.update()
    def get(self):
        outdict = super(NumaInfoClass, self).get()
        for cls in self.hugepages:
            outdict.update({cls.name : cls.get()})
        return outdict

class NumaInfo(BaseInfoGroup):
    def __init__(self, extended=False):
        super(NumaInfo, self).__init__(subclass=NumaInfoClass, extended=extended)
        self.name = "NumaInfo"
    def generate(self):
        base = "/sys/devices/system/node/node*"
        nmat = re.compile(r".*/node(\d+)$")
        nodes = sorted([int(nmat.match(x).group(1)) for x in glob(base) if nmat.match(x)])
        for node in nodes:
            cls = self.subclass(node=node, extended=self.extended)
            self.instances.append(cls)

class CacheTopologyClass(BaseInfo):
    def __init__(self, ident, extended=False):
        super(CacheTopologyClass, self).__init__(name="L{}".format(ident), extended=extended)
        base = "/sys/devices/system/cpu/cpu0/cache/index{}".format(ident)
        self.files = {"Size" : (pjoin(base, "size"), r"(\d+)", int),
                      "Level" : (pjoin(base, "level"), r"(\d+)", int),
                      "Type" : (pjoin(base, "type"), r"(.+)"),
                     }
        self.functions = {"CpuList" : (CacheTopologyClass.getcpulist, ident)}
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
        if "Level" in self.data:
            self.name = "L{}".format(self.data["Level"])
            if "Type" in self.data:
                if self.data["Type"] == "Data":
                    self.name += "D"
                elif self.data["Type"] == "Instruction":
                    self.name += "I"

class CacheTopology(BaseInfoGroup):
    def __init__(self, extended=False):
        super(CacheTopology, self).__init__(subclass=CacheTopologyClass, extended=extended)
        self.name = "CacheTopology"

    def generate(self):
        base = "/sys/devices/system/cpu/cpu0/cache/index*"
        cmat = re.compile(r".*/index(\d+)$")
        caches = sorted([int(cmat.match(x).group(1)) for x in glob(base) if cmat.match(x)])
        for cache in caches:
            cls = self.subclass(cache, self.extended)
            self.instances.append(cls)

class Uptime(BaseInfo):
    def __init__(self, extended=False):
        super(Uptime, self).__init__(name="Uptime", extended=extended)
        self.files = {"Uptime" : ("/proc/uptime", r"([\d\.]+)\s+[\d\.]+", float)}
        if extended:
            self.files.update({"CpusIdle" : ("/proc/uptime", r"[\d\.]+\s+([\d\.]+)", float)})

class LoadAvg(BaseInfo):
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

class MemInfo(BaseInfo):
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

class KernelInfo(BaseInfo):
    def __init__(self, extended=False):
        super(KernelInfo, self).__init__(name="KernelInfo", extended=extended)
        self.files = {"Version" : ("/proc/sys/kernel/osrelease",),
                      "CmdLine" : ("/proc/cmdline",),
                     }

class CgroupInfo(BaseInfo):
    def __init__(self, extended=False):
        super(CgroupInfo, self).__init__(name="Cgroups", extended=extended)
        base = "/sys/fs/cgroup/cpuset"
        self.files = {"CPUs" : (pjoin(base, "cpuset.cpus"), r"(.+)", tointlist),
                      "Mems" : (pjoin(base, "cpuset.mems"), r"(.+)", tointlist),
                     }
        if extended:
            names = ["CPUs.effective", "Mems.effective"]
            files = ["cpuset.effective_cpus", "cpuset.effective_mems"]
            for key, fname in zip(names, files):
                self.files[key] = (pjoin(base, fname), r"(.+)", tointlist)


class Writeback(BaseInfo):
    def __init__(self, extended=False):
        super(Writeback, self).__init__(name="Writeback", extended=extended)
        base = "/sys/bus/workqueue/devices/writeback"
        self.files = {"CPUmask" : (pjoin(base, "cpumask"), r"(.+)"),
                      "MaxActive" : (pjoin(base, "max_active"), r"(\d+)", int),
                     }

class TransparentHugepages(BaseInfo):
    def __init__(self, extended=False):
        super(TransparentHugepages, self).__init__(name="TransparentHugepages", extended=extended)
        base = "/sys/kernel/mm/transparent_hugepage"
        self.files = {"State" : (pjoin(base, "enabled"), r".*\[(.*)\].*"),
                      "UseZeroPage" : (pjoin(base, "use_zero_page"), r"(\d+)", bool),
                     }



class PowercapInfoClass(BaseInfo):
    def __init__(self, socket, ident, extended=False):
        super(PowercapInfoClass, self).__init__(extended)
        base = "/sys/devices/virtual/powercap/intel-rapl"
        base = pjoin(base, "intel-rapl:{}/intel-rapl:{}:{}".format(socket, socket, ident))
        self.name = totitle(read_file(pjoin(base, "name")))
        self.files = {"Enabled" : (pjoin(base, "enabled"), r"(\d+)", bool)}
        for path in glob(pjoin(base, "constraint_*_name")):
            number = re.match(r".*/constraint_(\d+)_name", path).group(1)
            names = ["Constraint{}_Name".format(number),
                     "Constraint{}_PowerLimitUw".format(number),
                     "Constraint{}_TimeWindowUs".format(number)]
            files = ["constraint_{}_name".format(number),
                     "constraint_{}_power_limit_uw".format(number),
                     "constraint_{}_time_window_us".format(number)]
            funcs = [totitle, int, int]
            for key, fname, func in zip(names, files, funcs):
                self.files[key] = (pjoin(path, fname), r"(.+)", func)


class PowercapInfoPackage(BaseInfoGroup):
    def __init__(self, socket, extended=False):
        super(PowercapInfoPackage, self).__init__(subclass=PowercapInfoClass, extended=extended)
        self.name = "PowercapInfoPackage"
        self.socket = socket
    def generate(self):
        base = "/sys/devices/virtual/powercap/intel-rapl/intel-rapl:{}".format(self.socket)
        search = pjoin(base, "intel-rapl:{}:*".format(self.socket))
        dmat = re.compile(r".*/intel-rapl\:\d+:(\d+)")
        domains = sorted([int(dmat.match(f).group(1)) for f in glob(search) if dmat.match(f)])
        for dom in domains:
            cls = self.subclass(self.socket, dom, extended=self.extended)
            cls.generate()
            self.instances.append(cls)


class PowercapInfo(BaseInfoGroup):
    def __init__(self, extended=False):
        super(PowercapInfo, self).__init__(subclass=PowercapInfoPackage, extended=extended)
        self.name = "PowercapInfo"
    def generate(self):
        base = "/sys/devices/virtual/powercap/intel-rapl/intel-rapl:*"
        pmat = re.compile(r".*/intel-rapl\:(\d+)")
        packages = sorted([int(pmat.match(f).group(1)) for f in glob(base) if pmat.match(f)])
        for pack in packages:
            cls = self.subclass(pack, extended=self.extended)
            cls.name = "Package{}".format(pack)
            cls.generate()
            self.instances.append(cls)

class HugepagesClass(BaseInfo):
    def __init__(self, size, extended=False):
        name = "Hugepages-{}".format(size)
        super(HugepagesClass, self).__init__(name=name, extended=extended)
        base = "/sys/kernel/mm/hugepages/hugepages-{}".format(size)
        self.files = {"Count" : (pjoin(base, "nr_hugepages"), r"(\d+)", int),
                      "Free" : (pjoin(base, "free_hugepages"), r"(\d+)", int),
                      "Reserved" : (pjoin(base, "resv_hugepages"), r"(\d+)", int),
                     }

class Hugepages(BaseInfoGroup):
    def __init__(self, extended=False):
        super(Hugepages, self).__init__(subclass=HugepagesClass, extended=extended)
        self.name = "Hugepages"
    def generate(self):
        base = "/sys/kernel/mm/hugepages/hugepages-*"
        sizematch = re.compile(r".*/hugepages-(\d+[kKMG][B])")
        sizes = [sizematch.match(f).group(1) for f in glob(base) if sizematch.match(f)]
        for size in sizes:
            cls = self.subclass(size, extended=self.extended)
            cls.generate()
            self.instances.append(cls)



class CompilerInfoClass(BaseInfo):
    def __init__(self, executable, extended=False):
        super(CompilerInfoClass, self).__init__(extended)
        self.name = totitle(executable)
        self.commands = {"Version" : (executable, "--version", r"(\d+\.\d+\.\d+)")}
        if self.extended:
            self.functions = {"Path" : (get_abspath, executable)}


class CCompilerInfo(BaseInfoGroup):
    def __init__(self, extended=False):
        super(CCompilerInfo, self).__init__(subclass=CompilerInfoClass, extended=extended)
        self.name = "CompilerInfo_C"
        self.compilerlist = ["gcc", "icc", "clang", "pgcc", "xlc", "armclang"]
        if "CC" in os.environ:
            comp = os.environ["CC"]
            if comp not in self.compilerlist:
                self.compilerlist.append(comp)
    def generate(self):
        for comp in self.compilerlist:
            if len(get_abspath(comp)) > 0:
                cls = self.subclass(comp, extended=self.extended)
                cls.generate()
                self.instances.append(cls)

class CPlusCompilerInfo(BaseInfoGroup):
    def __init__(self, extended=False):
        super(CPlusCompilerInfo, self).__init__(subclass=CompilerInfoClass, extended=extended)
        self.name = "CompilerInfo_C++"
        self.compilerlist = ["g++", "icpc", "clang++", "pg++", "armclang++"]
        if "CXX" in os.environ:
            comp = os.environ["CXX"]
            if comp not in self.compilerlist:
                self.compilerlist.append(comp)
    def generate(self):
        for comp in self.compilerlist:
            if len(get_abspath(comp)) > 0:
                cls = self.subclass(comp, extended=self.extended)
                cls.generate()
                self.instances.append(cls)

class FortranCompilerInfo(BaseInfoGroup):
    def __init__(self, extended=False):
        super(FortranCompilerInfo, self).__init__(subclass=CompilerInfoClass, extended=extended)
        self.name = "CompilerInfo_Fortran"
        self.compilerlist = ["gfortran", "ifort", "flang", "pgf90", "armflang"]
        if "FC" in os.environ:
            comp = os.environ["FC"]
            if comp not in self.compilerlist:
                self.compilerlist.append(comp)
    def generate(self):
        for comp in self.compilerlist:
            if len(get_abspath(comp)) > 0:
                cls = self.subclass(comp, extended=self.extended)
                cls.generate()
                self.instances.append(cls)

#TODO Python2 not working
class PythonInfo(BaseInfoGroup):
    def __init__(self, extended=False):
        super(PythonInfo, self).__init__(subclass=CompilerInfoClass, extended=extended)
        self.name = "PythonInfo"
        self.interpreters = ["python2", "python3"]
    def generate(self):
        for inter in self.interpreters:
            if len(get_abspath(inter)) > 0:
                cls = self.subclass(inter, extended=self.extended)
                cls.generate()
                self.instances.append(cls)

class MpiInfoClass(BaseInfo):
    def __init__(self, executable, extended=False):
        super(MpiInfoClass, self).__init__(extended)
        self.name = totitle(executable)
        self.commands = {"Version" : (executable, "--version", r"(.+)", MpiInfoClass.mpiversion),
                         "Implementor" : (executable, "--version", r"(.+)", MpiInfoClass.mpivendor)
                        }

        if extended:
            self.functions = {"Path" : (get_abspath, executable)}

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

class MpiInfo(BaseInfoGroup):
    def __init__(self, extended=False):
        super(MpiInfo, self).__init__(subclass=MpiInfoClass, extended=extended)
        self.name = "MpiInfo"
        mpilist = ["mpiexec", "mpiexec.hydra", "mpirun", "srun"]
        for mpi in mpilist:
            if len(get_abspath(mpi)) > 0:
                cls = self.subclass(mpi, extended=extended)
                self.instances.append(cls)


class ShellEnvironment(BaseInfo):
    def __init__(self, extended=False):
        super(ShellEnvironment, self).__init__(extended)
        self.name = "ShellEnvironment"
    def update(self):
        outdict = {}
        for key in os.environ:
            outdict.update({key : os.environ[key]})
        self.data = outdict

class PrefetcherInfoClass(BaseInfo):
    def __init__(self, ident, extended=False):
        super(PrefetcherInfoClass, self).__init__(name="Cpu{}".format(ident), extended=extended)
        names = ["HW_PREFETCHER", "CL_PREFETCHER", "DCU_PREFETCHER", "IP_PREFETCHER"]
        cmd_opts = "-c {} -l".format(ident)
        for name in names:
            self.commands[name] = ("likwid-features", cmd_opts, r"{}\s+(\w+)".format(name), bool)

class PrefetcherInfo(BaseInfoGroup):
    def __init__(self, extended=False):
        super(PrefetcherInfo, self).__init__(subclass=PrefetcherInfoClass, extended=extended)
        self.name = "PrefetcherInfo"
    def generate(self):
        basepath = "/sys/devices/system/cpu/cpu*"
        cmat = re.compile(r".*/cpu(\d+)$")
        cpus = sorted([int(cmat.match(x).group(1)) for x in glob(basepath) if cmat.match(x)])
        for cpu in cpus:
            cls = self.subclass(cpu, extended=self.extended)
            cls.generate()
            self.instances.append(cls)

class TurboInfo:
    def __init__(self, extended=False):
        self.data = {}
        self.name = "TurboInfo"
        self.extended = extended
        self.cmd = "likwid-powermeter"
        self.cmd_opts = "-i"
    def generate(self):
        pass
    def update(self):
        outdict = {}
        cmdlist = ["which {}; exit 0;".format(self.cmd),
                   "{} {}; exit 0;".format(self.cmd, self.cmd_opts)]
        for cmd in cmdlist:
            data = check_output(cmd, stderr=DEVNULL, shell=True).decode(ENCODING).strip()
        if data:
            lines = data.split("\n")
            for line in lines:
                mat = re.match(r"C(\d+) ([\d\.]+ MHz)", line)
                if mat:
                    active = int(mat.group(1))
                    freq = mat.group(2)
                    outdict.update({"{}CoresActive".format(active+1) : freq})
        self.data = outdict
    def get(self):
        return self.data
    def get_json(self):
        outdict = self.get()
        return json.dumps(outdict, sort_keys=False, indent=4)

class ClocksourceInfoClass(BaseInfo):
    def __init__(self, ident, extended=False):
        name = "Clocksource{}".format(ident)
        super(ClocksourceInfoClass, self).__init__(name=name, extended=extended)
        base = "/sys/devices/system/clocksource/clocksource{}".format(ident)
        self.files = {"Available" : (pjoin(base, "available_clocksource"), r"(.+)", tostrlist),
                      "Current" : (pjoin(base, "current_clocksource"), r"(\s+)", str),
                     }

class ClocksourceInfo(BaseInfoGroup):
    def __init__(self, extended=False):
        super(ClocksourceInfo, self).__init__(subclass=ClocksourceInfoClass, extended=extended)
        self.name = "ClocksourceInfo"
    def generate(self):
        base = "/sys/devices/system/clocksource/clocksource*"
        cmat = re.compile(r".*/clocksource(\d+)$")
        clocks = sorted([int(cmat.match(x).group(1)) for x in glob(base) if cmat.match(x)])
        for clock in clocks:
            cls = self.subclass(clock, extended=self.extended)
            cls.generate()
            self.instances.append(cls)

class ExecutableInfoExec(BaseInfo):
    def __init__(self, executable, extended=False):
        super(ExecutableInfoExec, self).__init__(extended)
        self.name = "ExecutableInfo"
        self.executable = executable
        abspath = get_abspath(self.executable)
        #self.functions = {"Abspath" : (get_abspath, self.executable),}
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

class ExecutableInfoLibraries(BaseInfo):
    def __init__(self, executable, extended=False):
        super(ExecutableInfoLibraries, self).__init__(name="Libraries", extended=extended)
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
        self.data = libdict

class ExecutableInfo(BaseInfoGroup):
    def __init__(self, executable, extended=False):
        super(ExecutableInfo, self).__init__(subclass=None, extended=extended)
        self.name = "ExecutableInfo"
        self.executable = executable
    def generate(self):
        self.instances.append(ExecutableInfoExec(self.executable, extended=self.extended))
        self.instances.append(ExecutableInfoLibraries(self.executable, extended=self.extended))



if __name__ == "__main__":
    mstate = MachineState(extended=True)

    if len(sys.argv) == 2:
        mstate.subclasses.append(ExecutableInfo(sys.argv[1]))
    mstate.update()
    print(mstate.get_json())

#    ex = ExecutableInfo("hostname", extended=True)
#    ex.generate()
#    ex.update()
#    print(ex.get_json())
