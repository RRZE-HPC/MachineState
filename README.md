
<div align=center><img src="https://github.com/RRZE-HPC/MachineState/raw/master/logo/machinestate_logo.png" alt="MachineState logo" width="150px"/></div>

--------------------------------------------------------------------------------
Introduction
--------------------------------------------------------------------------------
This script should be executed before running benchmarks to determine the
current system settings and the execution environment.

On Linux, most information is gathered from sysfs/procfs files to reduce the dependencies.
Some information is only available through external tools (`likwid-*`, `nvidia-smi`,
`vecmd`, `modulecmd`) and some basic tools (`hostname`, `users`, ...).
On MacOS, most information is gathered through the `sysctl` command.

An example JSON (in extended mode) from an Intel Skylake Desktop system running Linux can be found [here](./examples/skylake-desktop.json) ([raw](https://raw.githubusercontent.com/RRZE-HPC/MachineState/master/examples/skylake-desktop.json)).

An example JSON (in extended mode) from an Intel Skylake Desktop system running macOS can be found [here](./examples/skylake-desktop-macos.json) ([raw](https://raw.githubusercontent.com/RRZE-HPC/MachineState/master/examples/skylake-desktop-macos.json)). 

[![GitHub Action](https://github.com/RRZE-HPC/MachineState/actions/workflows/test-n-publish.yml/badge.svg)](https://github.com/RRZE-HPC/MachineState/actions/workflows/test-n-publish.yml) [![Codecov](https://codecov.io/github/RRZE-HPC/MachineState/coverage.svg?branch=master)](https://codecov.io/github/RRZE-HPC/MachineState?branch=mastern) [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.4599778.svg)](https://doi.org/10.5281/zenodo.4599778)



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
or just for the current project
```
$ wget https://raw.githubusercontent.com/RRZE-HPC/MachineState/master/machinestate.py
$ ./machinestate.py
```

The module cannot be used with Python2!

The module is tested on the latest Ubuntu distro for all Python versions with security support for the architectures AMD64, PPC64le and ARM8.
For macOS, all Python versions with security support for the ARM8 architecture are tested.



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
usage: machinestate.py [-h] [-e] [-a] [-c] [-s] [-i INDENT] [-o OUTPUT]
                       [-j JSON] [--html] [--configfile CONFIGFILE]
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
                        save to file (default: stdout)
  -j JSON, --json JSON  compare given JSON with current state
  -m, --no-meta         embed meta information in classes (recommended, default: True)
  --html                generate HTML page with CSS and JavaScript embedded
                        instead of JSON
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

Output the MachineState data as collapsible HTML table (with CSS and JavaScript):
```
$ machinestate --html
```

You can also redirect the HTML output to a file directly:
```
$ machinestate --html --output machine.html
```
You can embedd the file in your HTML page within an `<iframe>`ö.

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
True
```
In case of 'False', it reports the value differences and missing keys. For integer and float values, it compares the values with a tolerance of 20%. Be aware that if you use `oldstate.get() == ms.get()`, it uses the default `dict` comparison which does not print anything and matches exact.


If you want to load an old state and use the class tree
```
$ python3
>>> oldstate = {}           # dictionary of oldstate or
                            # path to JSON file of oldstate or
                            # JSON document (as string)
                            # or a MachineState class
                            # It has to contain the '_meta' entries
                            # you get when calling get_json() or
                            # get(meta=True)
>>> ms = machinestate.MachineState.from_dict(oldstate)
>>> ms == oldstate
True
```

--------------------------------------------------------------------------------
Differences between Shell and Python version
--------------------------------------------------------------------------------
The Shell version (`shell-version/machine-state.sh`) executes some commands and
just dumps the output to stdout.

The Python version (`machinestate.py`) collects all data and outputs it in JSON
format. This version is currently under development.


--------------------------------------------------------------------------------
Additional information by others
--------------------------------------------------------------------------------
- [The Tuned Project](https://tuned-project.org/)
- [Intel® 64 and IA-32 Architectures Software Developer Manuals](https://software.intel.com/content/www/us/en/develop/articles/intel-sdm.html)
- [Intel® 64 and IA-32 Architectures Optimization Reference Manual](https://software.intel.com/content/www/us/en/develop/download/intel-64-and-ia-32-architectures-optimization-reference-manual.html)
- [AMD Tech Docs](https://developer.amd.com/resources/developer-guides-manuals/)
- [ARM documetatation center](https://developer.arm.com/documentation/)
- [Performance Optimization and Tuning Techniques for IBM Power Systems Processors Including IBM POWER8](http://www.redbooks.ibm.com/abstracts/sg248171.html)
- [System Tuning Info for Linux Servers by Adrian Likins](http://people.redhat.com/alikins/system_tuning.html)
- [Low latency tuning guide by Erik Rigtorp](https://rigtorp.se/low-latency-guide/)
- https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux_for_real_time/7/html/tuning_guide/real_time_throttling
- [What are Interrupt Threads and How do They Work? by Mike Anderson](https://elinux.org/images/e/ef/InterruptThreads-Slides_Anderson.pdf)
- [perf Examples by Brendan Gregg](http://brendangregg.com/perf.html)
- [Tuning your Linux system for Gaming Performance by user u/sn0w75 on Reddit](https://www.reddit.com/r/linux_gaming/comments/8j0evj/tuning_your_linux_system_for_gaming_performance/)
