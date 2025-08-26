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
- OperatingSystemInfo
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
- ModulesInfo (if modulecmd command is present)
- NvidiaInfo (if nvidia-smi command is present)
- NecTsubasaInfo (if vecmd command is present)
- OpenCLInfo (if clinfo command is present)
- PrefetcherInfo (if likwid-features command is present)
- TurboInfo (if likwid-powermeter command is present)
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
import struct
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
# from shutil import which
from getpass import getuser
from grp import getgrgid
import inspect
import logging
import uuid
from .CpuInfo import CpuInfo, CpuTopology
import shutil

def which(cmd: str) -> str | None:
    """Cross-platform wrapper for shutil.which."""
    return shutil.which(cmd)
from .DmiDecodeFile import DmiDecodeFile
from .MpiInfo import MpiInfo
from .ShellEnvironment import ShellEnvironment
from .PythonInfo import PythonInfo
from .HostInfo import HostInfo
from .OperatingSystemInfo import OperatingSystemInfo, OSInfoMacOS
from .KernelInfo import KernelInfo
from .Uptime import Uptime, UptimeMacOs
from .LoadAvg import LoadAvg
from .MemInfo import MemInfo, MemInfoMacOS
from .CgroupInfo import CgroupInfo
from .WritebackWorkqueue import WritebackWorkqueue
from .CpuFrequency import CpuFrequency, CpuFrequencyMacOs
from .NumaBalance import NumaBalance
from .NumaInfo import NumaInfo, NumaInfoMacOS
from .CacheTopology import CacheTopology, CacheTopologyMacOS
from .TransparentHugepages import TransparentHugepages
from .PowercapInfo import PowercapInfo
from .Hugepages import Hugepages
from .CompilerInfo import CompilerInfo
from .ClocksourceInfo import ClocksourceInfo
from .CoretempInfo import CoretempInfo
from .BiosInfo import BiosInfo
from .ThermalZoneInfo import ThermalZoneInfo
from .VulnerabilitiesInfo import VulnerabilitiesInfo
from .UsersInfo import UsersInfo
from .IrqAffinity import IrqAffinity
from .CpuAffinity import CpuAffinity
from .ModulesInfo import ModulesInfo
from .NvidiaSmiInfo import NvidiaSmiInfo
from .NecTsubasaInfo import NecTsubasaInfo
from .OpenCLInfo import OpenCLInfo
from .PrefetcherInfo import PrefetcherInfo
from .TurboInfo import TurboInfo
from .DmiDecodeFile import DmiDecodeFile
from .common import InfoGroup, ListInfoGroup, MultiClassInfoGroup, process_cmd, which, pexists, re, os
from .CpuTopology import CpuTopology, CpuTopologyMacOS
from .WritebackInfo import WritebackInfo
from .ExecutableInfo import ExecutableInfo
from .CpuInfo import CpuInfoMacOS
from .LoadAvg import LoadAvgMacOs



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
# The OpenCLInfo class requires this path if clinfo is not in $PATH
CLINFO_PATH = "/usr/bin"

################################################################################
# Version information
################################################################################
MACHINESTATE_VERSION = "0.6.0"
MACHINESTATE_SCHEMA_VERSION = "v1"
__version__ = MACHINESTATE_VERSION

################################################################################
# Constants
################################################################################
ENCODING = getpreferredencoding()

DEFAULT_LOGLEVEL = "info"
NEWLINE_REGEX = re.compile(r"\n")

################################################################################
# Helper functions
################################################################################

def fopen(filename):
    if filename is not None and pexists(filename) and os.path.isfile(filename):
        try:
            filefp = open(filename, "rb")
        except PermissionError:
            logging.debug("Not enough permissions to read file %s", filename)
            return None
        except Exception as e:
            logging.error("File %s open: %s", filename, e)
            return None
        return filefp
    elif filename is None:
        logging.debug("Filename is None")
    elif not pexists(filename):
        logging.debug("Target of filename (%s) does not exist", filename)
    elif not os.path.isfile(filename):
        logging.debug("Target of filename (%s) is no file", filename)
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
        return re.split(r"[,\s\|]+", value)

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


def int_from_str(s):
    """Parse int from string, either hex with leading 0x or plain integer."""
    if re.match(r'0x[0-9a-fA-F]+', s):
        return int(s, base=16)
    else:
        return int(s)


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
        try:
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
        except OSError as e:
            sys.stderr.write("Failed to read file {}: {}\n".format(fname, e))
        finally:
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
            try:
                rawdata = filefp.read()
                data = rawdata.decode(ENCODING)
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
            except OSError as e:
                sys.stderr.write("Failed to read file {}: {}\n".format(fname, e))
            finally:
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
# Classes for single operations
################################################################################

class BaseOperation:
    def __init__(self, regex=None, parser=None, required=False, tolerance=None):
        self.regex = regex
        self.parser = parser
        self.required = required
        self.tolerance = tolerance
    def valid(self):
        return False
    def ident(self):
        return None
    def match(self, data):
        out = data
        if self.regex is not None:
            regex = re.compile(self.regex)
            m = None
            for l in NEWLINE_REGEX.split(data):
                m = regex.match(l)
                if m:
                    out = m.group(1)
                    break
                else:
                    m = regex.search(l)
                    if m:
                        out = m.group(1)
                        break
            if not m:
                out = ""
                self.parser = None
        return out
    def parse(self, data):
        out = data
        if self.parser is not None:
            if callable(self.parser):
                try:
                    if isinstance(data, str) and data.startswith("0x"):
                        # Convert hexadecimal string to integer
                        out = int(data, 16)
                    else:
                        out = self.parser(data)
                except ValueError as e:
                    print(f"Error parsing data: {data}. Exception: {e}")
                    raise
        return out
    def update(self):
        return None
    def get(self):
        d = self.update()
        logging.debug("Update '%s'", str(d))
        if self.match:
            d = self.match(d)
            logging.debug("Match '%s'", str(d))
        if self.parse:
            d = self.parse(d)
            logging.debug("Parse '%s'", str(d))
        return d
    def _init_args(self):
        """Get list of tuples with __init__ arguments"""
        parameters = inspect.signature(self.__init__).parameters.values()
        arglist = [
            (p.name, getattr(self, p.name))
            for p in parameters
            if p.default is not getattr(self, p.name)
        ]
        return arglist

    def __repr__(self):
        cls = str(self.__class__.__name__)
        args = ", ".join(["{}={!r}".format(k,v) for k,v in self._init_args()])
        return "{}({})".format(cls, args)

class Constant(BaseOperation):
    def __init__(self, value, required=False, tolerance=None):
        super(Constant, self).__init__(regex=None,
                                       parser=None,
                                       required=required,
                                       tolerance=tolerance)
        self.value = value
    def ident(self):
        return uuid.uuid4()
    def valid(self):
        return True
    def update(self):
        return self.value


class File(BaseOperation):
    def __init__(self, path, regex=None, parser=None, required=False, tolerance=None):
        super(File, self).__init__(regex=regex,
                                   parser=parser,
                                   required=required,
                                   tolerance=tolerance)
        self.path = path
    def ident(self):
        return self.path
    def valid(self):
        res = super(File, self).valid()
        if os.access(self.path, os.R_OK):
            try:
                filefp = fopen(self.path)
                data = filefp.read(1)
                filefp.close()
                res = True
            except BaseException as e:
                logging.debug("File %s not valid: %s", self.path, e)
                pass
        #logging.debug("File %s valid: %s", self.path, res)
        return res
    def update(self):
        data = None
        logging.debug("Read file %s", self.path)
        filefp = fopen(self.path)
        if filefp:
            try:
                data = filefp.read().decode(ENCODING).strip()
            except OSError as e:
                logging.error("Failed to read file %s: %s", self.path, e)
            finally:
                filefp.close()
        return data

class Command(BaseOperation):
    def __init__(self, cmd, cmd_args, regex=None, parser=None, required=False, tolerance=None):
        super(Command, self).__init__(regex=regex,
                                      parser=parser,
                                      required=required,
                                      tolerance=tolerance)
        self.cmd = cmd
        self.abscmd = self.cmd if os.access(self.cmd, os.X_OK) else which(self.cmd)
        self.cmd_args = cmd_args
    def ident(self):
        return "{} {}".format(self.cmd, self.cmd_args)
    def valid(self):
        res = super(Command, self).valid()
        if self.abscmd:
            if os.access(self.abscmd, os.X_OK):
                res = True
            if self.abscmd and len(self.abscmd):
                res = True
        #logging.debug("Command %s valid: %s", self.abscmd, res)
        return res
    def update(self):
        data = None
        if self.valid():
            logging.debug("Exec command %s %s", self.abscmd, self.cmd_args)
            exe = "LANG=C {} {}; exit 0;".format(self.abscmd, self.cmd_args)
            data = check_output(exe, stderr=DEVNULL, shell=True).decode(ENCODING).strip()
        return data

################################################################################
# Base Classes
################################################################################



class InfoGroup:
    def __init__(self, name=None, extended=False, anonymous=False):
        # Holds subclasses
        self._instances = []
        # Holds operations of this class instance
        self._operations = {}
        # Holds the data of this class instance
        self._data = {}
        # Space for file reads (deprecated)
        # Key -> (filename, regex_with_one_group, convert_function)
        # If regex_with_one_group is None, the whole content of filename is passed to
        # convert_function. If convert_function is None, the output is saved as string
        self.files = {}
        # Space for commands for execution (deprecated)
        # Key -> (executable, exec_arguments, regex_with_one_group, convert_function)
        # If regex_with_one_group is None, the whole content of filename is passed to
        # convert_function. If convert_function is None, the output is saved as string
        self.commands = {}
        # Space for constants (deprecated)
        # Key -> Value
        self.constants = {}
        # Keys in the group that are required to check equality (deprecated)
        self.required4equal = []
        # Set attributes
        self.name = name
        self.extended = extended
        self.anonymous = anonymous

    @classmethod
    def from_dict(cls, data):
        """Initialize from data dictionary produced by `get(meta=True)`"""
        if isinstance(data, dict) and not data.get('_meta', "").startswith(cls.__name__):
            raise ValueError("`from_dict` musst be called on class matching `_meta` (call get(meta=True)).")
        if isinstance(data, InfoGroup):
            data = data.get(meta=True)
        intmatch = re.compile(r"^(.*)=([\d]+)$")
        floatmatch = re.compile(r"^(.*)=([\d\.eE+\-]+)$")
        strmatch = re.compile(r"^(.*)='(.*)'$")
        nonematch = re.compile(r"^(.*)='None'$")
        truematch = re.compile(r"^(.*)='True'$")
        falsematch = re.compile(r"^(.*)='False'$")
        anymatch = re.compile(r"^(.*)=(.*)$")
        mmatch = r"{}\((.*)\)".format(cls.__name__)
        m = re.match(mmatch, data['_meta'])
        initargs = {}
        if m:
            argstring = m.group(1)
            for astr in [ x.strip() for x in argstring.split(",") if len(x) > 0]:
                k = None
                v = None
                if intmatch.match(astr):
                    k,v = intmatch.match(astr).groups()
                    v = int(v)
                elif floatmatch.match(astr):
                    k,v = floatmatch.match(astr).groups()
                    v = float(v)
                elif nonematch.match(astr):
                    k = nonematch.match(astr).group(1)
                    v = None
                elif truematch.match(astr):
                    k = truematch.match(astr).group(1)
                    v = True
                elif falsematch.match(astr):
                    k = falsematch.match(astr).group(1)
                    v = False
                elif strmatch.match(astr):
                    k,v = strmatch.match(astr).groups()
                    v = str(v)
                elif anymatch.match(astr):
                    k,v = anymatch.match(astr).groups()
                    v = str(v)
                if v == "None": v = None
                if v == "True": v = True
                if v == "False": v = False
                if k is not None:
                    initargs[k] = v

        c = cls(**dict(initargs))
        validkeys = list(c._operations.keys())
        for key, value in data.items():
            if isinstance(value, dict) and '_meta' in value:
                clsname = value['_meta'].split("(")[0]
                c._instances.append(
                    getattr(sys.modules[__name__], clsname).from_dict(value))
            elif key in validkeys or key in [n.name for n in c._instances]:
                c._data[key] = value
        return c

    def addf(self, key, filename, match=None, parse=None, extended=False):
        """Add file to object including regex and parser"""
        self._operations[key] = File(filename, regex=match, parser=parse)
    def addc(self, key, cmd, cmd_opts=None, match=None, parse=None, extended=False):
        """Add command to object including command options, regex and parser"""
        self._operations[key] = Command(cmd, cmd_opts, regex=match, parser=parse)
    def const(self, key, value):
        """Add constant value to object"""
        self._operations[key] = Constant(value)
    def required(self, *args):
        """Add item(s) to list of required fields at comparison"""
        if args:
            for arg in args:
                if isinstance(arg, list):
                    for subarg in arg:
                        if subarg in self._operations:
                            self._operations[subarg].required = True
                elif isinstance(arg, str):
                    if arg in self._operations:
                        self._operations[arg].required = True

    def generate(self):
        '''Generate subclasses, defined by derived classes'''
        pass

    def update(self):
        '''Read object's files and commands. Triggers update() of subclasses'''
        outdict = { k: None for (k,v) in self._operations.items()}
        for key, op in self._operations.items():
            if op.valid() and outdict[key] is None:
                logging.debug("Updating key '%s'", key)
                data = op.update()
                if data is not None:
                    for subkey, subop in self._operations.items():
                        if not subop.valid(): continue
                        if outdict[subkey] is not None: continue
                        if key != subkey and op.ident() == subop.ident():
                            logging.debug("Updating subkey '%s'", subkey)
                            subdata = subop.match(data)
                            subdata = subop.parse(subdata)
                            outdict[subkey] = subdata
                    data = op.match(data)
                    data = op.parse(data)
                    outdict[key] = data
        for inst in self._instances:
            inst.update()
        self._data.update(outdict)

    def get(self, meta=False):
        """Get the object's and all subobjects' data as dict"""
        outdict = { k: None for (k,v) in self._operations.items()}
        for inst in self._instances:
            clsout = inst.get(meta=meta)
            outdict.update({inst.name : clsout})
        outdict.update(self._data)
        if meta:
            outdict["_meta"] = self.__repr__()
        return outdict
    def get_html(self, level=0):
        """Get the object's and all subobjects' data as collapsible HTML table used by get_html()"""
        s = ""
        s += "<button class=\"accordion\">{}</button>\n".format(self.name)
        s += "<div class=\"panel\">\n<table style=\"width:100vw\">\n"
        for k,v in self._data.items():
            if isinstance(v, list):
                s += "<tr>\n<td style=\"width: 20%\"><b>{}:</b></td>\n<td>{}</td>\n</tr>\n".format(k, ", ".join([str(x) for x in v]))
            else:
                s += "<tr>\n<td style=\"width: 20%\"><b>{}:</b></td>\n<td>{}</td>\n</tr>\n".format(k, v)
        for inst in self._instances:
            if len(self._data) > 0 and level > 0:
                s += "<tr>\n<td colspan=\"2\">\n{}</td>\n</tr>".format(inst.get_html(level+1))
            else:
                s += "<tr>\n<td>{}</td>\n</tr>".format(inst.get_html(level+1))
        s += "</table>\n</div>\n"
        return s

    def get_json(self, sort=False, intend=4, meta=True):
        """Get the object's and all subobjects' data as JSON document (string)"""
        outdict = self.get(meta=meta)
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

    def compare(self, other):
        """Compare object with another object-like structure like Class,
           dict, JSON document or path to JSON file"""
        self_meta = False
        def valuecmp(key, cls, left, right):
            """Compare two values used only internally in __eq__"""
            tcase = TestCase()
            estr = "key '{}' for class {}".format(key, cls)
            if isinstance(left, str) and isinstance(right, str):
                lmatch = re.match(r"^([\d\.]+).*", left)
                rmatch = re.match(r"^([\d\.]+).*", right)
                if lmatch and rmatch:
                    try:
                        left = float(lmatch.group(1))
                        right = float(rmatch.group(1))
                    except:
                        pass
            if ((isinstance(left, int) and isinstance(right, int)) or
                (isinstance(left, float) and isinstance(right, float))):
                try:
                    tcase.assertAlmostEqual(left, right, delta=left*0.2)
                except BaseException as exce:
                    print("ERROR: AlmostEqual check failed for {} (delta +/- 20%): {} <-> {}".format(estr, left, right))
                    return False
            elif left != right:
                print("ERROR: Equality check failed for {}: {} <-> {}".format(estr, left, right))
                return False
            return True

        # Load the other object
        if isinstance(other, str):
            if pexists(other):
                jsonfp = fopen(other)
                if jsonfp:
                    other = jsonfp.read().decode(ENCODING)
                    jsonfp.close()
            try:
                otherdict = json.loads(other)
                self_meta = True
            except:
                raise ValueError("`__eq__` musst be called on InfoGroup class, \
                                  dict, JSON or path to JSON file.")
        elif isinstance(other, InfoGroup):
            otherdict = other.get(meta=True)
            self_meta = True
        elif isinstance(other, dict):
            otherdict = other
            if "_meta" in otherdict:
                self_meta = True
        elif self.get() is None and other is None:
            return True
        else:
            raise ValueError("`__eq__` musst be called on InfoGroup class, dict, \
                              JSON or path to JSON file.")
        # After here only dicts allowed
        selfdict = self.get(meta=self_meta)
        clsname = self.__class__.__name__
        key_not_found = 'KEY_NOT_FOUND_IN_OTHER_DICT'
        instnames = [ inst.name for inst in self._instances ]
        selfkeys = [ k for k in selfdict if k not in instnames ]
        required4equal = [k for k in self._operations if self._operations[k].required]
        otherkeys = [ k for k in otherdict if k not in instnames ]

        if set(selfkeys) & set(required4equal) != set(required4equal):
            print("Required keys missing in object: {}".format(
                  ", ".join(set(required4equal) - set(selfkeys)))
                 )
        if set(otherkeys) & set(required4equal) != set(required4equal):
            print("Required keys missing in compare object: {}".format(
                  ", ".join(set(required4equal) - set(otherkeys)))
                 )

        inboth = set(selfkeys) & set(otherkeys)
        diff = {k:(selfdict[k], otherdict[k])
                for k in inboth
                if ((not valuecmp(k, clsname, selfdict[k], otherdict[k]))
                     and k in required4equal
                   )
               }
        diff.update({k:(selfdict[k], key_not_found)
                     for k in set(selfkeys) - inboth
                     if k in required4equal
                    })
        diff.update({k:(key_not_found, otherdict[k])
                     for k in set(otherkeys) - inboth
                     if k in required4equal
                    })
        for inst in self._instances:
            if inst.name in selfdict and inst.name in otherdict:
                instdiff = inst.compare(otherdict[inst.name])
                if len(instdiff) > 0:
                    diff[inst.name] = instdiff
        return diff
    def __eq__(self, other):
        diff = self.compare(other)
        return len(diff) == 0
    def _init_args(self):
        """Get list of tuples with __init__ arguments"""
        parameters = inspect.signature(self.__init__).parameters.values()
        arglist = [
            (p.name, getattr(self, p.name))
            for p in parameters
            if p.default is not getattr(self, p.name)
        ]
        return arglist

    def __repr__(self):
        cls = str(self.__class__.__name__)
        args = ", ".join(["{}={!r}".format(k,v) for k,v in self._init_args()])
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
        self.userlist = userlist or []
        if isinstance(subclass, str) or isinstance(subclass, int) or isinstance(subclass, bool):
            self.subclass = None
        else:
            self.subclass = subclass
        self.subargs = subargs if isinstance(subargs, dict) else {}

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
                 loglevel=DEFAULT_LOGLEVEL,
                 dmifile=DMIDECODE_FILE,
                 likwid_enable=DO_LIKWID,
                 likwid_path=LIKWID_PATH,
                 nvidia_path=NVIDIA_PATH,
                 modulecmd=MODULECMD_PATH,
                 vecmd_path=VEOS_BASE,
                 clinfo_path=CLINFO_PATH):
        super(MachineState, self).__init__(extended=extended, anonymous=anonymous)
        self.loglevel = loglevel
        self.dmifile = dmifile
        self.likwid_enable = likwid_enable
        self.executable = executable
        self.likwid_path = likwid_path
        self.nvidia_path = nvidia_path
        self.modulecmd = modulecmd
        self.vecmd_path = vecmd_path
        self.clinfo_path = clinfo_path
        ostype = get_ostype()
        if ostype == "Linux":
            self.classlist = [
                MachineStateInfo,
                HostInfo,
                CpuInfo,
                OperatingSystemInfo,
                KernelInfo,
                Uptime,
                CpuTopology,
                NumaBalance,
                LoadAvg,
                MemInfo,
                CgroupInfo,
                WritebackInfo,
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
            self.classlist.append(OpenCLInfo)
            self.classargs.append({"clinfo_path" : clinfo_path})
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
            self.classlist.append(OpenCLInfo)
            self.classargs.append({"clinfo_path" : clinfo_path})

    def get_config(self, sort=False, intend=4):
        outdict = {}
        for inst in self._instances:
            clsout = inst.get_config()
            outdict.update({inst.name : clsout})
        return json.dumps(outdict, sort_keys=sort, indent=intend)

    def get_html(self, level=0):
        s = ""
        s += "<table style=\"width:100vw\">\n"
#        for k,v in self._data.items():
#            if isinstance(v, list):
#                s += "<tr>\n\t<td>{}</td>\n\t<td>{}</td>\n</tr>\n".format(k, ", ".join([str(x) for x in v]))
#            else:
#                s += "<tr>\n\t<td>{}</td>\n\t<td>{}</td>\n</tr>\n".format(k, v)
        for inst in self._instances:
            s += "<tr>\n\t<td>{}</td>\n</tr>".format(inst.get_html(level+1))
        s += "</table>\n\n"
        return s
