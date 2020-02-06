--------------------------------------------------------------------------------
Introduction
--------------------------------------------------------------------------------
This script should be executed before running benchmarks to determine the
current system settings and the execution enviroment.

--------------------------------------------------------------------------------
Checks
--------------------------------------------------------------------------------
- Hostname, operating system and kernel version
- Users that are logged into the system that might disturb the runs
- CPUset
- CPU and NUMA topology
- CPU/Uncore frequency settings
- Prefetchers
- The current load of the system
- OS settings (NUMA balancing, huge pages, ...)
- Power contraints (RAPL limits)
- Module system
- Installed compilers and MPI implementations
- Accelerator information (Nvidida GPUs and NEC Tsubasa)
- Runtime enviroment
- Dmidecode system configuration (if available)
- Information about the benchmark (if cmd given as first argument)

