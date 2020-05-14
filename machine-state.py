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
from glob import glob

################################################################################
# Configuration
################################################################################
DO_LIKWID=1
LIKWID_PATH=""
DMIDECODE_FILE="/etc/dmidecode.txt"
BIOS_XML_FILE=""

################################################################################
# Data types
################################################################################
class Base:
    def __init__(self):
        self.json = {}
        self.list = []
        self.subs = {}
        self.sublist = []
    def add(self, name, value):
        self.json.update({name : value})
        self.list.append(name)
    def new_sub(self, name):
        self.subs.update({name : [{}, []]})
        self.sublist.append(name)
    def add_sub(self, sub, name, value):
        self.subs[sub][0].update({name : value})
        self.subs[sub][1].append(name)
    def add_sub_multi(self, sub, cmddict):
        self.new_sub(sub)
        for k in cmddict:
            self.add_sub(sub, k, cmddict[k])
    def get(self):
        out = {}
        for k in self.list:
            out.update({k : self.json[k]})
        for sub in self.sublist:
            t = {}
            for k in self.subs[sub][1]:
                t.update({k : self.subs[sub][0][k]})
            out.update({ sub : t})
        return out
    def getjson(self):
        d = self.get()
        return json.dumps(d, sort_keys=True, indent=4)

class SysParms:
    def __init__(self):
        self.hostname = None
        self.machinetype = None
        self.kernelrelease = None
        self.kernelversion = None
        self.uptime = None
        self.osrelease = None
        self.platform = None
        self.env = None

    def _read_uname(self):
        system, node, release, version, machine, processor = platform.uname()
        if len(release) > 0:
            self.kernelrelease = release
        if len(version) > 0:
            self.kernelversion = version
        if len(machine) > 0:
            self.machinetype = machine
    def get_hostname(self):
        if not self.hostname:
            self.hostname = socket.gethostname()
        return self.hostname
    def get_machinetype(self):
        if not self.machinetype:
            self._read_uname()
        return self.machinetype
    def get_kernelversion(self):
        if not self.kernelversion:
            self._read_uname()
        return self.kernelversion
    def get_kernelrelease(self):
        if not self.kernelrelease:
            self._read_uname()
        return self.kernelrelease
    def get_platform(self):
        if not self.platform:
            self.platform = platform.platform()
        return self.platform
    def get_env(self):
        if not self.env:
            self.env = sys.environ
        return env
    def get_osrelease():
        if not self.osrelease:
            self.osrelease = read_file("/etc/os-release", parse_os_release)
        return self.osrelease


def _remove_empty_lines(string):
    if string:
        tmp = string.split("\n")
        return "\n".join([l for l in tmp if l.strip() != ''])

def read_file(filename, parser=None):
    enc = locale.getpreferredencoding()
    if not os.access(filename, os.R_OK):
        print("File '{}' not readable".format(filename))
    finput = None
    with open(filename) as fp:
        try:
            finput = fp.read()
        except:
            finput = ""
    finput = _remove_empty_lines(finput)
    if finput and parser:
        finput = parser(finput)
    return finput

def exec_cmd(command, parser=None):
    enc = locale.getpreferredencoding()
    try:
        cinput = None
        p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
        p.wait()
        if p.returncode == 0:
            cinput = p.stdout.read().decode(enc)
        else:
            print("Command '{}' returned {}".format(command, p.returncode))
        cinput = _remove_empty_lines(cinput)
        if cinput and parser:
            cinput = parser(cinput)
        return cinput
    except:
        print("Error executing command '{}'".format(command))
    return None

def check_cmd(command):
    paths = os.environ["PATH"]
    for p in paths.split(":"):
        t = os.path.join(p, command)
        if os.access(t, os.X_OK):
            return True
    return False


################################################################################
# Parsers
################################################################################
def parse_loadavg(string):
    t = string.split(" ")
    return t[:3]

def parse_os_release(string):
    t = string.split("\n")
    o = {}
    for l in t:
        m = re.match("(.*)=[\"]*(.*)[\"]*", l)
        if m:
            o.update({m.group(1) : m.group(2)})
    return o

def parse_users(string):
    return re.split("\s+", string)

def parse_true_false(string):
    if string == "1":
        return "Enabled"
    return "Disabled"

def parse_meminfo(string):
    t = {}
    fields = ["MemTotal", "MemFree", "MemAvailable", "Buffers", "Cached", "SwapTotal", "SwapFree", "HugePages_Total", "HugePages_Free"]
    for l in string.split("\n"):
        for f in fields:
            m = re.match("{}:\s*(\d+[ ]*[k]*[B]*)".format(f), l)
            if m:
                t.update({f : m.group(1)})
    return t

def parse_trans_huge_pages(string):
    m = re.search("\[(.*)\]", string)
    if m:
        return m.group(1)
    return string

################################################################################
# Fill the structure
################################################################################

#base = Base()
#base.add("Hostname", exec_cmd("hostname -f"))
#base.add("Operating System Kernel Machine", exec_cmd("uname -m"))
#base.add("Operating System Kernel Release", exec_cmd("uname -r"))
#base.add("Operating System Kernel Version", exec_cmd("uname -v"))
#base.add("Uptime", exec_cmd("uptime -p"))
#base.add("Loadavg", read_file("/proc/loadavg", parse_loadavg))
#base.add_sub_multi("Operating System Release", read_file("/etc/os-release", parse_os_release))
#base.add("Logged in users", exec_cmd("users", parse_users))
#base.add("NUMA balancing", read_file("/proc/sys/kernel/numa_balancing", parse_true_false))
#base.add_sub_multi("General memory info", read_file("/proc/meminfo", parse_meminfo))
#base.add("Transparent huge pages", read_file("/sys/kernel/mm/transparent_hugepage/enabled", parse_trans_huge_pages))
#base.add("Transparent huge pages (zero page)", read_file("/sys/kernel/mm/transparent_hugepage/use_zero_page", parse_true_false))
#base.add("Transparent huge pages (page size)", read_file("/sys/kernel/mm/transparent_hugepage/hpage_pmd_size"))
#base.add_sub_multi("Environment", exec_cmd("env", parse_os_release))

################################################################################
# Output structure
################################################################################
#print(base.getjson())

sys = SysParms()

def readable_sysfs_files_in_folder(folder):
    f = []
    for p in glob(os.path.join(folder, "*")):
        if os.path.isdir(p): continue
        if os.path.islink(p): continue
        if not os.path.isfile(p): continue
        if not os.access(p, os.R_OK): continue
        if os.path.basename(p) in ["uevent"]:
            continue
        fp = open(p)
        if not fp: continue
        try:
            fp.read()
        except:
            fp.close()
            continue
        fp.close()
        f.append(p)
    return f

def accessible_sysfs_folders_in_folder(folder, search=None):
    d = []
    for p in glob(os.path.join(folder, "*")):
        if os.path.islink(p): continue
        if os.path.isfile(p): continue
        if not os.path.isdir(p): continue
        if not os.access(p, os.R_OK|os.X_OK): continue
        if os.path.basename(p) in ["power"]:
            continue
        if search and not re.search(search, p):
            continue
        d.append(p)
    return d

def read_sysfs_cputopo():
    t = {}
    for p in accessible_sysfs_folders_in_folder("/sys/devices/system/cpu", "cpu(\d+)"):
        for f in readable_sysfs_files_in_folder(os.path.join(p, "topology")):
            t.update({f : None})
    for k in t:
        t[k] = read_file(k)
    return t



def read_sysfs_cachetopo():
    c = {}
    if os.access("/sys/devices/system/cpu/cpu0/cache/", os.R_OK|os.X_OK):
        for p in accessible_sysfs_folders_in_folder("/sys/devices/system/cpu/cpu0/cache", "index(\d+)"):
            for f in readable_sysfs_files_in_folder(p):
                c.update({f : None})
        for k in c:
            c[k] = read_file(k)
    return c

def read_sysfs_vulnerabilities():
    v = {}
    if os.access("/sys/devices/system/cpu/vulnerabilities", os.R_OK|os.X_OK):
        for p in readable_sysfs_files_in_folder("/sys/devices/system/cpu/vulnerabilities"):
            v.update( {p: None})
        for k in v:
            v[k] = read_file(k)
    return v

def read_sysfs_numatopo():
    m = {}
    if os.access("/sys/devices/system/node", os.R_OK|os.X_OK):
        for p in accessible_sysfs_folders_in_folder("/sys/devices/system/node", "node(\d+)"):
            for mf in readable_sysfs_files_in_folder(p):
                m.update( {mf: None})
            hugepages = os.path.join(p, "hugepages")

            if os.access(hugepages, os.R_OK|os.X_OK):
                for hp in accessible_sysfs_folders_in_folder(hugepages, "hugepages-([\dkKMGB]+)"):
                    for hpf in readable_sysfs_files_in_folder(hp):
                        m.update( {hpf: None})
        for k in m:
            m[k] = read_file(k)
    return m

def read_sysfs_clocksource():
    cs = {}
    if os.access("/sys/devices/system/clocksource", os.R_OK|os.X_OK):
        for p in accessible_sysfs_folders_in_folder("/sys/devices/system/clocksource", "clocksource(\d+)"):
            for csf in readable_sysfs_files_in_folder(p):
                v.update( {csf: None})
        for k in cs:
            cs[k] = read_file(k)
    return t, c, v, m, cs

def read_sysfs_coretemp():
    ct = {}
    folder = "/sys/devices/platform/coretemp.0"
    if os.access(folder, os.R_OK|os.X_OK):
        for p in accessible_sysfs_folders_in_folder(folder):
            for cp in accessible_sysfs_folders_in_folder(p):
                for cpf in readable_sysfs_files_in_folder(cp):
                    ct.update({cpf : None})
        for k in ct:
            ct[k] = read_file(k)
    return ct

def read_sysfs_powercap():
    pc = {}
    folder = "/sys/devices/virtual/powercap/intel-rapl"
    if os.access(folder, os.R_OK|os.X_OK):
        for f in readable_sysfs_files_in_folder(folder):
            pc.update({f : None})
        for p in accessible_sysfs_folders_in_folder(folder):
            for f in readable_sysfs_files_in_folder(p):
                pc.update({f : None})
            for pp in accessible_sysfs_folders_in_folder(p):
                for f in readable_sysfs_files_in_folder(pp):
                    pc.update({f : None})
        for k in pc:
            pc[k] = read_file(k)
    return pc

def read_sysfs_thermalzones():
    tz = {}
    folder = "/sys/devices/virtual/thermal"
    if os.access(folder, os.R_OK|os.X_OK):
        for p in accessible_sysfs_folders_in_folder(folder, "thermal_zone(\d+)"):
            for f in readable_sysfs_files_in_folder(p):
                tz.update({f : None})
        for k in tz:
            tz[k] = read_file(k)
    return tz

def read_sysfs_transhugepages():
    thp = {}
    folder = "/sys/kernel/mm/transparent_hugepage"
    if os.access(folder, os.R_OK|os.X_OK):
        for f in readable_sysfs_files_in_folder(p):
            thp.update({f : None})
        if os.access(os.path.join(folder, "khugepaged"), os.R_OK|os.X_OK):
            for f in readable_sysfs_files_in_folder(os.path.join(folder, "khugepaged")):
                thp.update({f : None})
        for k in thp:
            thp[k] = read_file(k)
    return thp

def read_sysfs_hugepages():
    hp = {}
    folder = "/sys/kernel/mm/hugepages"
    if os.access(folder, os.R_OK|os.X_OK):
        for hpp in accessible_sysfs_folders_in_folder(folder, "hugepages-(\d+[kKMG][B])"):
            for f in readable_sysfs_files_in_folder(hpp):
                hp.update({f : None})
        for k in hp:
            hp[k] = read_file(k)
    return hp

def read_sysfs_writeback_workqueue():
    wq = {}
    folder = "/sys/bus/workqueue/writeback"
    if os.access(folder, os.R_OK|os.X_OK):
        for f in readable_sysfs_files_in_folder(folder):
            wq.update({f : None})
        for k in wq:
            wq[k] = read_file(k)
    return wq

def read_sysfs_cgroups():
    cg = {}
    folder = "/sys/fs/cgroup/cpuset/"
    if os.access(folder, os.R_OK|os.X_OK):
        for f in readable_sysfs_files_in_folder(folder):
            if os.path.basename(f) not in ["cgroup.procs", "tasks"]:
                cg.update({f : None})
        for k in cg:
            cg[k] = read_file(k)
    return cg

def read_procfs_meminfo():
    mi = {}
    file = "/proc/meminfo"
    if os.access(file, os.R_OK):
        with open(file) as fp:
            lines = fp.read().split("\n")
            for l in lines:
                m = re.search("([\w\d_]+):\s*(\d+\s[kKMG][B])", l)
                if m:
                    mi.update({m.group(1) : m.group(2)})
    return mi

def read_procfs_vmstat():
    vm = {}
    file = "/proc/vmstat"
    if os.access(file, os.R_OK):
        with open(file) as fp:
            lines = fp.read().split("\n")
            for l in lines:
                m = re.search("([\w\d_]+)\s*(\d+)", l)
                if m:
                    vm.update({m.group(1) : m.group(2)})
    return vm

def read_procfs_numabalancing():
    nb = {}
    files = "/proc/sys/kernel/numa_balancing*"
    for f in glob(files):
        if os.access(f, os.R_OK):
            with open(f) as fp:
                nb.update({f : fp.read().strip()})
    return nb

def read_procfs_loadavg():
    load = {}
    file = "/proc/loadavg"
    if os.access(file, os.R_OK):
        with open(file) as fp:
            data = fp.read().strip()
            m = re.match("([\d+\.]+)\s+([\d+\.]+)\s+([\d+\.]+)\s+(\d+)/(\d+)\s+(\d+)", data)
            if m:
                load.update({"loadavg_1m" : m.group(1)})
                load.update({"loadavg_5m" : m.group(2)})
                load.update({"loadavg_15m" : m.group(3)})
                load.update({"run_processes" : m.group(4)})
                load.update({"all_processes" : m.group(5)})
                load.update({"last_pid" : m.group(6)})
    return load

def read_procfs_uptime():
    up = {}
    file = "/proc/uptime"
    if os.access(file, os.R_OK):
        with open(file) as fp:
            data = fp.read().strip()
            m = re.match("([\d\.]+)\s+([\d\.]+)", data)
            if m:
                up.update({"uptime" : m.group(1)})
                up.update({"cores_idle_time" : m.group(2)})
    return up

def read_procfs_hostname():
    h = {}
    f1 = "/proc/sys/kernel/hostname"
    f2 = "/proc/sys/kernel/domainname"
    if os.access(f1, os.R_OK):
        with open(f1) as fp:
            h.update({f1 : fp.read.strip()})
    if os.access(f2, os.R_OK):
        with open(f2) as fp:
            h.update({f2 : fp.read.strip()})
    return h

def read_procfs_kernel():
    u = {}
    f1 = "/proc/version"
    f2 = "/proc/cmdline"
    if os.access(f1, os.R_OK):
        with open(f1) as fp:
            u.update({f1: fp.read().strip()})
    if os.access(f2, os.R_OK):
        with open(f2) as fp:
            u.update({f2 : fp.read().strip()})
    return u

def read_procfs_modules():
    mods = {}
    file = "/proc/modules"
    if os.access(file, os.R_OK):
        with open(file) as fp:
            for l in fp.read().split("\n"):
                m = re.match("([\w\d_]+)\s+(\d+)\s+(\d+)\s+([^\s]+)", l)
                if m:
                    t = {}
                    t.update({"memory_size" : m.group(2)})
                    t.update({"instances" : m.group(3)})
                    t.update({"dependencies" : [ x for x in m.group(4).split(",") if x.strip() and x != "-"]})
                    mods.update({m.group(1) : t})
    return mods

def read_procfs_cpuinfo():
    ci = {}
    file = "/proc/cpuinfo"
    matches = ["flags", "bugs", "vendor_id", "model", "model name", "cpu family", "stepping", "clflush size", "cache_alignment"]
    if os.access(file, os.R_OK):
        with open(file) as fp:
            lines = fp.read().split("\n")
            for l in lines:
                for test in matches:
                    m = re.match("{}\s+:\s(.+)".format(test), l)
                    if m and not test in ci:
                        ci.update({test : m.group(1)})
    return ci

def read_sysfs_cpufreq():
    freq = {}
    for p in accessible_sysfs_folders_in_folder("/sys/devices/system/cpu", "cpu(\d+)"):
        for f in readable_sysfs_files_in_folder(os.path.join(p, "cpufreq")):
            freq.update({f : None})
    for k in freq:
        freq[k] = read_file(k)
    return freq

def read_etc_osrelease():
    rel = {}
    file = "/etc/os-release"
    if os.access(file, os.R_OK):
        with open(file) as fp:
            lines = fp.read().split("\n")
            for l in lines:
                m = re.match("([\w_]+)=[\"]*([^\"]+)[\"]*", l)
                if m:
                    rel.update({m.group(1) : m.group(2)})
    return rel

def read_etc_lsbrelease():
    rel = {}
    file = "/etc/lsb-release"
    if os.access(file, os.R_OK):
        with open(file) as fp:
            lines = fp.read().split("\n")
            for l in lines:
                m = re.match("([\w_]+)=[\"]*([^\"]+)[\"]*", l)
                if m:
                    rel.update({m.group(1) : m.group(2)})
    return rel

print(read_etc_lsbrelease())
