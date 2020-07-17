
<div align=center><img src="https://github.com/RRZE-HPC/MachineState/raw/master/logo/machinestate_logo.png" alt="MachineState logo" width="150px"/></div>

--------------------------------------------------------------------------------
Introduction
--------------------------------------------------------------------------------
This script should be executed before running benchmarks to determine the
current system settings and the execution enviroment.

On Linux, most information is gathered from sysfs/procfs files to reduce the dependecies.
Some information is only available through external tools (`likwid-*`, `nvidia-smi`,
`vecmd`, `modulecmd`) and some basic tools (`hostname`, `users`, ...).
On MacOS, most information is gathered through the `sysctl` command.

An example JSON (in extended mode) from an Intel Skylake Desktop system running Linux can be found [here](./examples/skylake-desktop.json) ([raw](https://raw.githubusercontent.com/RRZE-HPC/MachineState/master/examples/skylake-desktop.json)).

An example JSON (in extended mode) from an Intel Skylake Desktop system running macOS can be found [here](./examples/skylake-desktop-macos.json) ([raw](https://raw.githubusercontent.com/RRZE-HPC/MachineState/master/examples/skylake-desktop-macos.json)). 

[![Build Status](https://travis-ci.org/RRZE-HPC/MachineState.svg?branch=master)](https://travis-ci.org/RRZE-HPC/MachineState) [![Codecov](https://codecov.io/github/RRZE-HPC/MachineState/coverage.svg?branch=master)](https://codecov.io/github/RRZE-HPC/MachineState?branch=mastern)

--------------------------------------------------------------------------------
Installation
--------------------------------------------------------------------------------
MachineState is written as Python3 module:

```
$ git clone https://github.com/RRZE-HPC/MachineState
$ cd MachineState
$ ./machinestate.py
```
or
```
$ pip3 install MachineState
$ machinestate
or
$ python3
>>> import machinestate
```

The module cannot be used with Python2!

The module is tested on Ubuntu Xenial for Python versions 3.4, 3.5, 3.6, 3.7 and 3.8 for the architectures AMD64, PPC64le and ARM8. For macOS, only Python versions 3.7 and 3.8 for the AMD64 architecture are tested.



--------------------------------------------------------------------------------
Checks
--------------------------------------------------------------------------------
General:
- Hostname
- The current load of the system
- Number of users that are logged into the system that might disturb the runs
- Shell environment
- Module system
- Installed compilers and MPI implementations
- Information about the executable (if command is passed as cli argument)

Linux:
- Operating system and kernel version
- CPU information (family, model, vulnerabilities, ...) and cpuset
- CPU, cache and NUMA topology
- CPU frequency settings
- Memory information
- Uncore frequency settings (Uncore only if LIKWID is available)
- Prefetchers and turbo frequencies (if LIKWID is available)
- OS settings (NUMA balancing, huge pages, transparent huge pages, ...)
- Power contraints (RAPL limits)
- Accelerator information (Nvidida GPUs and NEC Tsubasa)
- Dmidecode system configuration (if available)

macOS:
- Operating system version
- CPU information (family, model, ...)
- CPU, cache and NUMA topology
- CPU frequency settings
- Memory information

**All sizes are converted to bytes, all frequencies are converted to Hz**

--------------------------------------------------------------------------------
Usage (CLI)
--------------------------------------------------------------------------------
Getting usage help:
```
$ machinestate -h
usage: machinestate.py [-h] [-e] [-a] [-c] [-s] [-i INDENT] [-o OUTPUT]
                       [-j JSON] [--configfile CONFIGFILE]
                       [executable]


Reads and outputs system information as JSON document

positional arguments:
  executable            analyze executable (optional)

optional arguments:
  -h, --help            show this help message and exit
  -e, --extended        extended output (default: False)
  -a, --anonymous       Remove host-specific information (default: False)
  -c, --config          print configuration as JSON (files, commands, ...)
  -s, --sort            sort JSON output (default: False)
  -i INDENT, --indent INDENT
                        indention in JSON output (default: 4)
  -o OUTPUT, --output OUTPUT
                        save JSON to file (default: stdout)
  -j JSON, --json JSON  compare given JSON with current state
  --configfile CONFIGFILE
                        Location of configuration file
```

If the `configfile` cli option is not given, machinestate checks for configuration files at (in this order):
- `$PWD/.machinestate`
- `$HOME/.machinestate`
- `/etc/machinestate.conf`


--------------------------------------------------------------------------------
Examples
--------------------------------------------------------------------------------
Gather data and print JSON

```
$ machinestate
{
    "HostInfo": {
        "Hostname": "testhost"
    },
    [...]
}
```

Gather extended data and print JSON

```
$ machinestate -e
{
    "HostInfo": {
        "Hostname": "testhost"
        "Domainname": "testdomain.de",
        "FQDN": "testhost.testdomain.de"
    },
    [...]
}
```

Gather data, include information about the executable on cmdline and print JSON

```
$ machinestate hostname
{
    "HostInfo": {
        "Hostname": "testhost"
    },
    [...]
    "ExecutableInfo": {
        "ExecutableInfo": {
            "Name": "hostname",
            "Abspath": "/bin/hostname",
            "Size": 18504
        },
        "LinkedLibraries": {
            "linux-vdso.so.1": null,
            "libc.so.6": "/lib/x86_64-linux-gnu/libc.so.6",
            "/lib64/ld-linux-x86-64.so.2": "/lib64/ld-linux-x86-64.so.2"
        }
    }
}
```

Redirecting JSON output to file

```
$ machinestate -o $(hostname -s).json
```

Sort keys in JSON output
```
$ machinestate -s
```

Compare JSON file created with `machinestate.py` with current state
```
$ machinestate -j oldstate.json
```

--------------------------------------------------------------------------------
Configuration file
--------------------------------------------------------------------------------
The configuration file is in JSON format and should look like this:

```
{
  "dmifile" : "/path/to/file/containing/the/output/of/dmidecode",
  "likwid_enable" : <true|false>,
  "likwid_path" : "/path/to/LIKWID/installation/bin/directory",
  "modulecmd" : "/path/to/modulecmd",
  "vecmd_path" : "/path/to/vecmd/command",
  "debug" : <true|false>,
}
```

Valid locations are:

- `$PWD/.machinestate`
- `$HOME/.machinestate`
- `/etc/machinestate.conf`

Or the user can specify a custom path with the `--configfile CONFIGFILE` option.

For the ModulesInfo class with its `modulecmd` setting, also the TCL version can be used
with `tclsh /path/to/modulecmd.tcl`.

--------------------------------------------------------------------------------
Usage as Python3 module
--------------------------------------------------------------------------------
You can use MachineState also as module in your applications. You don't need to gather all
information if you are interested in only specific information classes.

In order to capture the current state:
```
$ python3
>>> import machinestate
>>> ms = machinestate.MachineState(extended=False, anonymous=False)
>>> ms.generate()                        # generate subclasses
>>> ms.update()                          # read information
>>> ms.get()                             # get the information as dict
{ ... all fields ... }
>>> ms.get_json(indent=4, sort=True)     # get the information as JSON document (parameters optional)
"... JSON document ..."
```


How to get the list of information classes:
```
$ python3
>>> import machinestate
>>> help(machinestate)
[...]
Provided classes:
    - HostInfo
    - CpuInfo
    - OSInfo
    [...]
```

Using single information classes is similar to the big `MachineState` class
```
$ python3
>>> import machinestate
>>> hi = machinestate.HostInfo(extended=False, anonymous=False)
>>> hi.generate()
>>> hi.update()
>>> hi_dict = hi.get()
{'Hostname': 'testhost'}
>>> hi_json = hi.get_json()
'{\n    "Hostname": "testhost"\n}'
```

If you want to compare with an old state:
```
$ python3
>>> oldstate = {}            # dictionary of oldstate or
                             # filename "oldstate.json" or
                             # JSON document "... OldState JSON document ..."
>>> ms = machinestate.MachineState(extended=False, anonymous=False)
>>> ms.generate()
>>> ms.update()
>>> ms == oldstate
False
```

--------------------------------------------------------------------------------
Differences between Shell and Python version
--------------------------------------------------------------------------------
The Shell version (`shell-version/machine-state.sh`) executes some commands and
just dumps the output to stdout.

The Python version (`machine-state.py`) collects all data and outputs it in JSON
format. This version is currently under development.
