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
import os
import os.path
import locale
import subprocess
import re
import json
import socket
import platform
from copy import deepcopy
from glob import glob

################################################################################
# Configuration
################################################################################
DO_LIKWID=1
LIKWID_PATH=""
DMIDECODE_FILE="/etc/dmidecode.txt"
BIOS_XML_FILE=""

################################################################################
# Helper Functions
################################################################################

def tobool(val):
    x = False
    try:
        x = bool(val[0])
    except:
        raise("Unable to cast value '%s' to boolean".format(val))
    return x

def toint(val):
    x = 0
    try:
        x = int(val[0])
    except:
        raise("Unable to cast value '%s' to integer".format(val))
    return x

def tofloat(val):
    x = 0
    try:
        x = float(val[0])
    except:
        raise("Unable to cast value '%s' to float".format(val))
    return x

def tostrlist(val):
    x = []
    try:
        x = re.split("\s+", val[0])
    except:
        raise("Unable to cast value '%s' to strlist".format(val))
    return x

def tointlist(val):
    x = []
    try:
        for part in re.split("[,\ ]", val[0]):
            if not part.strip(): continue
            if '-' in part:
                s,e = part.split("-")
                x += [ int(i) for i in range(int(s), int(e)+1)]
            else:
                x += [int(part)]
    except:
        raise("Unable to cast value '%s' to intlist".format(val))
    return x

def read_file(filename):
    enc = locale.getpreferredencoding()
    try:
        with open(filename, "rb") as fp:
            return fp.read().decode(enc).strip()
    except:
        raise("Cannot read file '{}'".format(filename))

def totitle(val):
    x = "".join(list(val))
    s = x.title()
    if "_" in s:
        s = s.replace("_", "")
    if " " in s:
        s = s.replace(" ", "")
    return s

def mpiimplementor(val):
    x = "".join(list(val))
    if "Open MPI" in x or "OpenRTE" in x:
        return "OpenMPI"
    elif "Intel" in x and "MPI" in x:
        return "IntelMPI"
    elif "slurm" in x:
        return "Slurm"

def mpiversion(val):
    x = "".join(list(val))
    for l in x.split("\n"):
        m = re.search("(\d+\.\d+\.\d+)", l)
        if m:
            return m.group(1)
        m = re.search("Version (\d+) Update (\d+) Build (\d+) \(id: (\d+)\)", l)
        if m:
            return "{}.{}".format(m.group(1), m.group(2))

################################################################################
# Base Classes
################################################################################

class BaseInfo:
    def __init__(self, extended=False):
        self.name = None
        self.data = {}
        self.files = {}
        self.commands = {}
        self.other = {}
    def update(self):
        d = {}
        enc = locale.getpreferredencoding()
        if len(self.files) > 0:
            for key in self.files:
                val = self.files.get(key, (None, None))
                if len(val) == 3:
                    fname, fmatch, fconvert = val
                elif len(val) == 2:
                    fname, fmatch = val
                    fconvert = None
                elif len(val) == 1:
                    fname = val[0]
                    fmatch = None
                    fconvert = None
                if fname:
                    with (open(fname, "rb")) as fp:
                        if fmatch and type(fmatch) == type("str"):
                            lines = fp.read().decode(enc).strip().split("\n")
                            for l in lines:
                                    m = re.search(fmatch, l)
                                    if m:
                                        if not fconvert:
                                            d.update({key : m.group(1)})
                                        else:
                                            d.update({key : fconvert(m.groups())})
                        else:
                            d.update({key : fp.read().decode(enc).strip()})
        if len(self.commands) > 0:
            for key in self.commands:
                val = self.commands.get(key, (None, None, None))
                if len(val) == 3:
                    cmd, cmd_opts, cmatch = val
                    cconvert = None
                elif len(val) == 4:
                    cmd, cmd_opts, cmatch, cconvert = val
                elif len(val) == 2:
                    cmd, cmd_opts = val
                    cmatch = "(.*)"
                    cconvert = None
                if cmd and cmatch:
                    #val = exec_cmd_new(cmd, cmd_opts, [cmatch])
                    cmdlist = ["which {}; exit 0;".format(cmd),
                               "{} {}; exit 0;".format(cmd, cmd_opts)]
                    for c in cmdlist:
                        data = subprocess.check_output(c, stderr=subprocess.DEVNULL, shell=True).decode(enc).strip()
                    if data:
                        if cmatch:
                            m = re.search(cmatch, data)
                            if m:
                                data = m.group(1)
                        if not cconvert:
                            d.update({key : data})
                        else:
                            d.update({key : cconvert(data)})
        if len(self.other) > 0:
            for key in self.other:
                val = self.other.get(key, (None, None))
                if len(val) == 2:
                    d.update({key : val[0](val[1])})
                if len(val) == 1:
                    d.update({key : val[0]})
        #if len(d) == len(self.files)+len(self.commands):
        self.data = d
    def generate(self):
        return
    def get(self):
        return self.data
    def get_json(self):
        d = self.get()
        return json.dumps(d, sort_keys=False, indent=4)


class BaseInfoGroup():
    def __init__(self, subclass=BaseInfo, extended=False):
        self.instances = []
        self.name = None
        self.extended = extended
        self.subclass = subclass
    def generate(self):
        return
    def update(self):
        for x in self.instances:
            x.update()
    def get(self):
        d = {}
        for inst in self.instances:
            x = inst.get()
            d.update({inst.name : x})
        return d
    def get_json(self):
        d = self.get()
        return json.dumps(d, sort_keys=False, indent=4)

class MachineState():
    def __init__(self, extended=False):
        self.extended = extended
        self.additional = {}
        self.subclasses = [
            HostInfo,
            CpuInfo,
            OsInfo,
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
            SystemEnvironment,
            TurboInfo,
        ]
        self.instances = []
        for c in self.subclasses:
            self.instances.append(c(extended=extended))
    def update(self):
        for c in self.instances:
            c.generate()
            c.update()
    def get(self):
        d = {}
        for c in self.instances:
            x = c.get()
            d.update({c.name : x})
        for k in self.additional:
            d.update({k : self.additional[k]})
        return d
    def add_data(self, name, datadict):
        self.additional.update({name : datadict})
    def get_json(self):
        d = self.get()
        return json.dumps(d, sort_keys=False, indent=4)

################################################################################
# Configuration Classes
################################################################################

class OsInfo(BaseInfo):
    def __init__(self, extended=False):
        super(OsInfo, self).__init__(extended)
        self.name = "OperatingSystem"
        self.files = {"Name" : ("/etc/os-release", "NAME=[\"]*(?P<Name>[^\"]+)[\"]*"),
                      "Version" : ("/etc/os-release", "VERSION=[\"]*(?P<Version>[^\"]+)[\"]*"),
                     }
        if extended:
            self.files.update({ "URL" : ("/etc/os-release", "HOME_URL=[\"]*([^\"]+)[\"]*")})
            self.files.update({ "Codename" : ("/etc/os-release", "VERSION_CODENAME=[\"]*([^\"]+)[\"]*")})

class NumaBalance(BaseInfo):
    def __init__(self, extended=False):
        super(NumaBalance, self).__init__(extended)
        self.name = "NumaBalancing"
        self.files = {"State" : ("/proc/sys/kernel/numa_balancing", "(\d+)", tobool)}
        if extended:
            self.files.update({ "ScanDelayMs" : ("/proc/sys/kernel/numa_balancing_scan_delay_ms", "(\d+)", toint)})
            self.files.update({ "ScanPeriodMaxMs" : ("/proc/sys/kernel/numa_balancing_scan_period_max_ms", "(\d+)", toint)})
            self.files.update({ "ScanPeriodMinMs" : ("/proc/sys/kernel/numa_balancing_scan_period_min_ms", "(\d+)", toint)})
            self.files.update({ "ScanSizeMb" : ("/proc/sys/kernel/numa_balancing_scan_size_mb", "(\d+)", toint)})

class HostInfo(BaseInfo):
    def __init__(self, extended=False):
        super(HostInfo, self).__init__(extended)
        self.name = "HostInfo"
        self.commands = {"Hostname" : ("hostname", "-s", "(?P<Hostname>.*)")}
        if extended:
            self.commands.update({"Domainname" : ("hostname", "-d", "(?P<Domainname>.+)")})
            self.commands.update({"FQDN" : ("hostname", "-f", "(?P<FQDN>.+)")})

class CpuInfo(BaseInfo):
    def __init__(self, extended=False):
        super(CpuInfo, self).__init__(extended)
        self.name = "CpuInfo"
        self.files = {"Vendor" : ("/proc/cpuinfo", "vendor_id\s+:\s(?P<Vendor>.*)"),
                      "Name" : ("/proc/cpuinfo", "model name\s+:\s(?P<Name>.+)"),
                      "Family" : ("/proc/cpuinfo", "cpu family\s+:\s(?P<Family>.+)"),
                      "Model" : ("/proc/cpuinfo", "model\s+:\s(?P<Model>.+)"),
                      "Stepping" : ("/proc/cpuinfo", "stepping\s+:\s(?P<Stepping>.+)"),
                      "Variant" : ("/proc/cpuinfo", "variant\s+:\s(?P<Variant>.+)"),
                     }
        if extended:
            self.files.update({"Flags" : ("/proc/cpuinfo", "flags\s+:\s(?P<Flags>.+)", tostrlist),
                               "Bugs" : ("/proc/cpuinfo", "bugs\s+:\s(?P<Bugs>.+)", tostrlist),
                               "Microcode" : ("/proc/cpuinfo", "microcode\s+:\s(?P<Microcode>.+)"),})

class CpuTopologyClass(BaseInfo):
    def __init__(self, ident, extended=False):
        super(CpuTopologyClass, self).__init__(extended)
        self.hwthread = ident
        self.name = "cpu{}".format(self.hwthread)
        self.basepath = "/sys/devices/system/cpu/{}/topology".format(self.name)

        self.files = {"CoreId" : (os.path.join(self.basepath, "core_id"), "(\d+)", toint),
                      "PackageId" : (os.path.join(self.basepath, "physical_package_id"), "(\d+)", toint),
                     }
    def get(self):
        d = {"HWThread" : self.hwthread, "ThreadId" : 0}
        with open(os.path.join(self.basepath, "thread_siblings_list"), "rb") as fp:
            tid = 0
            enc = locale.getpreferredencoding()
            data = fp.read().decode(enc).strip()
            dlist = data.split(",")
            if len(dlist) > 1:
                tid = dlist.index(str(self.hwthread))
            else:
                dlist = data.split("-")
                if len(dlist) > 1:
                    r = range(int(dlist[0]), int(dlist[1])+1)
                    tid = r.index(self.hwthread)
            d["ThreadId"] = tid
        d.update(super(CpuTopologyClass, self).get())
        return d


class CpuTopology(BaseInfoGroup):
    def __init__(self, extended=False):
        super(CpuTopology, self).__init__(subclass=CpuTopologyClass, extended=extended)
        self.name = "CpuFrequency"
    def generate(self):
        basepath = "/sys/devices/system/cpu/cpu*"
        cpumatch = re.compile(".*/cpu(\d+)$")
        cpus = sorted([int(cpumatch.match(x).group(1)) for x in glob(basepath) if cpumatch.match(x)])
        for n in cpus:
            c = self.subclass(n, self.extended)
            c.name = "cpu{}".format(n)
            self.instances.append(c)

class CpuFrequencyClass(BaseInfo):
    def __init__(self, ident, extended=False):
        super(CpuFrequencyClass, self).__init__(extended)
        self.hwthread = ident
        self.name = "cpu{}".format(self.hwthread)
        self.basepath = "/sys/devices/system/cpu/{}/cpufreq".format(self.name)

        self.files = {"MaxFreq" : (os.path.join(self.basepath, "scaling_max_freq"), "(\d+)", toint),
                      "MinFreq" : (os.path.join(self.basepath, "scaling_min_freq"), "(\d+)", toint),
                      "Governor" : (os.path.join(self.basepath, "scaling_governor"),),
                     }



class CpuFrequency(BaseInfoGroup):
    def __init__(self, extended=False):
        super(CpuFrequency, self).__init__(subclass=CpuFrequencyClass, extended=extended)
        self.name = "CpuFrequency"
    def generate(self):
        basepath = "/sys/devices/system/cpu/cpu*"
        cpumatch = re.compile(".*/cpu(\d+)$")
        cpus = sorted([int(cpumatch.match(x).group(1)) for x in glob(basepath) if cpumatch.match(x)])
        for n in cpus:
            c = self.subclass(n, self.extended)
            c.name = "Cpu{}".format(n)
            self.instances.append(c)

class NumaInfoClass(BaseInfo):
    def __init__(self, node, extended=False):
        super(NumaInfoClass, self).__init__(extended)
        self.node = node
        self.name = "node{}".format(self.node)
        self.basepath = "/sys/devices/system/node/{}".format(self.name)
        self.files = {"MemTotal" : (os.path.join(self.basepath, "meminfo"),"Node {} MemTotal:\s+(\d+\s[kKMG][B])".format(node)),
                      "MemFree" : (os.path.join(self.basepath, "meminfo"),"Node {} MemFree:\s+(\d+\s[kKMG][B])".format(node)),
                      "MemUsed" : (os.path.join(self.basepath, "meminfo"),"Node {} MemUsed:\s+(\d+\s[kKMG][B])".format(node)),
                      "Distances" : (os.path.join(self.basepath, "distance"),"(.*)", tointlist),
                      "CpuList" : (os.path.join(self.basepath, "cpulist"),"(.*)", tointlist),
                     }
        if extended:
            self.files.update({"Writeback" : (os.path.join(self.basepath, "meminfo"),"Node {} Writeback:\s+(\d+\s[kKMG][B])".format(node)),
                               #"Cached" : (os.path.join(self.basepath, "meminfo"),"Node {} Cached:\s+(\d+\s[kKMG][B])".format(node)),
                              })
        self.sizepath = "/sys/devices/system/node/{}/hugepages/hugepages-*".format(self.name)
        self.sizematch = re.compile(".*/hugepages-(\d+[kKMG][B])$")
        self.sizes = sorted([self.sizematch.match(x).group(1) for x in glob(self.sizepath) if self.sizematch.match(x)])
        for s in self.sizes:
            p = "/sys/devices/system/node/{}/hugepages/hugepages-{}".format(self.name, s)

            self.files.update({"NrHugepages{}".format(s) : (os.path.join(p, "nr_hugepages"), "(\d+)", toint),
                               "FreeHugepages{}".format(s) : (os.path.join(p, "free_hugepages"), "(\d+)", toint),
                              })


class NumaInfo(BaseInfoGroup):
    def __init__(self, extended=False):
        super(NumaInfo, self).__init__(subclass=NumaInfoClass, extended=extended)
        self.name = "NumaInfo"
    def generate(self):
        basepath = "/sys/devices/system/node/node*"
        nodematch = re.compile(".*/node(\d+)$")
        nodes = sorted([int(nodematch.match(x).group(1)) for x in glob(basepath) if nodematch.match(x)])
        for n in nodes:
            c = self.subclass(n, self.extended)
            c.name = "Node{}".format(n)
            self.instances.append(c)

class CacheTopologyClass(BaseInfo):
    def __init__(self, ident, extended=False):
        super(CacheTopologyClass, self).__init__(extended)
        self.cache = ident
        self.name = "L{}".format(self.cache)
        self.basepath = "/sys/devices/system/cpu/cpu0/cache/index{}".format(self.cache)
        self.files = {"Size" : (os.path.join(self.basepath, "size"), "(\d+)", toint),
                      "Level" : (os.path.join(self.basepath, "level"), "(\d+)", toint),
                      "Type" : (os.path.join(self.basepath, "type"), "(.+)"),
                     }
        self.other = {"CpuList" : (self.getcpulist, self.cache)}
        if extended:
            self.files.update({"Sets" : (os.path.join(self.basepath, "number_of_sets"), "(\d+)", toint),
                               "Associativity" : (os.path.join(self.basepath, "ways_of_associativity"), "(\d+)", toint),
                               "CoherencyLineSize" : (os.path.join(self.basepath, "coherency_line_size"), "(\d+)", toint),
                               "PhysicalLineSize" : (os.path.join(self.basepath, "physical_line_partition"), "(\d+)", toint),
                              })

        #"CpuList" : (os.path.join(self.basepath, "shared_cpu_list"), "(.*)", tointlist),
    def getcpulist(self, arg):
        basepath = "/sys/devices/system/cpu/cpu*"
        cpumatch = re.compile(".*/cpu(\d+)$")
        cpus = sorted([int(cpumatch.match(x).group(1)) for x in glob(basepath) if cpumatch.match(x)])
        cpulist = []
        slist = []
        for c in cpus:
            path = "/sys/devices/system/cpu/cpu{}/cache/index{}/shared_cpu_list".format(c, self.cache)
            with open(path, "rb") as fp:
                enc = locale.getpreferredencoding()
                data = fp.read().decode(enc).strip()
                l = tointlist((data,))
                if str(l) not in slist:
                    cpulist.append(l)
                    slist.append(str(l))
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
        basepath = "/sys/devices/system/cpu/cpu0/cache/index*"
        cachematch = re.compile(".*/index(\d+)$")
        caches = sorted([int(cachematch.match(x).group(1)) for x in glob(basepath) if cachematch.match(x)])
        for n in caches:
            c = self.subclass(n, self.extended)
            c.name = "Cache{}".format(n)
            self.instances.append(c)

class Uptime(BaseInfo):
    def __init__(self, extended=False):
        super(Uptime, self).__init__(extended)
        self.name = "Uptime"
        self.files = {"Uptime" : ("/proc/uptime", "([\d\.]+)", tofloat)}
        if extended:
            self.files = {"CpusIdle" : ("/proc/uptime", "[\d\.]+\s+([\d\.]+)", tofloat)}

class LoadAvg(BaseInfo):
    def __init__(self, extended=False):
        super(LoadAvg, self).__init__(extended)
        self.name = "LoadAvg"
        self.files = {"LoadAvg1m" : ("/proc/loadavg", "([\d\.]+)", tofloat),
                      "LoadAvg5m" : ("/proc/loadavg", "[\d\.]+\s+([\d+\.]+)", tofloat),
                      "LoadAvg15m" : ("/proc/loadavg", "[\d\.]+\s+[\d+\.]+\s+([\d+\.]+)", tofloat),
                     }
        if extended:
            self.files.update({"RunningProcesses" : ("/proc/loadavg", "[\d+\.]+\s+[\d+\.]+\s+[\d+\.]+\s+(\d+)", toint),
                               "AllProcesses" : ("/proc/loadavg", "[\d+\.]+\s+[\d+\.]+\s+[\d+\.]+\s+\d+/(\d+)", toint),
                              })

class MemInfo(BaseInfo):
    def __init__(self, extended=False):
        super(MemInfo, self).__init__(extended)
        self.name = "MemInfo"
        self.files = {"MemTotal" : ("/proc/meminfo","MemTotal:\s+(\d+\s[kKMG][B])"),
                      "MemFree" : ("/proc/meminfo","MemFree:\s+(\d+\s[kKMG][B])"),
                      "MemAvailable" : ("/proc/meminfo","MemAvailable:\s+(\d+\s[kKMG][B])"),
                      "SwapTotal" : ("/proc/meminfo","SwapTotal:\s+(\d+\s[kKMG][B])"),
                      "SwapFree" : ("/proc/meminfo","SwapFree:\s+(\d+\s[kKMG][B])"),
                     }
        if extended:
            self.files.update({"Buffers" : ("/proc/meminfo","Buffers:\s+(\d+\s[kKMG][B])"),
                               "Cached" : ("/proc/meminfo","Cached:\s+(\d+\s[kKMG][B])"),
                              })

class KernelInfo(BaseInfo):
    def __init__(self, extended=False):
        super(KernelInfo, self).__init__(extended)
        self.name = "KernelInfo"
        self.files = {"Version" : ("/proc/sys/kernel/osrelease",),
                      "CmdLine" : ("/proc/cmdline",),
                     }

class CgroupInfo(BaseInfo):
    def __init__(self, extended=False):
        super(CgroupInfo, self).__init__(extended)
        self.name = "Cgroups"
        self.files = {"CPUs" : ("/sys/fs/cgroup/cpuset/cpuset.cpus", "(.*)", tointlist),
                      "Mems" : ("/sys/fs/cgroup/cpuset/cpuset.mems", "(.*)", tointlist),
                     }
        if extended:
            self.files.update({"CPUs.effective" : ("/sys/fs/cgroup/cpuset/cpuset.effective_cpus", "(.*)", tointlist),
                               "Mems.effective" : ("/sys/fs/cgroup/cpuset/cpuset.effective_mems", "(.*)", tointlist),
                              })

class Writeback(BaseInfo):
    def __init__(self, extended=False):
        super(Writeback, self).__init__(extended)
        self.name = "Writeback"
        self.files = {"CPUmask" : ("/sys/bus/workqueue/devices/writeback/cpumask", "(.*)"),
                      "MaxActive" : ("/sys/bus/workqueue/devices/writeback/max_active", "(\d+)", toint),
                     }

class TransparentHugepages(BaseInfo):
    def __init__(self, extended=False):
        super(TransparentHugepages, self).__init__(extended)
        self.name = "TransparentHugepages"
        self.files = {"State" : ("/sys/kernel/mm/transparent_hugepage/enabled", ".*\[(.*)\].*"),
                      "UseZeroPage" : ("/sys/kernel/mm/transparent_hugepage/use_zero_page", "(\d*)", tobool),
                     }



class PowercapInfoClass(BaseInfo):
    def __init__(self, socket, ident, extended=False):
        super(PowercapInfoClass, self).__init__(extended)
        self.socket = socket
        self.domain = ident
        path = "/sys/devices/virtual/powercap/intel-rapl/intel-rapl:{}/intel-rapl:{}:{}".format(self.socket, self.socket, self.domain)
        self.name = totitle(read_file(os.path.join(path, "name")))
        self.files = {"Enabled" : (os.path.join(path, "enabled"), "(\d+)", tobool)}
        for p in glob(os.path.join(path, "constraint_*_name")):
            i = re.match(".*/constraint_(\d+)_name", p).group(1)
            self.files.update({"Constraint{}_Name".format(i) : (os.path.join(path, "constraint_{}_name".format(i)), "(.+)", totitle),
                               "Constraint{}_PowerLimitUw".format(i) : (os.path.join(path, "constraint_{}_power_limit_uw".format(i)), "(\d+)", toint),
                               "Constraint{}_TimeWindowUs".format(i) : (os.path.join(path, "constraint_{}_time_window_us".format(i)), "(\d+)", toint),
                              })


class PowercapInfoPackage(BaseInfoGroup):
    def __init__(self, socket, extended=False):
        super(PowercapInfoPackage, self).__init__(subclass=PowercapInfoClass, extended=extended)
        self.name = "PowercapInfoPackage"
        self.extended = extended
        self.socket = socket
    def generate(self):
        base = "/sys/devices/virtual/powercap/intel-rapl/intel-rapl:{}".format(self.socket)
        search = os.path.join(base, "intel-rapl:{}:*".format(self.socket))
        domainmatch = re.compile(".*/intel-rapl\:\d+:(\d+)")
        enc = locale.getpreferredencoding()
        domains = sorted([ int(domainmatch.match(f).group(1)) for f in glob(search) if domainmatch.match(f) ])
        for p in domains:
            c = self.subclass(self.socket, p, extended=self.extended)
            c.generate()
            self.instances.append(c)


class PowercapInfo(BaseInfoGroup):
    def __init__(self, extended=False):
        super(PowercapInfo, self).__init__(subclass=PowercapInfoPackage, extended=extended)
        self.name = "PowercapInfo"
    def generate(self):
        base = "/sys/devices/virtual/powercap/intel-rapl/intel-rapl:*"
        packmatch = re.compile(".*/intel-rapl\:(\d+)")
        packages = sorted([ int(packmatch.match(f).group(1)) for f in glob(base) if packmatch.match(f) ])
        for p in packages:
            c = self.subclass(p, extended=self.extended)
            c.name = "Package{}".format(p)
            c.generate()
            self.instances.append(c)

class Hugepages(BaseInfo):
    def __init__(self, extended=False):
        super(Hugepages, self).__init__(extended)
        self.name = "Hugepages"
        base = "/sys/kernel/mm/hugepages"
        search = os.path.join(base, "hugepages-*")
        sizematch = re.compile(".*/hugepages-(\d+[kKMG][B])")
        sizes = [ sizematch.match(f).group(1) for f in glob(search) if sizematch.match(f) ]
        for s in sizes:
            p = os.path.join(base, "hugepages-{}".format(s))
            self.files.update({"NrHugepages{}".format(s) : (os.path.join(p, "nr_hugepages"), "(\d+)", toint),
                               "FreeHugepages{}".format(s) : (os.path.join(p, "free_hugepages"), "(\d+)", toint),
                               "ReservedHugepages{}".format(s) : (os.path.join(p, "resv_hugepages"), "(\d+)", toint),
                              })

def get_abspath(cmd):
    x = "".join(list(cmd))
    enc = locale.getpreferredencoding()
    try:
        data = subprocess.check_output("which {}; exit 0".format(x), stderr=subprocess.DEVNULL, shell=True).decode(enc).strip()
        return data
    except:
        raise("Cannot expand filepath of '{}'".format(x))

class CompilerInfoClass(BaseInfo):
    def __init__(self, executable, extended=False):
        super(CompilerInfoClass, self).__init__(extended)
        self.name = totitle(executable)
        self.commands = {"Version" : (executable, "--version", ".*(\d+\.\d+\.\d+).*", None)}
        if extended:
            self.other = {"Path" : (get_abspath, executable)}


class CCompilerInfo(BaseInfoGroup):
    def __init__(self, extended=False):
        super(CCompilerInfo, self).__init__(subclass=CompilerInfoClass, extended=extended)
        self.name = "CompilerInfo_C"
        compilerlist = ["gcc", "icc", "clang", "pgcc", "xlc", "armclang"]
        if "CC" in os.environ:
            cc = os.environ["CC"]
            if cc not in compilerlist:
                compilerlist.append(cc)
        for comp in compilerlist:
            if len(get_abspath(comp)) > 0:
                c = self.subclass(comp, extended=extended)
                self.instances.append(c)

class CPlusCompilerInfo(BaseInfoGroup):
    def __init__(self, extended=False):
        super(CPlusCompilerInfo, self).__init__(subclass=CompilerInfoClass, extended=extended)
        self.name = "CompilerInfo_C++"
        compilerlist = ["g++", "icpc", "clang++", "pg++", "armclang++"]
        if "CXX" in os.environ:
            cc = os.environ["CXX"]
            if cc not in compilerlist:
                compilerlist.append(cc)
        for comp in compilerlist:
            if len(get_abspath(comp)) > 0:
                c = self.subclass(comp, extended=extended)
                self.instances.append(c)

class FortranCompilerInfo(BaseInfoGroup):
    def __init__(self, extended=False):
        super(FortranCompilerInfo, self).__init__(subclass=CompilerInfoClass, extended=extended)
        self.name = "CompilerInfo_Fortran"
        compilerlist = ["gfortran", "ifort", "flang", "pgf90", "armflang"]
        if "FC" in os.environ:
            cc = os.environ["FC"]
            if cc not in compilerlist:
                compilerlist.append(cc)
        for comp in compilerlist:
            if len(get_abspath(comp)) > 0:
                c = self.subclass(comp, extended=extended)
                self.instances.append(c)

class MpiInfoClass(BaseInfo):
    def __init__(self, executable, extended=False):
        super(MpiInfoClass, self).__init__(extended)
        self.name = totitle(executable)
        self.commands = {"Version" : (executable, "--version", "(.*)", mpiversion),
                         "Implementor" : (executable, "--version", "(.*)", mpiimplementor)
                        }

        if extended:
            self.other = {"Path" : (get_abspath, executable)}

class MpiInfo(BaseInfoGroup):
    def __init__(self, extended=False):
        super(MpiInfo, self).__init__(subclass=MpiInfoClass, extended=extended)
        self.name = "MpiInfo"
        mpilist = ["mpiexec", "mpiexec.hydra", "mpirun", "srun"]
        for mpi in mpilist:
            if len(get_abspath(mpi)) > 0:
                c = self.subclass(mpi, extended=extended)
                self.instances.append(c)

class SystemEnvironment(BaseInfo):
    def __init__(self, extended=False):
        super(SystemEnvironment, self).__init__(extended)
        self.name = "SystemEnvironment"
    def update(self):
        d = {}
        for k in os.environ:
            d.update({k : os.environ[k]})
        self.data = d

class PrefetcherInfoClass(BaseInfo):
    def __init__(self, ident, extended=False):
        super(PrefetcherInfoClass, self).__init__(extended)
        self.name = "Cpu{}".format(ident)
        self.commands = {"HW_PREFETCHER" : ("likwid-features", "-c {} -l".format(ident), "HW_PREFETCHER\s+(\w+)", tobool),
                         "CL_PREFETCHER" : ("likwid-features", "-c {} -l".format(ident), "CL_PREFETCHER\s+(\w+)", tobool),
                         "DCU_PREFETCHER" : ("likwid-features", "-c {} -l".format(ident), "DCU_PREFETCHER\s+(\w+)", tobool),
                         "IP_PREFETCHER" : ("likwid-features", "-c {} -l".format(ident), "IP_PREFETCHER\s+(\w+)", tobool),
        }

class PrefetcherInfo(BaseInfoGroup):
    def __init__(self, extended=False):
        super(PrefetcherInfo, self).__init__(subclass=PrefetcherInfoClass, extended=extended)
        self.name = "PrefetcherInfo"
        self.extended = extended
    def generate(self):
        basepath = "/sys/devices/system/cpu/cpu*"
        cpumatch = re.compile(".*/cpu(\d+)$")
        cpus = sorted([int(cpumatch.match(x).group(1)) for x in glob(basepath) if cpumatch.match(x)])
        for c in cpus:
            x = self.subclass(c, extended=self.extended)
            self.instances.append(x)

class TurboInfo:
    def __init__(self, extended=False):
        self.data = {}
        self.name = "TurboInfo"
        self.extended = extended
        self.cmd = "likwid-powermeter"
        self.cmd_opts = "-i"
    def generate(self):
        return
    def update(self):
        d = {}
        enc = locale.getpreferredencoding()
        cmdlist = ["which {}; exit 0;".format(self.cmd),
                   "{} {}; exit 0;".format(self.cmd, self.cmd_opts)]
        for c in cmdlist:
            data = subprocess.check_output(c, stderr=subprocess.DEVNULL, shell=True).decode(enc).strip()
        if data:
            lines = data.split("\n")
            for l in lines:
                m = re.match("C(\d+) ([\d\.]+ MHz)", l)
                if m:
                    active = int(m.group(1))
                    freq = m.group(2)
                    d.update({"{}CoresActive".format(active+1) : freq})
        self.data = d
    def get(self):
        return self.data
    def get_json(self):
        d = self.get()
        return json.dumps(d, sort_keys=False, indent=4)


if __name__ == "__main__":
    ms = MachineState(extended=True)
    ms.update()
    if len(sys.argv) == 2:
        d = {"Path" : get_abspath(sys.argv[1]), "Executable" : sys.argv[1]}
        enc = locale.getpreferredencoding()
        libs = {}
        data = subprocess.check_output("ldd {}".format(sys.argv[1]), stderr=subprocess.DEVNULL, shell=True).decode(enc).strip()
        for l in data.split("\n"):
            m = re.match("\s+([^\s]+)\s+=>\s+([^\s]+)\s+.*", l)
            if m:
                libs.update({m.group(1) : m.group(2)})
        if len(libs) > 0:
            d.update({"Libraries" : libs})
        ms.add_data("Executable", d)
    print(ms.get_json())
