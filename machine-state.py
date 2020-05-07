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

import sys
import os
import os.path
import locale
import subprocess
import re
import json

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
        finput = fp.read()
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

base = Base()
base.add("Hostname", exec_cmd("hostname -f"))
base.add("Operating System Kernel Machine", exec_cmd("uname -m"))
base.add("Operating System Kernel Release", exec_cmd("uname -r"))
base.add("Operating System Kernel Version", exec_cmd("uname -v"))
base.add("Uptime", exec_cmd("uptime -p"))
base.add("Loadavg", read_file("/proc/loadavg", parse_loadavg))
base.add_sub_multi("Operating System Release", read_file("/etc/os-release", parse_os_release))
base.add("Logged in users", exec_cmd("users", parse_users))
base.add("NUMA balancing", read_file("/proc/sys/kernel/numa_balancing", parse_true_false))
base.add_sub_multi("General memory info", read_file("/proc/meminfo", parse_meminfo))
base.add("Transparent huge pages", read_file("/sys/kernel/mm/transparent_hugepage/enabled", parse_trans_huge_pages))
base.add("Transparent huge pages (zero page)", read_file("/sys/kernel/mm/transparent_hugepage/use_zero_page", parse_true_false))
base.add("Transparent huge pages (page size)", read_file("/sys/kernel/mm/transparent_hugepage/hpage_pmd_size"))
base.add_sub_multi("Environment", exec_cmd("env", parse_os_release))

################################################################################
# Output structure
################################################################################
print(base.getjson())
