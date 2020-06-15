--------------------------------------------------------------------------------
Introduction
--------------------------------------------------------------------------------
This script should be executed before running benchmarks to determine the
current system settings and the execution enviroment.

Most information is gathered from sysfs/procfs files to reduce the dependecies.
Some information is only available through external tools (`likwid-*`, `nvidia-smi`,
`vecmd`, `modulecmd`) and some basic tools (`hostname`, `users`, ...).

[![Build Status](https://travis-ci.org/RRZE-HPC/MachineState.svg?branch=master)](https://travis-ci.org/RRZE-HPC/MachineState) [![Codecov](https://codecov.io/github/RRZE-HPC/MachineState/coverage.svg?branch=master)](https://codecov.io/github/RRZE-HPC/MachineState?branch=mastern)

--------------------------------------------------------------------------------
Installation
--------------------------------------------------------------------------------
MachineState is written as Python3 module but it's not yet in the PIP index.
So, in order to install it, use pip's local feature:

```
$ git clone https://github.com/RRZE-HPC/MachineState
$ cd MachineState
$ pip3 install (--user) .
or
$ ./machinestate.py
```

The module cannot be used with Python2!



--------------------------------------------------------------------------------
Checks
--------------------------------------------------------------------------------
- Hostname, operating system and kernel version
- Users that are logged into the system that might disturb the runs
- CPU information (family, model, vulnerabilities, ...) and cpuset
- CPU, cache and NUMA topology
- CPU/Uncore frequency settings (Uncore only if LIKWID is available)
- Prefetchers and turbo frequencies (if LIKWID is available)
- The current load of the system
- OS settings (NUMA balancing, huge pages, transparent huge pages, ...)
- Power contraints (RAPL limits)
- Module system
- Installed compilers and MPI implementations
- Shell environment
- Accelerator information (Nvidida GPUs and NEC Tsubasa)
- Dmidecode system configuration (if available)
- Information about the executable (if command is passed as cli argument)

**All sizes are converted to bytes, all frequencies are converted to Hz**

--------------------------------------------------------------------------------
Usage (Python version)
--------------------------------------------------------------------------------
Getting usage help:
```
$ ./machinestate.py -h
usage: machinestate.py [-h] [-e] [-a] [-c] [-s] [-i INDENT] [-o OUTPUT]
                       [-j JSON] [--configfile CONFIGFILE] [--html]
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
  --html                Create HTML output out of generated MachineState
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
$ ./machinestate.py
{
    "HostInfo": {
        "Hostname": "testhost"
    },
    [...]
}
```

Gather extended data and print JSON

```
$ ./machinestate.py -e
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
$ ./machinestate.py hostname
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
$ ./machinestate.py -o $(hostname -s).json
```

Sort keys in JSON output
```
$ ./machinestate.py -s
```

Compare JSON file created with `machinestate.py` with current state
```
$ ./machinestate.py -j oldstate.json
```

Create HTML representation with sorted keys
```
$ ./machinestate.py -s --html -o webview.html
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
Differences between Shell and Python version
--------------------------------------------------------------------------------
The Shell version (`shell-version/machine-state.sh`) executes some commands and
just dumps the output to stdout.

The Python version (`machine-state.py`) collects all data and outputs it in JSON
format. This version is currently under development.
