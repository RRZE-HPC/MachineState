#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module provides a simple interface for collecting hardware and software settings for
documentation and reproducibility purposes.

Depends on no external module but for all features, the following applications need to be present:
- likwid-pin, likwid-features and likwid-powermeter
- nvidia-smi
- vecmd
- modules (package environment-modules)
- taskset

Provided functions:
- tostrlist: parse string with commas or spaces into list of strings
- tointlist: parse string with commas or spaces into list of integers
- tobytes: parse string with byte units (kB, MB, GB, kiB, MiB, GiB) into bytes
- tohertz: parse string with Hz unit (kHz, MHz, GHz) to Hz
- tohertzlist: parse string with commas or spaces into list of HZ values (tohertz)
- totitle: call string's totitle function and removes all spaces and underscores
- masktolist: parse bitmask to list of integers
- fopen: opens a file if it exists and is readable and returns file pointer

Provided classes:
- HostInfo
- CpuInfo
- OSInfo
- KernelInfo
- Uptime
- CpuTopology
- NumaBalance
- LoadAvg
- MemInfo
- CgroupInfo
- WritebackWorkqueue
- CpuFrequency
- NumaInfo
- CacheTopology
- TransparentHugepages
- PowercapInfo
- Hugepages
- CompilerInfo
- MpiInfo
- ShellEnvironment
- PythonInfo
- ClocksourceInfo
- CoretempInfo
- BiosInfo
- ThermalZoneInfo
- VulnerabilitiesInfo
- UsersInfo
- IrqAffinity
- CpuAffinity (uses os.get_schedaffinity(), likwid-pin or taskset)
- ModulesInfo (if modulecmd is present)
- NvidiaInfo (if nvidia-smi is present)
- NecTsubasaInfo (if vecmd is present)
- PrefetcherInfo (if likwid-features is present)
- TurboInfo (if likwid-powermeter is present)
- DmiDecodeFile (if DMIDECODE_FILE is setup properly)

The module contains more classes but all except the above ones are used only internally
"""

# =======================================================================================
#
#      Filename:  machinestate.py
#
#      Description:  Collect hardware and software settings
#
#      Author:   Thomas Gruber (né Roehl), thomas.roehl@googlemail.com
#      Project:  MachineState
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

# TODO: Should keys be available in all cases?
# TODO: More analysis by ExecutableInfo? (type, compilation info, ...)
# TODO: Add class for 'sysctl -a' ?

################################################################################
# Imports
################################################################################
import os
import sys
import re
import json
import platform
from subprocess import check_output, DEVNULL
from glob import glob
from os.path import join as pjoin
from os.path import exists as pexists
from os.path import getsize as psize
from locale import getpreferredencoding
from datetime import timedelta, datetime
import hashlib
import argparse
from copy import deepcopy
from unittest import TestCase
from shutil import which
from getpass import getuser
from grp import getgrgid

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
# call 'tclsh MODULECMD_PATH' if tclsh and MODULECMD_PATH exist.
MODULECMD_PATH = "tclsh /apps/modules/modulecmd.tcl"
# The NecTsubasaInfo class requires this path to call the vecmd command
VEOS_BASE = "/opt/nec/ve/bin"
# The NvidiaInfo class requires this path if nvidia-smi is not in $PATH
NVIDIA_PATH = "/opt/nvidia/bin"


################################################################################
# Version information
################################################################################
MACHINESTATE_VERSION = "0.3"
MACHINESTATE_SCHEMA_VERSION = "v1"
__version__ = MACHINESTATE_VERSION

################################################################################
# Constants
################################################################################
ENCODING = getpreferredencoding()

DEBUG_OUTPUT = False

################################################################################
# Helper functions
################################################################################

def fopen(filename):
    if filename is not None and pexists(filename) and os.path.isfile(filename):
        try:
            filefp = open(filename, "rb")
        except PermissionError:
            return None
        return filefp
    return None

################################################################################
# Parser Functions used in multiple places. If a parser function is used only
# in a single class, it is defined as static method in the class
################################################################################


def tostrlist(value):
    r'''Returns string split at \s and , in list of strings. Strings might not be unique in list.

    :param value: string with sub-strings

    :returns: Expanded list
    :rtype: [str]
    '''
    if value is not None:
        if isinstance(value, int):
            value = str(value)
        return re.split(r"[,\s]", value)

def tointlist(value):
    r'''Returns string split at \s and , in list of integers. Supports lists like 0,1-4,7.

    :param value: string with lists like 5,6,8 or 1-4 or 0,1-4,7
    :raises: :class:`ValueError`: Element of the list cannot be casted to type int

    :returns: Expanded list
    :rtype: [int]
    '''
    if value and isinstance(value, int):
        return [value]
    if value and isinstance(value, float):
        return [int(value)]

    if value and isinstance(value, str):
        outlist = []
        for part in [x for x in re.split(r"[,\s]", value) if x.strip()]:
            if '-' in part:
                start, end = part.split("-")
                try:
                    start = int(start)
                    end = int(end)
                except ValueError as exce:
                    raise exce
                outlist += [i for i in range(int(start), int(end)+1)]
            else:
                ipart = None
                mat = re.match(r"(\d+)\.\d+", part)
                if mat:
                    part = mat.group(1)
                try:
                    ipart = int(part)
                except ValueError as exce:
                    raise exce
                if ipart is not None:
                    outlist.append(ipart)
        return outlist
    return None

def totitle(value):
    r'''Returns titleized split (string.title()) with _ and whitespaces removed.'''
    if value and isinstance(value, str):
        return value.title().replace("_", "").replace(" ", "")
    return str(value)

def tobytes(value):
    r'''Returns a size value (XXXX kB or XXXGB) to size in bytes

    :param value: size value (XXXX kB or XXXGB)

    :returns: size in bytes
    :rtype: int
    '''
    if value and isinstance(value, int):
        return value
    if value and isinstance(value, str):
        mat = re.match(r"([\d\.]+)\s*([kKmMgG]{0,1})([i]{0,1})([bB]{0,1})", value)
        if mat is not None:
            count = int(mat.group(1))
            mult = 1024
            if mat.group(4).lower() == "b":
                if mat.group(3).lower() == "i":
                    mult = 1000
            if mat.group(2).lower() == "k":
                count *= mult
            elif mat.group(2).lower() == "m":
                count *= (mult * mult)
            elif mat.group(2).lower() == "g":
                count *= (mult * mult * mult)
            return count
        else:
            value = None
    return value

def masktolist(value):
    '''Returns a integer list with the set bits in a bitmask like 0xff

    :param value: bitmask like ff,ffffffff

    :returns: List of set bits in bitmask
    :rtype: [int]
    '''
    outlist = None
    if value is not None:
        bits = 0
        if isinstance(value, str):
            mask = str(value).replace(",", "")
            bits = len(mask) * 4
            imask = int(mask, 16)
        elif isinstance(value, int):
            imask = value
            bits = 0
            while value > 0:
                value >>= 1
                bits += 1
        outlist = []
        for bit in range(bits):
            if (1<<bit) & imask:
                outlist.append(bit)
    return outlist

def tohertz(value):
    outvalue = None
    if value is not None:
        if isinstance(value, int) or isinstance(value, float):
            outvalue = int(value)
        elif isinstance(value, str):
            mat = re.match(r"([\d\.]+)\s*([kKmMgG]*[Hh]*[z]*)", value)
            if mat:
                outvalue = float(mat.group(1))
                if mat.group(2).lower().startswith("m"):
                    #print("MegaHertz")
                    outvalue *= 1000 * 1000
                elif mat.group(2).lower().startswith("g"):
                    #print("GigaHertz")
                    outvalue *= 1000 * 1000 * 1000
                elif mat.group(2).lower() == "hz":
                    outvalue *= 1
                else:
                    # We assume all other frequencies are in kHz
                    #print("KiloHertz")
                    outvalue *= 1000
                outvalue = int(outvalue)
    #print("tohertz", type(value), value, outvalue)
    return outvalue

def tohertzlist(value):
    outlist = []
    if value and isinstance(value, int):
        return [tohertz(value)]

    if value and isinstance(value, str):
        try:
            for part in [x for x in re.split(r"[,\s]", value) if x.strip()]:
                outlist += [tohertz(part)]
        except ValueError as exce:
            raise exce
        return outlist
    return None

def tobool(value):
    if isinstance(value, int):
        return bool(value)
    elif isinstance(value, float):
        return value != 0.0
    elif isinstance(value, str):
        if re.match(r"\d+", value):
            return bool(int(value))
        elif value.lower() == "on":
            return True
        elif value.lower() == "off":
            return False
        elif value.lower() == "true":
            return True
        elif value.lower() == "false":
            return False
    return False

################################################################################
# Processing functions for entries in class attributes 'files' and 'commands'  #
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
                    except BaseException:
                        pass
        filefp.close()
    return data

def process_files(filedict):
    sortdict = {}
    outdict = {}
    for key in filedict:
        fname, fmatch, fparse, *_ = filedict[key]
        if fname not in sortdict:
            sortdict[fname] = []
        sortdict[fname].append((key, fmatch, fparse))
        outdict[key] = None
    for fname in sortdict:
        filefp = fopen(fname)
        data = None
        if filefp:
            data = filefp.read().decode(ENCODING)
            for args in sortdict[fname]:
                key, fmatch, fparse = args
                tmpdata = str(data.strip()) if data.strip() else ""
                if fmatch is not None:
                    tmpdata = match_data(tmpdata, fmatch)
                if fparse is not None:
                    try:
                        tmpdata = fparse(tmpdata)
                    except BaseException:
                        pass
                outdict[key] = tmpdata
            filefp.close()
    return outdict

def process_cmds(cmddict):
    sortdict = {}
    outdict = {}
    for key in cmddict:
        cmd, cmd_opts, cmatch, cparse, *_ = cmddict[key]
        newkey = (cmd, cmd_opts or "")
        if newkey not in sortdict:
            sortdict[newkey] = []
        sortdict[newkey].append((key, cmatch, cparse))
        outdict[key] = None
    for cmdargs in sortdict:
        cmd, cmd_opts = cmdargs
        abscmd = which(cmd)
        data = None
        if abscmd and len(abscmd) > 0:
            exestr = "LANG=C {} {}; exit 0;".format(cmd, cmd_opts)
            data = check_output(exestr, stderr=DEVNULL, shell=True).decode(ENCODING).strip()
        for args in sortdict[cmdargs]:
            key, cmatch, cparse = args
            tmpdata = data
            if tmpdata and cmatch is not None:
                tmpdata = match_data(tmpdata, cmatch)
            if cparse is not None:
                try:
                    tmpdata = cparse(tmpdata)
                except BaseException:
                    pass
            outdict[key] = tmpdata
    return outdict

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
                exe = "LANG=C {} {}; exit 0;".format(cmd, cmd_opts)
                data = check_output(exe, stderr=DEVNULL, shell=True).decode(ENCODING).strip()
                if data and len(data) >= 0 and len(matchconvert) > 0:
                    cmatch, *convert = matchconvert
                    if cmatch:
                        data = match_data(data, cmatch)
                    if convert:
                        cconvert, = convert
                        if cconvert:
                            try:
                                data = cconvert(data)
                            except BaseException:
                                pass
                else:
                    if len(matchconvert) == 2:
                        cmatch, cconvert = matchconvert
                        if cconvert:
                            try:
                                data = cconvert(None)
                            except BaseException:
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

def get_ostype():
    out = process_cmd(("uname", "-s", r"(\s+)", None))
    if out:
        return out
    return "Unknown"

################################################################################
# Base Classes
################################################################################



class InfoGroup:
    def __init__(self, name=None, extended=False, anonymous=False):
        # Holds subclasses
        self._instances = []
        # Holds the data of this class instance
        self._data = {}
        # Space for file reads
        # Key -> (filename, regex_with_one_group, convert_function)
        # If regex_with_one_group is None, the whole content of filename is passed to
        # convert_function. If convert_function is None, the output is saved as string
        self.files = {}
        # Space for commands for execution
        # Key -> (executable, exec_arguments, regex_with_one_group, convert_function)
        # If regex_with_one_group is None, the whole content of filename is passed to
        # convert_function. If convert_function is None, the output is saved as string
        self.commands = {}
        # Space for constants
        # Key -> Value
        self.constants = {}
        # Keys in the group that are required to check equality
        self.required4equal = []
        self.name = None
        if isinstance(name, str):
            self.name = name

        self.extended = False
        if isinstance(extended, bool):
            self.extended = extended

        self.anonymous = False
        if isinstance(anonymous, bool):
            self.anonymous = anonymous

    def addf(self, key, filename, match=None, parse=None, extended=False):
        """Add file to object including regex and parser"""
        self.files[key] = (filename, match, parse)
    def addc(self, key, cmd, cmd_opts=None, match=None, parse=None, extended=False):
        """Add command to object including command options, regex and parser"""
        self.commands[key] = (cmd, cmd_opts, match, parse)
    def const(self, key, value):
        """Add constant value to object"""
        self.constants[key] = value
    def required(self, *args):
        """Add item(s) to list of required fields at comparison"""
        if args:
            for arg in args:
                if isinstance(arg, list):
                    for subarg in arg:
                        if subarg not in self.required4equal:
                            self.required4equal.append(subarg)
                elif isinstance(arg, str):
                    if arg not in self.required4equal:
                        self.required4equal.append(arg)

    def generate(self):
        '''Generate subclasses, defined by derived classes'''
        pass

    def update(self):
        '''Read object's files and commands. Triggers update() of subclasses'''
        outdict = {}
        if len(self.files) > 0:
            outdict.update(process_files(self.files))
        if len(self.commands) > 0:
            outdict.update(process_cmds(self.commands))
        if len(self.constants) > 0:
            for key in self.constants:
                outdict[key] = self.constants[key]
        for inst in self._instances:
            inst.update()
        self._data.update(outdict)
    def get(self):
        """Get the object's and all subobjects' data as dict"""
        outdict = {}
        for inst in self._instances:
            clsout = inst.get()
            outdict.update({inst.name : clsout})
        outdict.update(self._data)
        return outdict
    def get_json(self, sort=False, intend=4):
        """Get the object's and all subobjects' data as JSON document (string)"""
        outdict = self.get()
        return json.dumps(outdict, sort_keys=sort, indent=intend)
    def get_config(self):
        """Get the object's and all subobjects' configuration as JSON document (string)"""
        outdict = {}
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
# This is a starting point to implement a json-schema for MachineState
#    def get_schema(self):
#        schemedict = {}
#        pdict = {}
#        clsname = self.name.lower()
#        surl = "https://rrze-hpc.github.io/MachineState/scheme/{}.schema.json".format(clsname)
#        schemedict["$schema"] = "http://json-schema.org/draft-07/schema#"
#        schemedict["$id"] = surl
#        schemedict["title"] = self.name
#        schemedict["description"] = self.name
#        schemedict["type"] = "object"
#        schemedict["required"] = list(self.required4equal)

#        for key in self.files:
#            vtype = "string"
#            itype = None
#            fname, _, parse = self.files[key]
#            if parse in [int, tobytes, tohertz]:
#                vtype == "integer"
#            if parse in [tointlist, tohertzlist, tostrlist]:
#                vtype == "array"
#                itype == "integer"
#                if parse == tostrlist:
#                    itype == "string"
#            pdict[key] = {"type" : vtype, "description" : fname}
#            if itype:
#                pdict[key]["items"] = {"type" : itype}
#        for key in self.commands:
#            vtype = "string"
#            itype = None
#            cname, _, _, parse = self.commands[key]
#            if parse in [int, tobytes, tohertz]:
#                vtype == "integer"
#            if parse in [tointlist, tohertzlist, tostrlist]:
#                vtype == "array"
#                itype == "integer"
#                if parse == tostrlist:
#                    itype == "string"
#            pdict[key] = {"type" : vtype, "description" : fname}
#            if itype:
#                pdict[key]["items"] = {"type" : itype}
#        schemedict["properties"] = pdict
#        return schemedict

    def __eq__(self, other):
        selfdict = self.get()
        tcase = TestCase()
        cname = str(self.__class__.__name__)
        if isinstance(other, str):
            if pexists(other):
                jsonfp = fopen(other)
                if jsonfp:
                    other = json.loads(jsonfp.read().decode(ENCODING))
                    jsonfp.close()
            else:
                other = json.loads(other)

        for rkey in self.required4equal:
            estr = "key '{}' for class {}".format(rkey, cname)
            if rkey in other:
                if rkey in selfdict:
                    selfval = selfdict[rkey]
                    otherval = other[rkey]
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
                                tcase.assertAlmostEqual(selfval, otherval, delta=selfval*0.2)
                            except BaseException as exce:
                                print("ERROR: Equality check failed for {} with delta +/- 20% of \
                                        state value: {}".format(estr, exce))
                                return False
                    elif selfval != otherval:
                        print("ERROR: Equality check failed for {}".format(estr))
                        return False

                else:
                    print("ERROR: Required {} not found in current state.".format(estr))
                    print("       Maybe key only available in extended mode.")
                    return False
            else:
                print("ERROR: Required {} not found in input".format(estr))
        for inst in self._instances:
            if inst.name in other:
                instout = (inst.__eq__(other[inst.name]))
                if instout is False:
                    return False
        return True
    def __class_args__(self):
        """Used by __repr__ to add class' arguments"""
        arglist = []
        arglist.append("name=\"{}\"".format(self.name))
        arglist.append("extended={}".format(self.extended))
        arglist.append("anonymous={}".format(self.anonymous))
        return arglist
    def __repr__(self):
        cls = str(self.__class__.__name__)
        args = ", ".join(self.__class_args__())
        return "{}({})".format(cls, args)

class PathMatchInfoGroup(InfoGroup):
    '''Class for matching files in a folder and create subclasses for each path'''
    def __init__(self,
                 name=None,
                 extended=False,
                 anonymous=False,
                 searchpath=None,
                 match=None,
                 subclass=None,
                 subargs={}):
        super(PathMatchInfoGroup, self).__init__(extended=extended, name=name, anonymous=anonymous)
        self.searchpath = None
        self.match = None
        self.subargs = {}
        self.subclass = None

        if searchpath and isinstance(searchpath, str):
            if os.path.exists(os.path.dirname(searchpath)):
                self.searchpath = searchpath
        if match and isinstance(match, str):
            self.match = match

        if subargs and isinstance(subargs, dict):
            self.subargs = subargs

        if subclass:
            if callable(subclass) and type(subclass) == type(InfoGroup):
                self.subclass = subclass


    def generate(self):
        glist = []
        if self.searchpath and self.match and self.subclass:
            mat = re.compile(self.match)
            base = self.searchpath
            try:
                glist += sorted([int(mat.match(f).group(1)) for f in glob(base) if mat.match(f)])
            except ValueError:
                glist += sorted([mat.match(f).group(1) for f in glob(base) if mat.match(f)])
            for item in glist:
                cls = self.subclass(item,
                                    extended=self.extended,
                                    anonymous=self.anonymous,
                                    **self.subargs)
                cls.generate()
                self._instances.append(cls)
    def get_config(self):
        outdict = super(PathMatchInfoGroup, self).get_config()
        selfdict = {}
        selfdict["Type"] = str(self.__class__.__name__)
        selfdict["ClassType"] = "PathMatchInfoGroup"
        if self.searchpath:
            selfdict["SearchPath"] = str(self.searchpath)
        if self.match:
            selfdict["Regex"] = str(self.match)
        if self.subclass:
            selfdict["SubClass"] = str(self.subclass.__name__)
        if self.subargs:
            selfdict["SubArgs"] = str(self.subargs)
        outdict["Config"] = selfdict
        for inst in self._instances:
            outdict.update({inst.name : inst.get_config()})
        return outdict
    def __class_args__(self):
        arglist = super(PathMatchInfoGroup, self).__class_args__()
        arglist.append("searchpath=\"{}\"".format(self.searchpath))
        arglist.append("match=r\"{}\"".format(self.match))
        if self.subclass:
            arglist.append("subclass={}".format(self.subclass.__name__))
        else:
            arglist.append("subclass=None")
        arglist.append("subargs={}".format(self.subargs))
        return arglist

class ListInfoGroup(InfoGroup):
    '''Class for creating subclasses based on a list given by the user. All subclasses have the same
    class type.
    '''
    def __init__(self,
                 name=None,
                 extended=False,
                 anonymous=False,
                 userlist=None,
                 subclass=None,
                 subargs=None):
        super(ListInfoGroup, self).__init__(extended=extended, name=name, anonymous=anonymous)
        self.userlist = []
        self.subclass = None
        self.subargs = {}

        if userlist and isinstance(userlist, list):
            self.userlist = userlist
        if subargs and isinstance(subargs, dict):
            self.subargs = subargs
        if subclass:
            if callable(subclass) and type(subclass) == type(InfoGroup):
                self.subclass = subclass

    def generate(self):
        if self.userlist and self.subclass:
            for item in self.userlist:
                cls = self.subclass(item,
                                    extended=self.extended,
                                    anonymous=self.anonymous,
                                    **self.subargs)
                cls.generate()
                self._instances.append(cls)
    def get_config(self):
        outdict = super(ListInfoGroup, self).get_config()
        selfdict = {}
        selfdict["Type"] = str(self.__class__.__name__)
        selfdict["ClassType"] = "ListInfoGroup"
        if self.subclass:
            selfdict["SubClass"] = str(self.subclass.__name__)
        if self.subargs:
            selfdict["SubArgs"] = str(self.subargs)
        if self.userlist:
            selfdict["List"] = str(self.userlist)
        for inst in self._instances:
            outdict.update({inst.name : inst.get_config()})
        outdict["Config"] = selfdict
        return outdict
    def __class_args__(self):
        arglist = super(ListInfoGroup, self).__class_args__()
        arglist.append("userlist={}".format(self.userlist))
        if self.subclass:
            arglist.append("subclass={}".format(self.subclass.__name__))
        else:
            arglist.append("subclass=None")
        arglist.append("subargs={}".format(self.subargs))
        return arglist

class MultiClassInfoGroup(InfoGroup):
    '''Class for creating subclasses based on a list of class types given by the user.
    '''
    def __init__(self,
                 name=None,
                 extended=False,
                 anonymous=False,
                 classlist=[],
                 classargs=[]):
        super(MultiClassInfoGroup, self).__init__(extended=extended, name=name, anonymous=anonymous)
        self.classlist = []
        self.classargs = []
        if len(classlist) == len(classargs):
            if classlist:
                valid = True
                for cls in classlist:
                    if not (callable(cls) and type(cls) == type(InfoGroup)):
                        valid = False
                        break
                if valid:
                    self.classlist = classlist
            if classargs:
                valid = True
                for cls in classargs:
                    if not isinstance(cls, dict):
                        valid = False
                        break
                    if valid:
                        self.classargs = classargs

    def generate(self):
        for cltype, clargs in zip(self.classlist, self.classargs):
            try:
                cls = cltype(extended=self.extended, anonymous=self.anonymous, **clargs)
                if cls:
                    cls.generate()
                    self._instances.append(cls)
            except BaseException as exce:
                #print("{}.generate: {}".format(cltype.__name__, exce))
                raise exce
    def get_config(self):
        outdict = super(MultiClassInfoGroup, self).get_config()
        outdict["Type"] = str(self.__class__.__name__)
        outdict["ClassType"] = "MultiClassInfoGroup"
        for cls, args in zip(self.classlist, self.classargs):
            outdict[str(cls.__name__)] = str(args)
        for inst in self._instances:
            outdict.update({inst.name : inst.get_config()})
        return outdict
    def __class_args__(self):
        arglist = super(MultiClassInfoGroup, self).__class_args__()
        cllist = [str(x.__name__) for x in self.classlist if x]
        arglist.append("classlist={}".format(cllist))
        arglist.append("classargs={}".format(self.classargs))
        return arglist

class MachineStateInfo(InfoGroup):
    def __init__(self, extended=False, anonymous=False):
        super(MachineStateInfo, self).__init__(name="MachineState",
                                               anonymous=anonymous,
                                               extended=extended)
        self.const("Extended", self.extended)
        self.const("Anonymous", self.anonymous)
        self.const("Version", MACHINESTATE_VERSION)
        self.const("SchemaVersion", MACHINESTATE_SCHEMA_VERSION)
        self.const("Timestamp", datetime.now().ctime())
        self.required("SchemaVersion", "Extended", "Anonymous")

class MachineState(MultiClassInfoGroup):
    '''Main MachineState Class spawning all configuration specific subclasses'''
    def __init__(self,
                 extended=False,
                 executable=None,
                 anonymous=False,
                 debug=DEBUG_OUTPUT,
                 dmifile=DMIDECODE_FILE,
                 likwid_enable=DO_LIKWID,
                 likwid_path=LIKWID_PATH,
                 nvidia_path=NVIDIA_PATH,
                 modulecmd=MODULECMD_PATH,
                 vecmd_path=VEOS_BASE):
        super(MachineState, self).__init__(extended=extended, anonymous=anonymous)
        ostype = get_ostype()
        if ostype == "Linux":
            self.classlist = [
                MachineStateInfo,
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
                WritebackWorkqueue,
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
            ]
            if extended:
                self.classlist.append(IrqAffinity)
            self.classargs = [{} for x in self.classlist]

            self.classlist.append(ModulesInfo)
            self.classargs.append({"modulecmd" : modulecmd})
            self.classlist.append(NvidiaSmiInfo)
            self.classargs.append({"nvidia_path" : nvidia_path})
            self.classlist.append(NecTsubasaInfo)
            self.classargs.append({"vecmd_path" : vecmd_path})
            self.classlist.append(DmiDecodeFile)
            self.classargs.append({"dmifile" : dmifile})
            self.classlist.append(ExecutableInfo)
            self.classargs.append({"executable" : executable})
            if likwid_enable:
                if likwid_path is None or not pexists(likwid_path):
                    path = which("likwid-topology")
                    if path:
                        likwid_path = os.path.dirname(path)
                clargs = {"likwid_base" : likwid_path}
                self.classlist += [PrefetcherInfo, TurboInfo]
                self.classargs += [clargs, clargs]
        elif ostype == "Darwin":
            self.classlist = [
                MachineStateInfo,
                HostInfo,
                CpuInfoMacOS,
                OSInfoMacOS,
                CacheTopologyMacOS,
                CpuTopologyMacOS,
                CpuFrequencyMacOs,
                UptimeMacOs,
                UsersInfo,
                ShellEnvironment,
                PythonInfo,
                CompilerInfo,
                LoadAvgMacOs,
                MemInfoMacOS,
                MpiInfo,
                NumaInfoMacOS,
            ]
            self.classargs = [{} for x in self.classlist]
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
class OSInfoMacOS(InfoGroup):
    def __init__(self, extended=False, anonymous=False):
        super(OSInfoMacOS, self).__init__(anonymous=anonymous, extended=extended)
        self.name = "OperatingSystemInfo"
        ostype = get_ostype()
        self.const("Type", ostype)
        self.required("Type")
        self.addc("Version", "sysctl", "-n kern.osproductversion", r"([\d\.]+)")
        self.required("Version")

class OSInfo(InfoGroup):
    def __init__(self, extended=False, anonymous=False):
        super(OSInfo, self).__init__(anonymous=anonymous, extended=extended)
        self.name = "OperatingSystemInfo"
        ostype = get_ostype()
        self.const("Type", ostype)
        self.required("Type")
        self.addf("Name", "/etc/os-release", r"NAME=[\"]*([^\"]+)[\"]*\s*")
        self.addf("Version", "/etc/os-release", r"VERSION=[\"]*([^\"]+)[\"]*\s*")

        self.required(["Name", "Version"])
        if extended:
            self.addf("URL", "/etc/os-release", r"HOME_URL=[\"]*([^\"]+)[\"]*\s*")

################################################################################
# Infos about NUMA balancing
################################################################################
class NumaBalance(InfoGroup):
    def __init__(self, extended=False, anonymous=False):
        super(NumaBalance, self).__init__(extended=extended, anonymous=anonymous)
        self.name = "NumaBalancing"
        base = "/proc/sys/kernel"
        regex = r"(\d+)"
        self.addf("Enabled", pjoin(base, "numa_balancing"), regex, tobool)
        self.required("Enabled")
        if extended:
            names = ["ScanDelayMs", "ScanPeriodMaxMs", "ScanPeriodMinMs", "ScanSizeMb"]
            files = ["numa_balancing_scan_delay_ms", "numa_balancing_scan_period_max_ms",
                     "numa_balancing_scan_period_min_ms", "numa_balancing_scan_size_mb"]
            for key, fname in zip(names, files):
                self.addf(key, pjoin(base, fname), regex, int)
                self.required(key)

################################################################################
# Infos about the host
################################################################################
class HostInfo(InfoGroup):
    def __init__(self, extended=False, anonymous=False):
        super(HostInfo, self).__init__(anonymous=anonymous, extended=extended)
        self.name = "HostInfo"
        if not anonymous:
            self.addc("Hostname", "hostname", "-s", r"(.+)")
            if extended:
                self.addc("Domainname", "hostname", "-d", r"(.+)")
                self.addc("FQDN", "hostname", "-f", r"(.+)")

################################################################################
# Infos about the CPU
################################################################################

class CpuInfoMacOS(InfoGroup):
    def __init__(self, extended=False, anonymous=False):
        super(CpuInfoMacOS, self).__init__(name="CpuInfo", extended=extended, anonymous=anonymous)
        self.const("MachineType", platform.machine())
        self.addc("Vendor", "sysctl", "-a", r"machdep.cpu.vendor: (.*)")
        self.addc("Name", "sysctl", "-a", r"machdep.cpu.brand_string: (.*)")
        self.addc("Family", "sysctl", "-a", r"machdep.cpu.family: (\d+)", int)
        self.addc("Model", "sysctl", "-a", r"machdep.cpu.model: (\d+)", int)
        self.addc("Stepping", "sysctl", "-a", r"machdep.cpu.stepping: (\d+)", int)
        if extended:
            self.addc("Flags", "sysctl", "-a", r"machdep.cpu.features: (.*)", tostrlist)
            self.addc("ExtFlags", "sysctl", "-a", r"machdep.cpu.extfeatures: (.*)", tostrlist)
            self.addc("Leaf7Flags", "sysctl", "-a", r"machdep.cpu.leaf7_features: (.*)", tostrlist)
            self.addc("Microcode", "sysctl", "-a", r"machdep.cpu.microcode_version: (.*)")
            self.addc("ExtFamily", "sysctl", "-a", r"machdep.cpu.extfamily: (\d+)", int)
            self.addc("ExtModel", "sysctl", "-a", r"machdep.cpu.extmodel: (\d+)", int)
        self.required(["Vendor", "Family", "Model", "Stepping"])

class CpuInfo(InfoGroup):
    def __init__(self, extended=False, anonymous=False):
        super(CpuInfo, self).__init__(name="CpuInfo", extended=extended, anonymous=anonymous)
        march = platform.machine()
        self.const("MachineType", march)

        if march in ["x86_64", "i386"]:
            self.addf("Vendor", "/proc/cpuinfo", r"vendor_id\s+:\s(.*)")
            self.addf("Name", "/proc/cpuinfo", r"model name\s+:\s(.+)")
            self.addf("Family", "/proc/cpuinfo", r"cpu family\s+:\s(.+)", int)
            self.addf("Model", "/proc/cpuinfo", r"model\s+:\s(.+)", int)
            self.addf("Stepping", "/proc/cpuinfo", r"stepping\s+:\s(.+)", int)
        elif march in ["aarch64"]:
            self.addf("Vendor", "/proc/cpuinfo", r"CPU implementer\s+:\s([x0-9a-fA-F]+)")
            self.addf("Family", "/proc/cpuinfo", r"CPU architecture\s*:\s([x0-9a-fA-F]+)", int)
            self.addf("Model", "/proc/cpuinfo", r"CPU variant\s+:\s([x0-9a-fA-F]+)", int)
            self.addf("Stepping", "/proc/cpuinfo", r"CPU revision\s+:\s([x0-9a-fA-F]+)", int)
            self.addf("Variant", "/proc/cpuinfo", r"CPU part\s+:\s([x0-9a-fA-F]+)", int)
        elif march in ["ppc64le", "ppc64"]:
            self.addf("Platform", "/proc/cpuinfo", r"platform\s+:\s(.*)")
            self.addf("Name", "/proc/cpuinfo", r"model\s+:\s(.+)")
            self.addf("Family", "/proc/cpuinfo", r"cpu\s+:\s(POWER\d+).*")
            self.addf("Model", "/proc/cpuinfo", r"model\s+:\s(.+)")
            self.addf("Stepping", "/proc/cpuinfo", r"revision\s+:\s(.+)")

        
        if pexists("/sys/devices/system/cpu/smt/active"):
            self.addf("SMT", "/sys/devices/system/cpu/smt/active", r"(\d+)", tobool)
            self.required("SMT")
        if extended:
            if march in ["x86_64", "i386"]:
                self.addf("Flags", "/proc/cpuinfo", r"flags\s+:\s(.+)", tostrlist)
                self.addf("Microcode", "/proc/cpuinfo", r"microcode\s+:\s(.+)")
                self.addf("Bugs", "/proc/cpuinfo", r"bugs\s+:\s(.+)", tostrlist)
                self.required("Microcode")
            elif march in ["aarch64"]:
                self.addf("Flags", "/proc/cpuinfo", r"Features\s+:\s(.+)", tostrlist)

        self.required(["Vendor", "Family", "Model", "Stepping"])

################################################################################
# CPU Topology
################################################################################
class CpuTopologyMacOSClass(InfoGroup):
    def __init__(self, ident, extended=False, anonymous=False, ncpu=1, ncores=1, ncores_pack=1):
        super(CpuTopologyMacOSClass, self).__init__(anonymous=anonymous, extended=extended)
        self.name = "Cpu{}".format(ident)
        smt = ncpu/ncores
        self.const("ThreadId", int(ident % smt))
        self.const("CoreId", int(ident//smt))
        self.const("PackageId", int(ident//ncores_pack))
        self.const("HWThread", ident)

class CpuTopologyMacOS(ListInfoGroup):
    def __init__(self, extended=False, anonymous=False):
        super(CpuTopologyMacOS, self).__init__(anonymous=anonymous, extended=extended)
        self.name = "CpuTopology"
        ncpu = process_cmd(("sysctl", "-a", r"hw.logicalcpu: (\d+)", int))
        ncores_pack = process_cmd(("sysctl", "-a", r"machdep.cpu.cores_per_package: (\d+)", int))
        ncores = process_cmd(("sysctl", "-a", r"machdep.cpu.core_count: (\d+)", int))
        if isinstance(ncpu, int) and isinstance(ncores_pack, int) and isinstance(ncores, int):
            self.userlist = list(range(ncpu))
            self.subclass = CpuTopologyMacOSClass
            self.subargs = {"ncpu" : ncpu, "ncores" : ncores, "ncores_pack" : ncores_pack}

class CpuTopologyClass(InfoGroup):
    def __init__(self, ident, extended=False, anonymous=False):
        super(CpuTopologyClass, self).__init__(anonymous=anonymous, extended=extended)
        self.name = "Cpu{}".format(ident)
        base = "/sys/devices/system/cpu/cpu{}/topology".format(ident)
        self.addf("CoreId", pjoin(base, "core_id"), r"(\d+)", int)
        self.addf("PackageId", pjoin(base, "physical_package_id"), r"(\d+)", int)
        self.const("HWThread", ident)
        self.const("ThreadId", CpuTopologyClass.getthreadid(ident))
        self.required("CoreId", "PackageId", "HWThread", "ThreadId")

    @staticmethod
    def getthreadid(hwthread):
        base = "/sys/devices/system/cpu/cpu{}/topology/thread_siblings_list".format(hwthread)
        outfp = fopen(base)
        tid = 0
        if outfp:
            tid = 0
            data = outfp.read().decode(ENCODING).strip()
            dlist = data.split(",")
            if len(dlist) == 1:
                tid = 0
            elif len(dlist) > 1:
                tid = dlist.index(str(hwthread))
            elif "-" in data:
                dlist = data.split("-")
                if len(dlist) > 1:
                    trange = range(int(dlist[0]), int(dlist[1])+1)
                    tid = trange.index(hwthread)
            outfp.close
        return tid


class CpuTopology(PathMatchInfoGroup):
    def __init__(self, extended=False, anonymous=False):
        super(CpuTopology, self).__init__(extended=extended, anonymous=anonymous)
        self.name = "CpuTopology"
        self.searchpath = "/sys/devices/system/cpu/cpu*"
        self.match = r".*/cpu(\d+)$"
        self.subclass = CpuTopologyClass
        self.const("NumHWThreads", CpuTopology.getnumcpus())
        self.const("NumNUMANodes", CpuTopology.getnumnumanodes())
        self.const("SMTWidth", CpuTopology.getsmtwidth())
        self.const("NumSockets", CpuTopology.getnumpackages())
        self.const("NumCores", CpuTopology.getnumcores())

    @staticmethod
    def getnumcpus():
        searchpath = "/sys/devices/system/cpu/cpu*"
        match = r".*/cpu(\d+)$"
        if searchpath and match and pexists(os.path.dirname(searchpath)):
            mat = re.compile(match)
            base = searchpath
            glist = sorted([int(mat.match(f).group(1)) for f in glob(base) if mat.match(f)])
            return len(glist)
        return 0
    @staticmethod
    def getnumnumanodes():
        searchpath = "/sys/devices/system/node/node*"
        match = r".*/node(\d+)$"
        if searchpath and match and pexists(os.path.dirname(searchpath)):
            mat = re.compile(match)
            base = searchpath
            glist = sorted([int(mat.match(f).group(1)) for f in glob(base) if mat.match(f)])
            return len(glist)
        return 0
    def getsmtwidth():
        filefp = fopen("/sys/devices/system/cpu/cpu0/topology/thread_siblings_list")
        if filefp:
            data = filefp.read().decode(ENCODING).strip()
            filefp.close()
            return len(re.split(r",", data))
        return 1
    def getnumpackages():
        flist = glob("/sys/devices/system/cpu/cpu*/topology/physical_package_id")
        plist = []
        for fname in flist:
            filefp = fopen(fname)
            if filefp:
                data = filefp.read().decode(ENCODING).strip()
                if data not in plist:
                    plist.append(data)
                filefp.close()
        if len(plist) > 0:
            return len(plist)
        return 1
    def getnumcores():
        flist = glob("/sys/devices/system/cpu/cpu*/topology/core_id")
        plist = []
        for fname in flist:
            filefp = fopen(fname)
            if filefp:
                data = filefp.read().decode(ENCODING).strip()
                if data not in plist:
                    plist.append(data)
                filefp.close()
        return len(plist) * CpuTopology.getnumpackages()

################################################################################
# CPU Frequency
################################################################################
class CpuFrequencyMacOsCpu(InfoGroup):
    def __init__(self, extended=False, anonymous=False):
        super(CpuFrequencyMacOsCpu, self).__init__(extended=extended, anonymous=anonymous)
        self.name = "Cpus"
        self.addc("MaxFreq", "sysctl", "-a", r"hw.cpufrequency_max: (\d+)", int)
        self.addc("MinFreq", "sysctl", "-a", r"hw.cpufrequency_min: (\d+)", int)

class CpuFrequencyMacOsBus(InfoGroup):
    def __init__(self, extended=False, anonymous=False):
        super(CpuFrequencyMacOsBus, self).__init__(extended=extended, anonymous=anonymous)
        self.name = "Bus"
        self.addc("MaxFreq", "sysctl", "-a", r"hw.busfrequency_max: (\d+)", int)
        self.addc("MinFreq", "sysctl", "-a", r"hw.busfrequency_min: (\d+)", int)

class CpuFrequencyMacOs(MultiClassInfoGroup):
    def __init__(self, extended=False, anonymous=False):
        super(CpuFrequencyMacOs, self).__init__(extended=extended, anonymous=anonymous)
        self.name = "CpuFrequency"
        self.classlist = [CpuFrequencyMacOsCpu, CpuFrequencyMacOsBus]
        self.classargs = [{} for c in self.classlist]
        self.addc("TimerFreq", "sysctl", "-a", r"hw.tbfrequency: (\d+)", int)

class CpuFrequencyClass(InfoGroup):
    def __init__(self, ident, extended=False, anonymous=False):
        super(CpuFrequencyClass, self).__init__(anonymous=anonymous, extended=extended)
        self.name = "Cpu{}".format(ident)
        base = "/sys/devices/system/cpu/cpu{}/cpufreq".format(ident)
        if pexists(pjoin(base, "scaling_max_freq")):
            self.addf("MaxFreq", pjoin(base, "scaling_max_freq"), r"(\d+)", tohertz)
        if pexists(pjoin(base, "scaling_max_freq")):
            self.addf("MinFreq", pjoin(base, "scaling_min_freq"), r"(\d+)", tohertz)
        if pexists(pjoin(base, "scaling_governor")):
            self.addf("Governor", pjoin(base, "scaling_governor"), r"(.+)")
        if pexists(pjoin(base, "energy_performance_preference")):
            fname = pjoin(base, "energy_performance_preference")
            self.addf("EnergyPerfPreference", fname, r"(.+)")
        self.required(list(self.files.keys()))

class CpuFrequency(PathMatchInfoGroup):
    def __init__(self, extended=False, anonymous=False):
        super(CpuFrequency, self).__init__(extended=extended, anonymous=anonymous)
        self.name = "CpuFrequency"
        base = "/sys/devices/system/cpu/cpu0/cpufreq"
        if pexists(base):
            self.searchpath = "/sys/devices/system/cpu/cpu*"
            self.match = r".*/cpu(\d+)$"
            self.subclass = CpuFrequencyClass
            if pexists(pjoin(base, "scaling_driver")):
                self.addf("Driver", pjoin(base, "scaling_driver"), r"(.*)")
                self.required("Driver")
            if extended:
                if pexists(pjoin(base, "cpuinfo_transition_latency")):
                    fname = pjoin(base, "cpuinfo_transition_latency")
                    self.addf("TransitionLatency", fname, r"(\d+)", int)
                if pexists(pjoin(base, "cpuinfo_max_freq")):
                    self.addf("MaxAvailFreq", pjoin(base, "cpuinfo_max_freq"), r"(\d+)", tohertz)
                if pexists(pjoin(base, "cpuinfo_min_freq")):
                    self.addf("MinAvailFreq", pjoin(base, "cpuinfo_min_freq"), r"(\d+)", tohertz)
                if pexists(pjoin(base, "scaling_available_frequencies")):
                    fname = pjoin(base, "scaling_available_frequencies")
                    self.addf("AvailFrequencies", fname, r"(.*)", tohertzlist)
                if pexists(pjoin(base, "scaling_available_governors")):
                    fname = pjoin(base, "scaling_available_governors")
                    self.addf("AvailGovernors", fname, r"(.*)", tostrlist)
                if pexists(pjoin(base, "energy_performance_available_preferences")):
                    fname = pjoin(base, "energy_performance_available_preferences")
                    self.addf("AvailEnergyPerfPreferences", fname, r"(.*)", tostrlist)

################################################################################
# NUMA Topology
################################################################################
class NumaInfoMacOS(InfoGroup):
    def __init__(self, anonymous=False, extended=False):
        super(NumaInfoMacOS, self).__init__(anonymous=anonymous, extended=extended)
        self.name = "NumaNode0"
        self.addc("MemTotal", "sysctl", "-a", r"hw.memsize: (\d+)", int)
        self.addc("MemFree", "sysctl", "-a", r"vm.page_free_count: (\d+)", MemInfoMacOS.pagescale)
        self.addc("CpuList", "sysctl", "-a", r"hw.cacheconfig: (\d+)", NumaInfoMacOS.cpulist)
    @staticmethod
    def cpulist(value):
        ncpu = process_cmd(("sysctl", "-n hw.ncpu", r"(\d+)", int))
        clist = []
        if isinstance(ncpu, int):
            for i in range(ncpu//int(value)):
                clist.append(list(range(i*ncpu, (i+1)*ncpu)))
        return clist


class NumaInfoHugepagesClass(InfoGroup):
    def __init__(self, size, extended=False, anonymous=False, node=0):
        name = "Hugepages-{}".format(size)
        super(NumaInfoHugepagesClass, self).__init__(name=name,
                                                     extended=extended,
                                                     anonymous=anonymous)
        base = "/sys/devices/system/node/node{}/hugepages/hugepages-{}".format(node, size)
        self.addf("Count", pjoin(base, "nr_hugepages"), r"(\d+)", int)
        self.addf("Free", pjoin(base, "free_hugepages"), r"(\d+)", int)
        self.required(["Count", "Free"])

class NumaInfoClass(PathMatchInfoGroup):
    def __init__(self, node, anonymous=False, extended=False):
        super(NumaInfoClass, self).__init__(anonymous=anonymous, extended=extended)
        self.name = "NumaNode{}".format(node)
        base = "/sys/devices/system/node/node{}".format(node)
        meminfo = pjoin(base, "meminfo")
        prefix = "Node {}".format(node)
        regex = r"(\d+\s[kKMG][B])"
        self.addf("MemTotal", meminfo, r"{} MemTotal:\s+{}".format(prefix, regex), tobytes)
        self.addf("MemFree", meminfo, r"{} MemFree:\s+{}".format(prefix, regex), tobytes)
        self.addf("MemUsed", meminfo, r"{} MemUsed:\s+{}".format(prefix, regex), tobytes)
        self.addf("Distances", pjoin(base, "distance"), r"(.*)", tointlist)
        self.addf("CpuList", pjoin(base, "cpulist"), r"(.*)", tointlist)

        if extended:
            self.addf("Writeback", meminfo, r"{} Writeback:\s+{}".format(prefix, regex), tobytes)

        self.required("MemTotal", "MemFree", "CpuList")
        self.searchpath = "/sys/devices/system/node/node{}/hugepages/hugepages-*".format(node)
        self.match = r".*/hugepages-(\d+[kKMG][B])$"
        self.subclass = NumaInfoHugepagesClass
        self.subargs = {"node" : node}

class NumaInfo(PathMatchInfoGroup):
    def __init__(self, extended=False, anonymous=False):
        super(NumaInfo, self).__init__(name="NumaInfo", extended=extended, anonymous=anonymous)
        self.searchpath = "/sys/devices/system/node/node*"
        self.match = r".*/node(\d+)$"
        self.subclass = NumaInfoClass

################################################################################
# Cache Topology
################################################################################
class CacheTopologyMacOSClass(InfoGroup):
    def __init__(self, ident, extended=False, anonymous=False):
        super(CacheTopologyMacOSClass, self).__init__(extended=extended, anonymous=anonymous)
        self.name = ident.upper()
        self.addc("Size", "sysctl", "-n hw.{}cachesize".format(ident), r"(\d+)", int)
        self.const("Level", re.match(r"l(\d+)[id]*", ident).group(1))
        if re.match(r"l\d+([id]*)", ident).group(1) == 'i':
            self.const("Type", "Instruction")
        elif re.match(r"l\d+([id]*)", ident).group(1) == 'd':
            self.const("Type", "Data")
        else:
            self.const("Type", "Unified")
        self.const("CpuList", CacheTopologyMacOSClass.getcpulist(ident))
        if extended:
            self.addc("CoherencyLineSize", "sysctl", "-n hw.cachelinesize", r"(\d+)", int)
            key = "machdep.cpu.cache.{}_associativity".format(self.name)
            out = process_cmd(("sysctl", "-n {}".format(key), r"(\d+)", int))
            if isinstance(out, int):
                self.addc("Associativity", "sysctl", "-n {}".format(key), r"(\d+)", int)
    @staticmethod
    def getcpulist(arg):
        clist = []
        level = re.match(r"l(\d+)[id]*", arg).group(1)
        if level and int(level) > 0:
            ncpus = process_cmd(("sysctl", "-n hw.ncpu", r"(\d+)", int))
            cconfig = process_cmd(("sysctl", "-n hw.cacheconfig", r"([\d\s]+)", tointlist))
            if cconfig and ncpus:
                if len(cconfig) > int(level):
                    sharedbycount = int(cconfig[int(level)])
                    for i in range(ncpus//sharedbycount):
                        clist.append(list(range(i*sharedbycount, (i+1)*sharedbycount)))
        return clist



class CacheTopologyMacOS(ListInfoGroup):
    def __init__(self, extended=False, anonymous=False):
        super(CacheTopologyMacOS, self).__init__(anonymous=anonymous, extended=extended)
        self.name = "CacheTopology"
        self.userlist = ["l1i", "l1d", "l2", "l3"]
        self.subclass = CacheTopologyMacOSClass



class CacheTopologyClass(InfoGroup):
    def __init__(self, ident, extended=False, anonymous=False):
        super(CacheTopologyClass, self).__init__(extended=extended, anonymous=anonymous)
        self.name = "L{}".format(ident)
        base = "/sys/devices/system/cpu/cpu0/cache/index{}".format(ident)
        fparse = CacheTopologyClass.kBtoBytes
        if pexists(base):
            self.addf("Size", pjoin(base, "size"), r"(\d+)", fparse)
            self.addf("Level", pjoin(base, "level"), r"(\d+)", int)
            self.addf("Type", pjoin(base, "type"), r"(.+)")
            self.const("CpuList", CacheTopologyClass.getcpulist(ident))
            if extended:
                self.addf("Sets", pjoin(base, "number_of_sets"), r"(\d+)", int)
                self.addf("Associativity", pjoin(base, "ways_of_associativity"), r"(\d+)", int)
                self.addf("CoherencyLineSize", pjoin(base, "coherency_line_size"), r"(\d+)", fparse)
                phys_line_part = pjoin(base, "physical_line_partition")
                if pexists(phys_line_part):

                    self.addf("PhysicalLineSize", phys_line_part, r"(\d+)", fparse)
                alloc_policy = pjoin(base, "allocation_policy")
                if pexists(alloc_policy):
                    self.addf("AllocPolicy", alloc_policy, r"(.+)")
                write_policy = pjoin(base, "write_policy")
                if pexists(write_policy):
                    self.addf("WritePolicy", write_policy, r"(.+)", int)
        self.required(list(self.files.keys()))
        #"CpuList" : (pjoin(self.searchpath, "shared_cpu_list"), r"(.+)", tointlist),
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
            filefp = fopen(path)
            if filefp:
                data = filefp.read().decode(ENCODING).strip()
                clist = tointlist(data)
                if str(clist) not in slist:
                    cpulist.append(clist)
                    slist.append(str(clist))
                filefp.close()
        return cpulist
    @staticmethod
    def kBtoBytes(value):
        return tobytes("{} kB".format(value))
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
    def __init__(self, extended=False, anonymous=False):
        super(CacheTopology, self).__init__(anonymous=anonymous, extended=extended)
        self.name = "CacheTopology"
        self.searchpath = "/sys/devices/system/cpu/cpu0/cache/index*"
        self.match = r".*/index(\d+)$"
        self.subclass = CacheTopologyClass

################################################################################
# Infos about the uptime of the system
################################################################################
class UptimeMacOs(InfoGroup):
    def __init__(self, extended=False, anonymous=False):
        super(UptimeMacOs, self).__init__(name="Uptime", extended=extended, anonymous=anonymous)
        timematch = re.compile(r"\d+:\d+.*\s+(\d+:\d+).*")
        self.addc("Uptime", "uptime", cmd_opts=None, match=r"(.*)", parse=UptimeMacOs.parsetime)
        self.addc("UptimeReadable", "uptime", None, None, UptimeMacOs.parsereadable)
        self.required("Uptime")
    @staticmethod
    def parsetime(string):
        timematch = re.compile(r"\d+:\d+.*\s+(\d+):(\d+).*")
        daymatch = re.compile(r"\d+:\d+\s+up (\d+) days.*")
        tm = timematch.match(string)
        if tm:
            days = 0
            dm = daymatch.match(string)
            if dm:
                days = dm.group(1)
            hours, minutes = tm.groups()
            uptime = int(days) * 86400 + int(hours) * 3600 + int(minutes) * 60
            return float(uptime)
        return None
    @staticmethod
    def parsereadable(string):
        uptime = UptimeMacOs.parsetime(string)
        return Uptime.totimedelta(uptime)


class Uptime(InfoGroup):
    def __init__(self, extended=False, anonymous=False):
        super(Uptime, self).__init__(name="Uptime", extended=extended, anonymous=anonymous)
        fname = "/proc/uptime"
        self.addf("Uptime", fname, r"([\d\.]+)\s+[\d\.]+", float)
        self.addf("UptimeReadable", fname, r"([\d\.]+)\s+[\d\.]+", Uptime.totimedelta)

        self.required("Uptime")
        if extended:
            self.addf("CpusIdle", fname, r"[\d\.]+\s+([\d\.]+)", float)
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
class LoadAvgMacOs(InfoGroup):
    def __init__(self, extended=False, anonymous=False):
        super(LoadAvgMacOs, self).__init__(name="LoadAvg", extended=extended, anonymous=anonymous)
        self.addc("LoadAvg1m", "uptime", None, r".*load averages:\s+([\d\.]+)", float)
        self.addc("LoadAvg5m", "uptime", None, r".*load averages:\s+[\d\.]+\s+([\d+\.]+)", float)
        self.addc("LoadAvg15m", "uptime", None, r".*load averages:\s+[\d\.]+\s+[\d+\.]+\s+([\d+\.]+)", float)


class LoadAvg(InfoGroup):
    def __init__(self, extended=False, anonymous=False):
        super(LoadAvg, self).__init__(name="LoadAvg", extended=extended, anonymous=anonymous)
        self.addf("LoadAvg1m", "/proc/loadavg", r"([\d\.]+)", float)
        self.addf("LoadAvg5m", "/proc/loadavg", r"[\d\.]+\s+([\d+\.]+)", float)
        self.addf("LoadAvg15m", "/proc/loadavg", r"[\d\.]+\s+[\d+\.]+\s+([\d+\.]+)", float)
        #self.required(["LoadAvg15m"])
        if extended:
            rpmatch = r"[\d+\.]+\s+[\d+\.]+\s+[\d+\.]+\s+(\d+)"
            self.addf("RunningProcesses", "/proc/loadavg", rpmatch, int)
            apmatch = r"[\d+\.]+\s+[\d+\.]+\s+[\d+\.]+\s+\d+/(\d+)"
            self.addf("AllProcesses", "/proc/loadavg", apmatch, int)


################################################################################
# Infos about the memory of the system
################################################################################
class MemInfoMacOS(InfoGroup):
    def __init__(self, extended=False, anonymous=False):
        super(MemInfoMacOS, self).__init__(name="MemInfo", extended=extended, anonymous=anonymous)
        self.addc("MemTotal", "sysctl", "-a", r"hw.memsize: (\d+)", int)
        self.addc("MemFree", "sysctl", "-a", r"vm.page_free_count: (\d+)", MemInfoMacOS.pagescale)
        self.addc("SwapTotal", "sysctl", "-a", r"vm.swapusage: total =\s+([\d\,M]+)", MemInfoMacOS.tobytes)
        self.addc("SwapFree", "sysctl", "-a", r"vm.swapusage:.*free =\s+([\d\,M]+)", MemInfoMacOS.tobytes)
        self.required(["MemFree", "MemTotal"])
    @staticmethod
    def pagescale(string):
        pagesize = process_cmd(("sysctl", "-n vm.pagesize", r"(\d+)", int))
        return int(string) * pagesize
    def tobytes(string):
        return int(float(string) * 1024**2)

class MemInfo(InfoGroup):
    def __init__(self, extended=False, anonymous=False):
        super(MemInfo, self).__init__(name="MemInfo", extended=extended, anonymous=anonymous)
        fname = "/proc/meminfo"
        self.addf("MemTotal", fname, r"MemTotal:\s+(\d+\s[kKMG][B])", tobytes)
        self.addf("MemAvailable", fname, r"MemAvailable:\s+(\d+\s[kKMG][B])", tobytes)
        self.addf("MemFree", fname, r"MemFree:\s+(\d+\s[kKMG][B])", tobytes)
        self.addf("SwapTotal", fname, r"SwapTotal:\s+(\d+\s[kKMG][B])", tobytes)
        self.addf("SwapFree", fname, r"SwapFree:\s+(\d+\s[kKMG][B])", tobytes)
        if extended:
            self.addf("Buffers", fname, r"Buffers:\s+(\d+\s[kKMG][B])", tobytes)
            self.addf("Cached", fname, r"Cached:\s+(\d+\s[kKMG][B])", tobytes)
        self.required(["MemFree", "MemTotal"])

################################################################################
# Infos about the kernel
################################################################################
class KernelSchedInfo(InfoGroup):
    def __init__(self, extended=False, anonymous=False):
        super(KernelSchedInfo, self).__init__(name="KernelSchedInfo",
                                              extended=extended,
                                              anonymous=anonymous)
        base = "/proc/sys/kernel"
        self.addf("RealtimeBandwidthReservationUs", pjoin(base, "sched_rt_runtime_us"), parse=int)
        self.addf("TargetedPreemptionLatencyNs", pjoin(base, "sched_latency_ns"), parse=int)
        name = "MinimalPreemptionGranularityNs"
        self.addf(name, pjoin(base, "sched_min_granularity_ns"), parse=int)
        self.addf("WakeupLatencyNs", pjoin(base, "sched_wakeup_granularity_ns"), parse=int)
        self.addf("RuntimePoolTransferUs", pjoin(base, "sched_cfs_bandwidth_slice_us"), parse=int)
        self.addf("ChildRunsFirst", pjoin(base, "sched_child_runs_first"), parse=tobool)
        self.addf("CacheHotTimeNs", pjoin(base, "sched_migration_cost_ns"), parse=int)

class KernelRcuInfo(InfoGroup):
    def __init__(self, command, extended=False, anonymous=False):
        super(KernelRcuInfo, self).__init__(name=command,
                                            extended=extended,
                                            anonymous=anonymous)
        cmd_opts = "-c -p $(pgrep {})".format(command)
        regex = r".*current affinity list: (.*)"
        # see https://pyperf.readthedocs.io/en/latest/system.html#more-options
        self.addc("Affinity", "taskset", cmd_opts, regex, tointlist)

class KernelInfo(ListInfoGroup):
    def __init__(self, extended=False, anonymous=False):
        super(KernelInfo, self).__init__(name="KernelInfo",
                                         extended=extended,
                                         anonymous=anonymous)
        self.addf("Version", "/proc/sys/kernel/osrelease")
        self.addf("CmdLine", "/proc/cmdline")
        # see https://pyperf.readthedocs.io/en/latest/system.html#checks
        self.addf("ASLR", "/proc/sys/kernel/randomize_va_space", parse=int)
        self.addf("ThreadsMax", "/proc/sys/kernel/threads-max", parse=int)
        self.addf("NMIWatchdog", "/proc/sys/kernel/nmi_watchdog", parse=tobool)
        self.addf("Watchdog", "/proc/sys/kernel/watchdog", parse=tobool)
        self.addf("HungTaskCheckCount", "/proc/sys/kernel/hung_task_check_count", parse=int)
        if pexists("/proc/sys/kernel/softlockup_thresh"):
            self.addf("SoftwareWatchdog", "/proc/sys/kernel/softlockup_thresh", parse=int)
        self.addf("VMstatPolling", "/proc/sys/vm/stat_interval", parse=int)
        self.required("Version", "CmdLine", "NMIWatchdog", "Watchdog")

        cls = KernelSchedInfo(extended=extended,
                              anonymous=anonymous)
        self._instances.append(cls)
        self.userlist = ["rcu_sched", "rcu_bh", "rcu_tasks_kthre"]
        self.subclass = KernelRcuInfo

################################################################################
# Infos about CGroups
################################################################################
class CgroupInfo(InfoGroup):
    def __init__(self, extended=False, anonymous=False):
        super(CgroupInfo, self).__init__(name="Cgroups", extended=extended, anonymous=anonymous)
        csetmat = re.compile(r"\d+\:cpuset\:([/\w\d\-\._]*)")
        cset = process_file(("/proc/self/cgroup", csetmat))
        if cset is not None:
            base = pjoin("/sys/fs/cgroup/cpuset", cset.strip("/"))
            self.addf("CPUs", pjoin(base, "cpuset.cpus"), r"(.+)", tointlist)
            self.addf("Mems", pjoin(base, "cpuset.mems"), r"(.+)", tointlist)
            self.required("CPUs", "Mems")
            if extended:
                names = ["CPUs.effective", "Mems.effective"]
                files = ["cpuset.effective_cpus", "cpuset.effective_mems"]
                for key, fname in zip(names, files):
                    self.addf(key, pjoin(base, fname), r"(.+)", tointlist)
                    self.required(key)

################################################################################
# Infos about the writeback workqueue
################################################################################
class WritebackWorkqueue(InfoGroup):
    def __init__(self, extended=False, anonymous=False):
        super(WritebackWorkqueue, self).__init__(name="WritebackWorkqueue",
                                                 extended=extended,
                                                 anonymous=anonymous)
        base = "/sys/bus/workqueue/devices/writeback"
        self.addf("CPUmask", pjoin(base, "cpumask"), r"([0-9a-fA-F]+)", masktolist)
        self.addf("MaxActive", pjoin(base, "max_active"), r"(\d+)", int)
        self.addf("NUMA", pjoin(base, "numa"), r"(\d+)", int)
        self.required(["CPUmask", "MaxActive", "NUMA"])

################################################################################
# Infos about transparent hugepages
################################################################################
class TransparentHugepages(InfoGroup):
    def __init__(self, extended=False, anonymous=False):
        super(TransparentHugepages, self).__init__(name="TransparentHugepages",
                                                   extended=extended,
                                                   anonymous=anonymous)
        base = "/sys/kernel/mm/transparent_hugepage"
        self.addf("State", pjoin(base, "enabled"), r".*\[(.*)\].*")
        self.addf("UseZeroPage", pjoin(base, "use_zero_page"), r"(\d+)", tobool)
        self.required(["State", "UseZeroPage"])


################################################################################
# Infos about powercapping
#################################################################################
class PowercapInfoConstraintClass(InfoGroup):
    '''Class to read information about one powercap constraint'''
    def __init__(self, ident, extended=False, anonymous=False, package=0, domain=-1):
        super(PowercapInfoConstraintClass, self).__init__(name="Constraint{}".format(ident),
                                                          extended=extended,
                                                          anonymous=anonymous)
        base = "/sys/devices/virtual/powercap/intel-rapl/intel-rapl:{}".format(package)
        fptr = fopen(pjoin(base, "constraint_{}_name".format(ident)))
        if fptr:
            self.name = totitle(fptr.read().decode(ENCODING).strip())
            fptr.close()
        if domain >= 0:
            base = pjoin(base, "intel-rapl:{}:{}".format(package, domain))
        names = ["PowerLimitUw",
                 "TimeWindowUs"]
        files = ["constraint_{}_power_limit_uw".format(ident),
                 "constraint_{}_time_window_us".format(ident)]
        for key, fname in zip(names, files):
            self.addf(key, pjoin(base, fname), r"(.+)", int)
        self.required(names)

class PowercapInfoClass(PathMatchInfoGroup):
    '''Class to spawn subclasses for each contraint in a powercap domain'''
    def __init__(self, ident, extended=False, anonymous=False, package=0):
        super(PowercapInfoClass, self).__init__(extended=extended, anonymous=anonymous)
        base = "/sys/devices/virtual/powercap/intel-rapl"
        base = pjoin(base, "intel-rapl:{}/intel-rapl:{}:{}".format(package, package, ident))
        fptr = fopen(pjoin(base, "name".format(ident)))
        if fptr:
            self.name = totitle(fptr.read().decode(ENCODING).strip())
            fptr.close()
        self.addf("Enabled", pjoin(base, "enabled"), r"(\d+)", tobool)
        self.searchpath = pjoin(base, "constraint_*_name")
        self.match = r".*/constraint_(\d+)_name"
        self.subclass = PowercapInfoConstraintClass
        self.subargs = {"package" : package, "domain" : ident}

class PowercapInfoPackageClass(PathMatchInfoGroup):
    '''Class to spawn subclasses for powercap package domain
    (/sys/devices/virtual/powercap/intel-rapl/intel-rapl:*)
    '''
    def __init__(self, ident, extended=False, anonymous=False):
        base = "/sys/devices/virtual/powercap/intel-rapl/intel-rapl:{}".format(ident)
        super(PowercapInfoPackageClass, self).__init__(name="Package",
                                                       extended=extended,
                                                       anonymous=anonymous,
                                                       searchpath=pjoin(base, "constraint_*_name"),
                                                       match=r".*/constraint_(\d+)_name",
                                                       subclass=PowercapInfoConstraintClass,
                                                       subargs={"package" : ident})
        self.addf("Enabled", pjoin(base, "enabled"), r"(\d+)", tobool)

class PowercapInfoPackage(PathMatchInfoGroup):
    '''Class to spawn subclasses for one powercap device/package
    (/sys/devices/virtual/powercap/intel-rapl/intel-rapl:<package>*:*)
    '''
    def __init__(self, package, extended=False, anonymous=False):
        base = "/sys/devices/virtual/powercap/intel-rapl/intel-rapl:{}".format(package)
        super(PowercapInfoPackage, self).__init__(extended=extended,
                                                  anonymous=anonymous,
                                                  subargs={"package" : package},
                                                  match=r".*/intel-rapl\:\d+:(\d+)",
                                                  subclass=PowercapInfoClass)

        fptr = fopen(pjoin(base, "name"))
        if fptr:
            self.name = totitle(fptr.read().decode(ENCODING).strip())
            fptr.close()
        else:
            self.name = "PowercapInfoPackage{}".format(package)
        self.searchpath = pjoin(base, "intel-rapl:{}:*".format(package))
        self.package = package

    def generate(self):
        super(PowercapInfoPackage, self).generate()
        cls = PowercapInfoPackageClass(self.package, extended=self.extended)
        cls.generate()
        self._instances.append(cls)


class PowercapInfo(PathMatchInfoGroup):
    '''Class to spawn subclasses for all powercap devices
    X86 path: /sys/devices/virtual/powercap
    POWER path: /sys/firmware/opal/powercap/system-powercap
    '''
    def __init__(self, extended=False, anonymous=False):
        super(PowercapInfo, self).__init__(name="PowercapInfo",
                                           extended=extended,
                                           anonymous=anonymous)
        if platform.machine() in ["x86_64", "i386"]:
            self.subclass = PowercapInfoPackage
            self.searchpath = "/sys/devices/virtual/powercap/intel-rapl/intel-rapl:*"
            self.match = r".*/intel-rapl\:(\d+)"
        else:
            base = "/sys/firmware/opal/powercap/system-powercap"
            if pexists(base):
                self.addf("PowerLimit", pjoin(base, "powercap-current"), r"(\d+)", int)
                if extended:
                    self.addf("PowerLimitMax", pjoin(base, "powercap-max"), r"(\d+)", int)
                    self.addf("PowerLimitMin", pjoin(base, "powercap-min"), r"(\d+)", int)
            base = "/sys/firmware/opal/psr"
            if pexists(base):
                for i, fname in enumerate(glob(pjoin(base, "cpu_to_gpu_*"))):
                    key = "CpuToGpu{}".format(i)
                    self.addf(key, fname, r"(\d+)", int)


################################################################################
# Infos about hugepages
################################################################################
class HugepagesClass(InfoGroup):
    '''Class to read information about one size of hugepages'''
    def __init__(self, size, extended=False, anonymous=False):
        name = "Hugepages-{}".format(size)
        super(HugepagesClass, self).__init__(name=name, extended=extended, anonymous=anonymous)
        base = "/sys/kernel/mm/hugepages/hugepages-{}".format(size)
        self.addf("Count", pjoin(base, "nr_hugepages"), r"(\d+)", int)
        self.addf("Free", pjoin(base, "free_hugepages"), r"(\d+)", int)
        self.addf("Reserved", pjoin(base, "resv_hugepages"), r"(\d+)", int)

class Hugepages(PathMatchInfoGroup):
    '''Class to spawn subclasses for all hugepages sizes (/sys/kernel/mm/hugepages/hugepages-*)'''
    def __init__(self, extended=False, anonymous=False):
        super(Hugepages, self).__init__(extended=extended, anonymous=anonymous)
        self.name = "Hugepages"
        self.searchpath = "/sys/kernel/mm/hugepages/hugepages-*"
        self.match = r".*/hugepages-(\d+[kKMG][B])"
        self.subclass = HugepagesClass

################################################################################
# Infos about compilers (C, C++ and Fortran)
################################################################################
class CompilerInfoClass(InfoGroup):
    '''Class to read version and path of a given executable'''
    def __init__(self, executable, extended=False, anonymous=False):
        super(CompilerInfoClass, self).__init__(extended=extended, anonymous=anonymous)
        self.name = executable
        self.addc("Version", executable, "--version", r"(\d+\.\d+\.\d+)")
        abscmd = which(executable)
        if abscmd and len(abscmd) > 0:
            self.const("Path", abscmd)
        self.required("Version")


class CCompilerInfo(ListInfoGroup):
    '''Class to spawn subclasses for various C compilers'''
    def __init__(self, extended=False, anonymous=False):
        super(CCompilerInfo, self).__init__(name="C",
                                            extended=extended,
                                            subclass=CompilerInfoClass,
                                            anonymous=anonymous)
        self.compilerlist = ["gcc", "icc", "clang", "pgcc", "xlc", "armclang", "ncc"]
        self.subclass = CompilerInfoClass
        if "CC" in os.environ:
            comp = os.environ["CC"]
            if comp not in self.compilerlist:
                self.compilerlist.append(comp)
        self.userlist = [c for c in self.compilerlist if which(c)]


class CPlusCompilerInfo(ListInfoGroup):
    '''Class to spawn subclasses for various C++ compilers'''
    def __init__(self, extended=False, anonymous=False):
        super(CPlusCompilerInfo, self).__init__(name="C++",
                                                extended=extended,
                                                subclass=CompilerInfoClass,
                                                anonymous=anonymous)
        self.compilerlist = ["g++", "icpc", "clang++", "pg++", "armclang++", "nc++"]
        self.subclass = CompilerInfoClass
        if "CXX" in os.environ:
            comp = os.environ["CXX"]
            if comp not in self.compilerlist:
                self.compilerlist.append(comp)
        self.userlist = [c for c in self.compilerlist if which(c)]


class FortranCompilerInfo(ListInfoGroup):
    '''Class to spawn subclasses for various Fortran compilers'''
    def __init__(self, extended=False, anonymous=False):
        super(FortranCompilerInfo, self).__init__(name="Fortran",
                                                  extended=extended,
                                                  subclass=CompilerInfoClass,
                                                  anonymous=anonymous)
        self.compilerlist = ["gfortran", "ifort", "flang", "pgf90", "armflang", "nfort"]
        if "FC" in os.environ:
            comp = os.environ["FC"]
            if comp not in self.compilerlist:
                self.compilerlist.append(comp)
        self.userlist = [c for c in self.compilerlist if which(c)]


class CompilerInfo(MultiClassInfoGroup):
    '''Class to spawn subclasses for various compilers'''
    def __init__(self, extended=False, anonymous=False):
        clist = [CCompilerInfo, CPlusCompilerInfo, FortranCompilerInfo]
        cargs = [{} for i in range(len(clist))]
        super(CompilerInfo, self).__init__(name="CompilerInfo",
                                           extended=extended,
                                           anonymous=anonymous,
                                           classlist=clist,
                                           classargs=cargs)

################################################################################
# Infos about Python interpreters
################################################################################
class PythonInfoClass(InfoGroup):
    '''Class to read information about a Python executable'''
    def __init__(self, executable, extended=False, anonymous=False):
        super(PythonInfoClass, self).__init__(extended=extended, anonymous=anonymous)
        self.name = executable
        abspath = which(executable)
        if abspath and len(abspath) > 0:
            self.addc("Version", abspath, "--version 2>&1", r"(\d+\.\d+\.\d+)")
            self.const("Path", abspath)
        self.required("Version")

class PythonInfo(ListInfoGroup):
    '''Class to spawn subclasses for various Python commands'''
    def __init__(self, extended=False, anonymous=False):
        self.interpreters = ["python2", "python3", "python"]
        super(PythonInfo, self).__init__(name="PythonInfo",
                                         extended=extended,
                                         anonymous=anonymous,
                                         subclass=PythonInfoClass,
                                         userlist=[i for i in self.interpreters if which(i)])

################################################################################
# Infos about MPI libraries
################################################################################
class MpiInfoClass(InfoGroup):
    '''Class to read information about an MPI or job scheduler executable'''
    def __init__(self, executable, extended=False, anonymous=False):
        super(MpiInfoClass, self).__init__(name=executable, extended=extended, anonymous=anonymous)
        self.addc("Version", executable, "--version", r"(.+)", MpiInfoClass.mpiversion)
        self.addc("Implementor", executable, "--version", r"(.+)", MpiInfoClass.mpivendor)
        abscmd = which(executable)
        if abscmd and len(abscmd) > 0:
            self.const("Path", abscmd)
        self.required(["Version", "Implementor"])

    @staticmethod
    def mpivendor(value):
        if "Open MPI" in value or "OpenRTE" in value:
            return "OpenMPI"
        elif "Intel" in value and "MPI" in value:
            return "IntelMPI"
        elif "slurm" in value.lower():
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
    '''Class to spawn subclasses for various MPI/job scheduler commands'''
    def __init__(self, extended=False, anonymous=False):
        super(MpiInfo, self).__init__(name="MpiInfo", extended=extended)
        self.mpilist = ["mpiexec", "mpiexec.hydra", "mpirun", "srun", "aprun"]
        self.subclass = MpiInfoClass
        self.userlist = [m for m in self.mpilist if which(m)]
        if extended:
            ompi = which("ompi_info")
            if ompi and len(ompi) > 0 and extended:
                ompi_args = "--parseable --params all all --level 9"
                self.addc("OpenMpiParams", ompi, ompi_args, parse=MpiInfo.openmpiparams)
            impi = which("impi_info")
            if impi and len(impi) > 0 and extended:
                self.addc("IntelMpiParams", impi, "| grep I_MPI", parse=MpiInfo.intelmpiparams)
    @staticmethod
    def openmpiparams(value):
        outdict = {}
        for line in value.split("\n"):
            if not line.strip(): continue
            if ":help:" in line or ":type:" in line: continue
            llist = re.split(r":", line)
            outdict[":".join(llist[:-1])] = llist[-1]
        return outdict
    @staticmethod
    def intelmpiparams(value):
        outdict = {}
        for line in value.split("\n"):
            if "I_MPI" not in line: continue
            if not line.strip(): continue
            llist = [x.strip() for x in line.split("|")]
            outdict[llist[1]] = llist[2]
        return outdict

################################################################################
# Infos about environ variables
################################################################################
class ShellEnvironment(InfoGroup):
    '''Class to read the shell environment (os.environ)'''
    def __init__(self, extended=False, anonymous=False):
        super(ShellEnvironment, self).__init__(extended=extended, anonymous=anonymous)
        self.name = "ShellEnvironment"
    def update(self):
        super(ShellEnvironment, self).update()
        outdict = {}
        for key in os.environ:
            value = os.environ[key]
            if self.anonymous:
                value = ShellEnvironment.anonymous_shell_var(key, value)
            outdict.update({key : value})
        self._data.update(outdict)
    @staticmethod
    def anonymous_shell_var(key, value):
        out = value
        ipregex = re.compile(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")
        for ipaddr in ipregex.findall(value):
            out = out.replace(ipaddr, "XXX.XXX.XXX.XXX")
        out = out.replace(getuser(), "anonuser")
        for i, group in enumerate(os.getgroups()):
            gname = getgrgid(group)
            out = out.replace(gname.gr_name, "group{}".format(i))
        return out

################################################################################
# Infos about CPU prefetchers (LIKWID only)
################################################################################
class PrefetcherInfoClass(InfoGroup):
    '''Class to read prefetcher settings for one HW thread (uses the likwid-features command)'''
    def __init__(self, ident, extended=False, anonymous=False, likwid_base=None):
        super(PrefetcherInfoClass, self).__init__(extended=extended, anonymous=anonymous)
        self.name = "Cpu{}".format(ident)
        names = ["HW_PREFETCHER", "CL_PREFETCHER", "DCU_PREFETCHER", "IP_PREFETCHER"]
        cmd_opts = "-c {} -l".format(ident)
        cmd = "likwid-features"
        abscmd = cmd
        if likwid_base and os.path.isdir(likwid_base):
            abscmd = pjoin(likwid_base, cmd)
        if not pexists(abscmd):
            abscmd = which(cmd)

        if abscmd:
            for name in names:
                self.addc(name, abscmd, cmd_opts, r"{}\s+(\w+)".format(name), tobool)
        self.required(names)

class PrefetcherInfo(PathMatchInfoGroup):
    '''Class to spawn subclasses for all HW threads returned by likwid-features'''
    def __init__(self, extended=False, anonymous=False, likwid_base=None):
        super(PrefetcherInfo, self).__init__(name="PrefetcherInfo",
                                             extended=extended,
                                             anonymous=anonymous)
        cmd = "likwid-features"
        abscmd = cmd
        if likwid_base and os.path.isdir(likwid_base):
            abscmd = pjoin(likwid_base, cmd)
        if not pexists(abscmd):
            abscmd = which(cmd)

        if abscmd:
            data = process_cmd((abscmd, "-l -c 0", r"Feature\s+CPU\s(\d+)", int))
            if data == 0:
                self.searchpath = "/sys/devices/system/cpu/cpu*"
                self.match = r".*/cpu(\d+)$"
                self.subclass = PrefetcherInfoClass
                self.subargs = {"likwid_base" : likwid_base}

################################################################################
# Infos about the turbo frequencies (LIKWID only)
################################################################################
class TurboInfo(InfoGroup):
    '''Class to read information about CPU/Uncore frequencies and perf-energy-bias
    (uses the likwid-powermeter command)
    '''
    def __init__(self, extended=False, anonymous=False, likwid_base=None):
        super(TurboInfo, self).__init__(name="TurboInfo", extended=extended, anonymous=anonymous)
        cmd = "likwid-powermeter"
        cmd_opts = "-i 2>&1"
        error_match = r"Cannot gather values.*"
        names = ["BaseClock", "MinClock", "MinUncoreClock", "MaxUncoreClock"]
        matches = [r"Base clock:\s+([\d\.]+ MHz)",
                   r"Minimal clock:\s+([\d\.]+ MHz)",
                   r"Minimal Uncore frequency:\s+([\d\.]+ MHz)",
                   r"Maximal Uncore frequency:\s+([\d\.]+ MHz)",
                  ]
        if likwid_base and len(likwid_base) > 0 and os.path.isdir(likwid_base):
            tmpcmd = pjoin(likwid_base, cmd)
            if pexists(tmpcmd):
                abscmd = tmpcmd
        else:
            abscmd = which(cmd)
        if abscmd:
            data = process_cmd((abscmd, cmd_opts, matches[0]))
            if len(data) > 0 and not re.match(error_match, data):
                for name, regex in zip(names, matches):
                    self.addc(name, abscmd, cmd_opts, regex, tohertz)
                    self.required(name)
                regex = r"^Performance energy bias:\s+(\d+)"
                self.addc("PerfEnergyBias", abscmd, cmd_opts, regex, int)
                self.required("PerfEnergyBias")
                freqfunc = TurboInfo.getactivecores
                self.addc("TurboFrequencies", abscmd, cmd_opts, None, freqfunc)
        self.required4equal = self.commands.keys()
    @staticmethod
    def getactivecores(indata):
        freqs = []
        for line in re.split(r"\n", indata):
            mat = re.match(r"C(\d+)\s+([\d\.]+ MHz)", line)
            if mat:
                freqs.append(tohertz(mat.group(2)))
        return freqs

################################################################################
# Infos about the clock sources provided by the kernel
################################################################################
class ClocksourceInfoClass(InfoGroup):
    '''Class to read information for one clocksource device'''
    def __init__(self, ident, extended=False, anonymous=False):
        super(ClocksourceInfoClass, self).__init__(anonymous=anonymous, extended=extended)
        self.name = "Clocksource{}".format(ident)
        base = "/sys/devices/system/clocksource/clocksource{}".format(ident)
        self.addf("Current", pjoin(base, "current_clocksource"), r"(\s+)", str)
        if extended:
            self.addf("Available", pjoin(base, "available_clocksource"), r"(.+)", tostrlist)
        self.required("Current")

class ClocksourceInfo(PathMatchInfoGroup):
    '''Class to spawn subclasses for all clocksourse devices
    /sys/devices/system/clocksource/clocksource*
    '''
    def __init__(self, extended=False, anonymous=False):
        super(ClocksourceInfo, self).__init__(anonymous=anonymous, extended=extended)
        self.name = "ClocksourceInfo"
        self.searchpath = "/sys/devices/system/clocksource/clocksource*"
        self.match = r".*/clocksource(\d+)$"
        self.subclass = ClocksourceInfoClass

################################################################################
# Infos about the executable (if given on cmdline)
################################################################################
class ExecutableInfoExec(InfoGroup):
    '''Class to read basic information of given executable'''
    def __init__(self, extended=False, anonymous=False, executable=""):
        super(ExecutableInfoExec, self).__init__(anonymous=anonymous, extended=extended)
        self.name = "ExecutableInfo"

        if executable is not None:
            self.executable = executable
            abscmd = which(self.executable)
            self.const("Name", str(self.executable))
            if abscmd and len(abscmd) > 0:
                self.const("Abspath", abscmd)
                self.const("Size", psize(abscmd))
                pfunc = ExecutableInfoExec.getcompiledwith
                self.addc("CompiledWith", "strings", "-a {}".format(abscmd), parse=pfunc)
                if extended:
                    self.const("MD5sum", ExecutableInfoExec.getmd5sum(abscmd))
            self.required(["Name", "Size", "MD5sum"])
    @staticmethod
    def getmd5sum(filename):
        hash_md5 = hashlib.md5()
        with open(filename, "rb") as md5fp:
            for chunk in iter(lambda: md5fp.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    @staticmethod
    def getcompiledwith(value):
        for line in re.split(r"\n", value):
            if "CC" in line:
                return line
        return "Not detectable"

class ExecutableInfoLibraries(InfoGroup):
    '''Class to read all libraries linked with given executable'''
    def __init__(self, executable, extended=False, anonymous=False):
        super(ExecutableInfoLibraries, self).__init__(anonymous=anonymous, extended=extended)
        self.name = "LinkedLibraries"
        self.ldd = None
        if executable is not None:
            self.executable = which(executable)
            self.ldd = None
            if self.executable and len(self.executable) > 0:
                self.ldd = "LANG=C ldd {}; exit 0".format(self.executable)
    def update(self):
        libdict = {}
        if self.ldd is not None:
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
            self.required(list(libdict.keys()))
        self._data = libdict

class ExecutableInfo(MultiClassInfoGroup):
    '''Class to spawn subclasses for analyzing a given executable'''
    def __init__(self, executable, extended=False, anonymous=False):
        super(ExecutableInfo, self).__init__(extended=extended, anonymous=anonymous)
        self.name = "ExecutableInfo"
        self.executable = executable
        self.classlist = [ExecutableInfoExec, ExecutableInfoLibraries]
        clsargs = {"executable" : self.executable}
        self.classargs = [clsargs for i in range(len(self.classlist))]

################################################################################
# Infos about the temperature using coretemp
################################################################################
class CoretempInfoHwmonClassX86(InfoGroup):
    '''Class to read information for one X86 coretemps sensor inside one hwmon entry and device'''
    def __init__(self, sensor, extended=False, anonymous=False, socket=0, hwmon=0):
        super(CoretempInfoHwmonClassX86, self).__init__(extended=extended, anonymous=anonymous)
        base = "/sys/devices/platform/coretemp.{}/hwmon/hwmon{}/".format(socket, hwmon)
        self.name = process_file((pjoin(base, "temp{}_label".format(sensor)),))
        self.addf("Input", pjoin(base, "temp{}_input".format(sensor)), r"(\d+)", int)
        self.required("Input")
        if extended:
            self.addf("Critical", pjoin(base, "temp{}_crit".format(sensor)), r"(\d+)", int)
            self.addf("Alarm", pjoin(base, "temp{}_crit_alarm".format(sensor)), r"(\d+)", int)
            self.addf("Max", pjoin(base, "temp{}_max".format(sensor)), r"(\d+)", int)

class CoretempInfoHwmonX86(PathMatchInfoGroup):
    '''Class to spawn subclasses for one hwmon entry inside a X86 coretemps device'''
    def __init__(self, hwmon, extended=False, anonymous=False, socket=0):
        super(CoretempInfoHwmonX86, self).__init__(extended=extended, anonymous=anonymous)
        self.name = "Hwmon{}".format(hwmon)
        self.subclass = CoretempInfoHwmonClassX86
        self.subargs = {"socket" : socket, "hwmon" : hwmon}
        base = "/sys/devices/platform/coretemp.{}".format(socket)
        self.searchpath = pjoin(base, "hwmon/hwmon{}/temp*_label".format(hwmon))
        self.match = r".*/temp(\d+)_label$"

class CoretempInfoSocketX86(PathMatchInfoGroup):
    '''Class to spawn subclasses for one X86 coretemps device'''
    def __init__(self, socket, extended=False, anonymous=False):
        super(CoretempInfoSocketX86, self).__init__(extended=extended, anonymous=anonymous)
        self.name = "Package{}".format(socket)
        self.socket = socket
        self.subargs = {"socket" : socket}
        self.subclass = CoretempInfoHwmonX86
        self.searchpath = "/sys/devices/platform/coretemp.{}/hwmon/hwmon*".format(self.socket)
        self.match = r".*/hwmon(\d+)$"

class CoretempInfoHwmonClassARM(InfoGroup):
    '''Class to read information for one ARM coretemps sensor inside one hwmon entry'''
    def __init__(self, sensor, extended=False, anonymous=False, hwmon=0):
        super(CoretempInfoHwmonClassARM, self).__init__(extended=extended, anonymous=anonymous)
        base = "/sys/devices/virtual/hwmon/hwmon{}".format(hwmon)
        self.name = "Core{}".format(sensor)
        self.addf("Input", pjoin(base, "temp{}_input".format(sensor)), r"(\d+)", int)
        self.required("Input")
        if extended:
            self.addf("Critical", pjoin(base, "temp{}_crit".format(sensor)), r"(\d+)", int)

class CoretempInfoSocketARM(PathMatchInfoGroup):
    '''Class to spawn subclasses for ARM coretemps for one hwmon entry'''
    def __init__(self, hwmon, extended=False, anonymous=False):
        super(CoretempInfoSocketARM, self).__init__(extended=extended, anonymous=anonymous)
        self.name = "Hwmon{}".format(hwmon)
        self.searchpath = "/sys/devices/virtual/hwmon/hwmon{}/temp*_input".format(hwmon)
        self.match = r".*/temp(\d+)_input$"
        self.subclass = CoretempInfoHwmonClassARM
        self.subargs = {"hwmon" : hwmon}

class CoretempInfo(PathMatchInfoGroup):
    '''Class to spawn subclasses to get all information for coretemps
    X86 path: /sys/devices/platform/coretemp.*
    ARM64 path: /sys/devices/virtual/hwmon/hwmon*
    '''
    def __init__(self, extended=False, anonymous=False):
        super(CoretempInfo, self).__init__(name="CoretempInfo",
                                           extended=extended,
                                           anonymous=anonymous)
        machine = platform.machine()
        if machine in ["x86_64", "i386"]:
            self.subclass = CoretempInfoSocketX86
            self.searchpath = "/sys/devices/platform/coretemp.*"
            self.match = r".*/coretemp\.(\d+)$"
        elif machine in ["aarch64"]:
            self.subclass = CoretempInfoSocketARM
            self.searchpath = "/sys/devices/virtual/hwmon/hwmon*"
            self.match = r".*/hwmon(\d+)$"


################################################################################
# Infos about the BIOS
################################################################################
class BiosInfo(InfoGroup):
    '''Class to read BIOS information (/sys/devices/virtual/dmi/id)'''
    def __init__(self, extended=False, anonymous=False):
        super(BiosInfo, self).__init__(name="BiosInfo",
                                       extended=extended,
                                       anonymous=anonymous)
        base = "/sys/devices/virtual/dmi/id"
        if pexists(base):
            self.addf("BiosDate", pjoin(base, "bios_date"))
            self.addf("BiosVendor", pjoin(base, "bios_vendor"))
            self.addf("BiosVersion", pjoin(base, "bios_version"))
            self.addf("SystemVendor", pjoin(base, "sys_vendor"))
            self.addf("ProductName", pjoin(base, "product_name"))
            if pexists(pjoin(base, "product_vendor")):
                self.addf("ProductVendor", pjoin(base, "product_vendor"))
            self.required(list(self.files.keys()))

################################################################################
# Infos about the thermal zones
################################################################################
class ThermalZoneInfoClass(InfoGroup):
    '''Class to read information for one thermal zone'''
    def __init__(self, zone, extended=False, anonymous=False):
        super(ThermalZoneInfoClass, self).__init__(name="ThermalZone{}".format(zone),
                                                   extended=extended,
                                                   anonymous=anonymous)
        base = "/sys/devices/virtual/thermal/thermal_zone{}".format(zone)
        if pexists(pjoin(base, "device/description")):
            with (open(pjoin(base, "device/description"), "rb")) as filefp:
                self.name = filefp.read().decode(ENCODING).strip()
        self.addf("Temperature", pjoin(base, "temp"), r"(\d+)", int)
        if extended:
            self.addf("Policy", pjoin(base, "policy"), r"(.+)")
            avpath = pjoin(base, "available_policies")
            self.addf("AvailablePolicies", avpath, r"(.+)", tostrlist)
            self.addf("Type", pjoin(base, "type"), r"(.+)")

class ThermalZoneInfo(PathMatchInfoGroup):
    '''Class to read information for thermal zones (/sys/devices/virtual/thermal/thermal_zone*)'''
    def __init__(self, extended=False, anonymous=False):
        spath = "/sys/devices/virtual/thermal/thermal_zone*"
        super(ThermalZoneInfo, self).__init__(name="ThermalZoneInfo",
                                              extended=extended,
                                              anonymous=anonymous,
                                              match=r".*/thermal_zone(\d+)$",
                                              searchpath=spath,
                                              subclass=ThermalZoneInfoClass)

################################################################################
# Infos about CPU vulnerabilities
################################################################################
class VulnerabilitiesInfo(InfoGroup):
    '''Class to read vulnerabilities information (/sys/devices/system/cpu/vulnerabilities)'''
    def __init__(self, extended=False, anonymous=False):
        super(VulnerabilitiesInfo, self).__init__(extended=extended, anonymous=anonymous)
        self.name = "VulnerabilitiesInfo"
        base = "/sys/devices/system/cpu/vulnerabilities"
        for vfile in glob(pjoin(base, "*")):
            vkey = totitle(os.path.basename(vfile))
            self.addf(vkey, vfile)
            self.required(vkey)

################################################################################
# Infos about logged in users (only count to avoid logging user names)
################################################################################
class UsersInfo(InfoGroup):
    '''Class to get count of logged in users. Does not print out the usernames'''
    def __init__(self, extended=False, anonymous=False):
        super(UsersInfo, self).__init__(name="UsersInfo", extended=extended, anonymous=anonymous)
        self.addc("LoggedIn", "users", "", r"(.*)", UsersInfo.countusers)
        self.required("LoggedIn")
    @staticmethod
    def countusers(value):
        if not value or len(value) == 0:
            return 0
        return len(list(set(re.split(r"[,\s]", value))))

################################################################################
# Infos from the dmidecode file (if DMIDECODE_FILE is available)
################################################################################
class DmiDecodeFile(InfoGroup):
    '''Class to read the content of a file containing the output of the dmidecode command which is
    commonly only usable with sufficient permissions. If a system administrator has dumped the
    content to a user readable file, this class includes the file.
    '''
    def __init__(self, dmifile, extended=False, anonymous=False):
        super(DmiDecodeFile, self).__init__(name="DmiDecodeFile",
                                            extended=extended,
                                            anonymous=anonymous)
        if pexists(dmifile):
            self.addf("DmiDecode", dmifile)

################################################################################
# Infos about the CPU affinity
# Some Python versions provide a os.get_schedaffinity()
# If not available, use LIKWID (if allowed)
################################################################################
class CpuAffinity(InfoGroup):
    '''Class to read information the CPU affinity for the session using Python's
    os.get_schedaffinity or likwid-pin if available
    '''
    def __init__(self, extended=False, anonymous=False):
        super(CpuAffinity, self).__init__(name="CpuAffinity",
                                          extended=extended,
                                          anonymous=anonymous)
        if "get_schedaffinity" in dir(os):
            self.const("Affinity", os.get_schedaffinity())
        elif DO_LIKWID and LIKWID_PATH and pexists(LIKWID_PATH):
            abscmd = which("likwid-pin")
            if abscmd and len(abscmd) > 0:
                self.addc("Affinity", abscmd, "-c N -p 2>&1", r"(.*)", tointlist)
                self.required("Affinity")
        else:
            abscmd = which("taskset")
            if abscmd and len(abscmd) > 0:
                regex = r".*current affinity list: (.*)"
                self.addc("Affinity", abscmd, "-c -p $$", regex, tointlist)
                self.required("Affinity")

################################################################################
# Infos about loaded modules in the modules system
################################################################################
class ModulesInfo(InfoGroup):
    '''Class to read information from the modules system'''
    def __init__(self, extended=False, anonymous=False, modulecmd="modulecmd"):
        super(ModulesInfo, self).__init__(name="ModulesInfo",
                                          extended=extended,
                                          anonymous=anonymous)
        parse = ModulesInfo.parsemodules
        cmd_opts = "sh list -t 2>&1"
        cmd = modulecmd
        abspath = which(cmd)
        if modulecmd is not None and len(modulecmd) > 0:
            path = "{}".format(modulecmd)
            path_opts = "{}".format(cmd_opts)
            if " " in path:
                tmplist = path.split(" ")
                path = which(tmplist[0])
                path_opts = "{} {}".format(" ".join(tmplist[1:]), path_opts)
            else:
                path = which(cmd)
            abscmd = path
            cmd_opts = path_opts
        if abscmd and len(abscmd) > 0:
            self.addc("Loaded", abscmd, cmd_opts, None, parse)
    @staticmethod
    def parsemodules(value):
        slist = re.split("\n", value)
        return slist[1:]

################################################################################
# Infos about interrupt handling
# see https://pyperf.readthedocs.io/en/latest/system.html#system-cmd-ops
################################################################################
class IrqAffinityClass(InfoGroup):
    '''Class to read information about one interrupt affinity'''
    def __init__(self, irq, extended=False, anonymous=False):
        super(IrqAffinityClass, self).__init__(name="irq{}".format(irq),
                                               extended=extended,
                                               anonymous=anonymous)
        self.addf("SMPAffinity", "/proc/irq/{}/smp_affinity".format(irq), parse=masktolist)

class IrqAffinity(PathMatchInfoGroup):
    '''Class to read information about one interrupt affinity'''
    def __init__(self, extended=False, anonymous=False):
        super(IrqAffinity, self).__init__(name="IrqAffinity",
                                          extended=extended,
                                          anonymous=anonymous,
                                          searchpath="/proc/irq/*",
                                          match=r".*/(\d+)",
                                          subclass=IrqAffinityClass)
        self.addf("DefaultSMPAffinity", "/proc/irq/default_smp_affinity", parse=masktolist)


################################################################################
# Infos about InfiniBand adapters
################################################################################
class InfinibandInfoClassPort(InfoGroup):
    '''Class to read the information of a single port of an InfiniBand/OmniPath driver.'''
    def __init__(self, port, extended=False, anonymous=False, driver=""):
        super(InfinibandInfoClassPort, self).__init__(extended=extended, anonymous=anonymous)
        self.name = "Port{}".format(port)
        ibpath = "/sys/class/infiniband/{}/ports/{}".format(driver, port)
        self.addf("Rate", pjoin(ibpath, "rate"), r"(.+)")
        self.addf("PhysState", pjoin(ibpath, "phys_state"), r"(.+)")
        self.addf("LinkLayer", pjoin(ibpath, "link_layer"), r"(.+)")


class InfinibandInfoClass(PathMatchInfoGroup):
    '''Class to read the information of an InfiniBand/OmniPath driver.'''
    def __init__(self, driver, extended=False, anonymous=False):
        super(InfinibandInfoClass, self).__init__(extended=extended, anonymous=anonymous)
        self.name = driver
        ibpath = "/sys/class/infiniband/{}".format(driver)
        self.addf("BoardId", pjoin(ibpath, "board_id"), r"(.+)")
        self.addf("FirmwareVersion", pjoin(ibpath, "fw_ver"), r"([\d\.]+)")
        self.addf("HCAType", pjoin(ibpath, "hca_type"), r"([\w\d\.]+)")
        self.addf("HWRevision", pjoin(ibpath, "hw_rev"), r"([\w\d\.]+)")
        self.addf("NodeType", pjoin(ibpath, "node_type"), r"(.+)")

        if not anonymous:
            self.addf("NodeGUID", pjoin(ibpath, "node_guid"), r"(.+)")
            self.addf("NodeDescription", pjoin(ibpath, "node_desc"), r"(.+)")
            self.addf("SysImageGUID", pjoin(ibpath, "sys_image_guid"), r"(.+)")
        self.searchpath = "/sys/class/infiniband/{}/ports/*".format(driver)
        self.match = r".*/(\d+)$"
        self.subclass = InfinibandInfoClassPort
        self.subargs = {"driver" : driver}

class InfinibandInfo(PathMatchInfoGroup):
    '''Class to read InfiniBand/OmniPath (/sys/class/infiniband).'''
    def __init__(self, extended=False, anonymous=False):
        super(InfinibandInfo, self).__init__(extended=extended, anonymous=anonymous)
        self.name = "InfinibandInfo"
        if pexists("/sys/class/infiniband"):
            self.searchpath = "/sys/class/infiniband/*"
            self.match = r".*/(.*)$"
            self.subclass = InfinibandInfoClass

################################################################################
# Infos from nvidia-smi (Nvidia GPUs)
################################################################################
class NvidiaSmiInfoClass(InfoGroup):
    '''Class to read information for one Nvidia GPU (uses the nvidia-smi command)'''
    def __init__(self, device, extended=False, anonymous=False, nvidia_path=""):
        super(NvidiaSmiInfoClass, self).__init__(name="Card{}".format(device),
                                                 extended=extended,
                                                 anonymous=anonymous)
        cmd = pjoin(nvidia_path, "nvidia-smi")
        if pexists(cmd):
            self.cmd = cmd
        elif which("nvidia-smi"):
            self.cmd = which("nvidia-smi")
        self.cmd_opts = "-q -i {}".format(device)
        abscmd = which(self.cmd)
        matches = {"ProductName" : r"\s+Product Name\s+:\s+(.+)",
                   "VBiosVersion" : r"\s+VBIOS Version\s+:\s+(.+)",
                   "ComputeMode" : r"\s+Compute Mode\s+:\s+(.+)",
                   "GPUCurrentTemp" : r"\s+GPU Current Temp\s+:\s+(\d+\sC)",
                   "MemTotal" : r"\s+Total\s+:\s+(\d+\sMiB)",
                   "MemFree" : r"\s+Free\s+:\s+(\d+\sMiB)",
                  }
        extmatches = {"PciDevice" : r"^GPU\s+([0-9a-fA-F:]+)",
                      "PciLinkWidth" : r"\s+Current\s+:\s+(\d+x)",
                      "GPUMaxOpTemp" : r"\s+GPU Max Operating Temp\s+:\s+(\d+\sC)",
                     }
        if abscmd:
            for key, regex in matches.items():
                self.addc(key, self.cmd, self.cmd_opts, regex)
            if extended:
                for key, regex in extmatches.items():
                    self.addc(key, self.cmd, self.cmd_opts, regex)

class NvidiaSmiInfo(ListInfoGroup):
    '''Class to spawn subclasses for each NVIDIA GPU device (uses the nvidia-smi command)'''
    def __init__(self, nvidia_path="", extended=False, anonymous=False):
        super(NvidiaSmiInfo, self).__init__(name="NvidiaInfo",
                                            extended=extended,
                                            anonymous=anonymous)
        self.cmd = "nvidia-smi"
        cmd = pjoin(nvidia_path, "nvidia-smi")
        if pexists(cmd):
            self.cmd = cmd
        self.cmd_opts = "-q"
        abscmd = which(self.cmd)
        if abscmd:
            num_gpus = process_cmd((self.cmd, self.cmd_opts, r"Attached GPUs\s+:\s+(\d+)", int))
            if num_gpus > 0:
                self.userlist = [i for i in range(num_gpus)]
                self.subclass = NvidiaSmiInfoClass
                self.subargs = {"nvidia_path" : nvidia_path}
        matches = {"DriverVersion" : r"Driver Version\s+:\s+([\d\.]+)",
                   "CudaVersion" : r"CUDA Version\s+:\s+([\d\.]+)",
                  }
        if abscmd:
            for key, regex in matches.items():
                self.addc(key, self.cmd, self.cmd_opts, regex)


################################################################################
# Infos from veosinfo (NEC Tsubasa)
################################################################################
class NecTsubasaInfoTemps(InfoGroup):
    '''Class to read temperature information for one NEC Tsubasa device (uses the vecmd command)'''
    def __init__(self, tempkeys, vecmd_path="", extended=False, anonymous=False, device=0):
        super(NecTsubasaInfoTemps, self).__init__(extended=extended, anonymous=anonymous)
        self.name = "Temperatures"
        vecmd = pjoin(vecmd_path, "vecmd")
        veargs = "-N {} info".format(device)
        for tempkey in tempkeys:
            self.addc(tempkey, vecmd, veargs, r"\s+{}\s+:\s+([\d\.]+\sC)".format(tempkey))

class NecTsubasaInfoClass(InfoGroup):
    '''Class to read information for one NEC Tsubasa device (uses the vecmd command)'''
    def __init__(self, device, vecmd_path="", extended=False, anonymous=False):
        super(NecTsubasaInfoClass, self).__init__(extended=extended, anonymous=anonymous)
        self.name = "Card{}".format(device)
        vecmd = pjoin(vecmd_path, "vecmd")
        veargs = "-N {} info".format(device)
        if pexists(vecmd):
            self.addc("State", vecmd, veargs, r"VE State\s+:\s+(.+)", totitle)
            self.addc("Model", vecmd, veargs, r"VE Model\s+:\s+(\d+)")
            self.addc("ProductType", vecmd, veargs, r"Product Type\s+:\s+(\d+)")
            self.addc("DriverVersion", vecmd, veargs, r"VE Driver Version\s+:\s+([\d\.]+)")
            self.addc("Cores", vecmd, veargs, r"Cores\s+:\s+(\d+)")
            self.addc("MemTotal", vecmd, veargs, r"Memory Size\s+:\s+(\d+)")
            if extended:
                regex = r"Negotiated Link Width\s+:\s+(x\d+)"
                self.addc("PciLinkWidth", vecmd, veargs, regex)
            ve_temps = process_cmd((vecmd, veargs, None, NecTsubasaInfoClass.gettempkeys))
            tempargs = {"device" : device, "vecmd_path" : vecmd_path}
            cls = NecTsubasaInfoTemps(ve_temps, extended=extended, anonymous=anonymous, **tempargs)
            self._instances.append(cls)
    @staticmethod
    def gettempkeys(value):
        keys = []
        for line in re.split("\n", value):
            if re.match(r"(.+):\s+[\d\.]+\sC$", line):
                key = re.match(r"(.+):\s+[\d\.]+\sC$", line).group(1).strip()
                keys.append(key)
        return keys


class NecTsubasaInfo(ListInfoGroup):
    '''Class to spawn subclasses for each NEC Tsubasa device (uses the vecmd command)'''
    def __init__(self, vecmd_path="", extended=False, anonymous=False):
        super(NecTsubasaInfo, self).__init__(name="NecTsubasaInfo",
                                             extended=extended,
                                             anonymous=anonymous)
        vecmd = pjoin(vecmd_path, "vecmd")
        if not pexists(vecmd):
            vecmd = which("vecmd")
            if vecmd is not None:
                vecmd_path = os.path.dirname(vecmd)
        if vecmd and len(vecmd) > 0:
            num_ves = process_cmd((vecmd, "info", r"Attached VEs\s+:\s+(\d+)", int))
            if num_ves > 0:
                self.userlist = [i for i in range(num_ves)]
                self.subclass = NecTsubasaInfoClass
                self.subargs = {"vecmd_path" : vecmd_path}


################################################################################
# Skript code
################################################################################

def read_cli(cliargs):
    # Create CLI parser
    desc = 'Reads and outputs system information as JSON document'
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('-e', '--extended', action='store_true', default=False,
                        help='extended output (default: False)')
    parser.add_argument('-a', '--anonymous', action='store_true', default=False,
                        help='Remove host-specific information (default: False)')
    parser.add_argument('-c', '--config', default=False, action='store_true',
                        help='print configuration as JSON (files, commands, ...)')
    parser.add_argument('-s', '--sort', action='store_true', default=False,
                        help='sort JSON output (default: False)')
    parser.add_argument('-i', '--indent', default=4, type=int,
                        help='indention in JSON output (default: 4)')
    parser.add_argument('-o', '--output', help='save JSON to file (default: stdout)', default=None)
    parser.add_argument('-j', '--json', help='compare given JSON with current state', default=None)
    parser.add_argument('--configfile', help='Location of configuration file', default=None)
    parser.add_argument('executable', help='analyze executable (optional)', nargs='?', default=None)
    pargs = vars(parser.parse_args(cliargs))

    # Check if executable exists and is executable
    if pargs["executable"] is not None:
        abspath = which(pargs["executable"])
        if abspath is None or not pexists(abspath):
            raise ValueError("Executable '{}' does not exist".format(pargs["executable"]))
        if not os.access(abspath, os.X_OK):
            raise ValueError("Executable '{}' is not executable".format(pargs["executable"]))
    # Check if JSON file exists and is readable
    if pargs["json"] is not None:
        if not pexists(pargs["json"]):
            raise ValueError("JSON document '{}' does not exist".format(pargs["json"]))
        if not os.access(pargs["json"], os.R_OK):
            raise ValueError("JSON document '{}' is not readable".format(pargs["json"]))
    # Check if configuration file exists and is readable
    if pargs["configfile"] is not None:
        if not pexists(pargs["configfile"]):
            raise ValueError("Configuration file '{}' does not exist".format(pargs["configfile"]))
        if not os.access(pargs["configfile"], os.R_OK):
            raise ValueError("Configuration file '{}' is not readable".format(pargs["configfile"]))
    return pargs

def read_config(config={"extended" : False, "anonymous" : False, "executable" : None}):

    if not ("extended" in config and "anonymous" in config and "executable" in config):
        raise ValueError("Given dict does not contain required keys: \
                          extended, anonymous and executable")
    configdict = {"dmifile" : DMIDECODE_FILE,
                  "likwid_enable" : DO_LIKWID,
                  "likwid_path" : LIKWID_PATH,
                  "modulecmd" : MODULECMD_PATH,
                  "vecmd_path" : VEOS_BASE,
                  "nvidia_path" : NVIDIA_PATH,
                  "debug" : DEBUG_OUTPUT,
                  "anonymous" : False,
                  "extended" : False,
                 }
    searchfiles = []

    userfile = config.get("configfile", None)
    configdict["anonymous"] = config.get("anonymous", False)
    configdict["extended"] = config.get("extended", False)
    configdict["executable"] = config.get("executable", None)

    if userfile is not None:
        searchfiles.append(userfile)
    else:
        searchfiles = [pjoin(os.getcwd(), ".machinestate")]
        if "HOME" in os.environ:
            searchfiles.append(pjoin(os.environ["HOME"], ".machinestate"))
        searchfiles.append("/etc/machinestate.conf")
    for sfile in searchfiles:
        if pexists(sfile):
            sfp = fopen(sfile)
            if sfp:
                sstr = sfp.read().decode(ENCODING)
                if len(sstr) > 0:
                    try:
                        tmpdict = json.loads(sstr)
                        configdict.update(tmpdict)
                    except:
                        exce = "Configuration file '{}' not valid JSON".format(userfile)
                        raise ValueError(exce)
                sfp.close()
                break



    return configdict

def main():
    try:
        # Read command line arguments
        cliargs = read_cli(sys.argv[1:])
        # Read configuration from configuration file
        runargs = read_config(cliargs)
    except Exception as e:
        print(e)
        sys.exit(1)

    # Initialize MachineState class
    mstate = MachineState(**runargs)
    # Generate subclasses of MachineState
    mstate.generate()
    # Update the current state
    mstate.update()

    # Compare a given JSON document (previously created with the same script)
    if cliargs["json"] is not None:
        if mstate == cliargs["json"]:
            print("Current state matches with input file")
        else:
            print("The current state differs at least in one setting with input file")
        sys.exit(0)

    # Get JSON document string (either from the configuration or the state)
    jsonout = {}
    if not cliargs["config"]:
        jsonout = mstate.get_json(sort=cliargs["sort"], intend=cliargs["indent"])
    else:
        jsonout = mstate.get_config(sort=cliargs["sort"], intend=cliargs["indent"])

    # Determine output destination
    if not cliargs["output"]:
        print(jsonout)
    else:
        with open(cliargs["output"], "w") as outfp:
            outfp.write(mstate.get_json(sort=cliargs["sort"], intend=cliargs["indent"]))
            outfp.write("\n")
    sys.exit(0)

#    # This part is for testing purposes
#    n = OSInfo(extended=cliargs["extended"])
#    n.generate()
#    n.update()
#    ndict = n.get()
#    copydict = deepcopy(ndict)
#    print(n == copydict)
#    print(n.get_json(sort=cliargs["sort"], intend=cliargs["indent"]))

__main__ = main
if __name__ == "__main__":
    main()
