#!/bin/bash -l

### Configurations ####
DO_LIKWID=1
LIKWID_PATH=""
#######################

function header {
    echo
    echo "################################################################################"
    echo "# $1"
    echo "################################################################################"
}

function likwid_command_exists {
    if [[ -z "${LIKWID_PATH//}" ]]; then
        checkCmd=$(command -v $1)
    else
        checkCmd=$(command -v $LIKWID_PATH"/""$1")
    fi
    if [ ${DO_LIKWID} ]; then
        if [[ -z "${checkCmd//}" ]]; then
            echo "false"
        else
            echo "true"
        fi
    else
        echo "false"
    fi
}

function likwid_command {
    if [ ${DO_LIKWID} ]; then
        if [[ -z "${LIKWID_PATH//}" ]]; then
            command $1
        else
            command "$LIKWID_PATH""/""$1"
        fi
    fi
}


function print_powercap_folder {
    FOLDER=$1
    if [ -e $FOLDER/name ]; then
        NAME=$(cat $FOLDER/name)
        echo "RAPL domain ${NAME}"
    else
        return
    fi
    if [ -e $FOLDER/constraint_0_name ]; then
        LIMIT0_NAME=$(cat $FOLDER/constraint_0_name)
        if [ -e $FOLDER/constraint_0_power_limit_uw ]; then
            LIMIT0_LIMIT=$(cat $FOLDER/constraint_0_power_limit_uw)
        else
            LIMIT0_LIMIT="NA"
        fi
        if [ -e $FOLDER/constraint_0_max_power_uw ]; then
            LIMIT0_MAXPOWER=$(cat $FOLDER/constraint_0_max_power_uw)
        else
            LIMIT0_MAXPOWER="NA"
        fi
        if [ -e $FOLDER/constraint_0_time_window_us ]; then
            LIMIT0_TIMEWIN=$(cat $FOLDER/constraint_0_time_window_us)
        else
            LIMIT0_TIMEWIN="NA"
        fi
        echo "- Limit0 ${LIMIT0_NAME} MaxPower ${LIMIT0_MAXPOWER}uW Limit ${LIMIT0_LIMIT}uW TimeWindow ${LIMIT0_TIMEWIN}us"
    fi
    if [ -e $FOLDER/constraint_1_name ]; then
        LIMIT1_NAME=$(cat $FOLDER/constraint_1_name)
        if [ -e $FOLDER/constraint_1_power_limit_uw ]; then
            LIMIT1_LIMIT=$(cat $FOLDER/constraint_1_power_limit_uw)
        else
            LIMIT1_LIMIT="NA"
        fi
        if [ -e $FOLDER/constraint_0_max_power_uw ]; then
            LIMIT1_MAXPOWER=$(cat $FOLDER/constraint_1_max_power_uw)
        else
            LIMIT1_MAXPOWER="NA"
        fi
        if [ -e $FOLDER/constraint_0_time_window_us ]; then
            LIMIT1_TIMEWIN=$(cat $FOLDER/constraint_1_time_window_us)
        else
            LIMIT1_TIMEWIN="NA"
        fi
        echo "- Limit1 ${LIMIT1_NAME} MaxPower ${LIMIT1_MAXPOWER}uW Limit ${LIMIT1_LIMIT}uW TimeWindow ${LIMIT1_TIMEWIN}us"
    fi
}

if [[ -z "${LIKWID_PATH//}" ]]; then
    if [ $(which likwid-topology 2>/dev/null | wc -l) != "1" ]; then
        module load likwid
        if [ $(which likwid-topology 2>/dev/null | wc -l) != "1" ]; then
            DO_LIKWID=0
        fi
    fi
else
        if [ $($LIKWID_PATH/likwid-topology 2>/dev/null | wc -l) != "1" ]; then
            echo "LIKWID not found in path"
            DO_LIKWID=0
        fi
fi

header "Logged in users"
users
w

if [ $(likwid_command_exists likwid-pin) = "true" ]; then
    header "CPUset"
    likwid_command "likwid-pin -p"
fi

header "CGroups"
echo -n "Allowed CPUs: "
cat /sys/fs/cgroup/cpuset/cpuset.effective_cpus
echo -n "Allowed Memory controllers: "
cat /sys/fs/cgroup/cpuset/cpuset.effective_mems

header "Topology"
if [ $(likwid_command_exists likwid-topology) = "true" ]; then
    likwid_command "likwid-topology"
else
    lscpu
fi
numactl -H

header "Frequencies"
if [ $(likwid_command_exists likwid-setFrequencies) = "true" ]; then
    likwid_command "likwid-setFrequencies -p"
else
    echo "likwid-setFrequencies not available"
fi

header "Prefetchers"
if [ $(likwid_command_exists likwid-features) = "true" ]; then
    likwid_command "likwid-features -l -c N"
else
    echo "likwid-features not available"
fi

header "Load"
cat /proc/loadavg

if [ $(likwid_command_exists "likwid-powermeter") ]; then
    header "Performance energy bias"
    likwid_command "likwid-powermeter -i" | grep -i bias
fi

header "NUMA balancing"
echo -n "Enabled: "
cat /proc/sys/kernel/numa_balancing

header "General memory info"
cat /proc/meminfo

header "Transparent huge pages"
echo -n "Enabled: "
cat /sys/kernel/mm/transparent_hugepage/enabled
echo -n "Use zero page: "
cat /sys/kernel/mm/transparent_hugepage/use_zero_page

header "Hardware power limits"
RAPL_FOLDERS=$(find /sys/devices/virtual/powercap -name "intel-rapl\:*")
for F in ${RAPL_FOLDERS}; do print_powercap_folder $F; done


header "Modules"
module list

header "Compiler"
CC=""
if [ $(which icc 2>/dev/null | wc -l ) == 1 ]; then
    CC=$(which icc)
elif [ $(which gcc 2>/dev/null | wc -l ) == 1 ]; then
    CC=$(which gcc)
elif [ $(which clang 2>/dev/null | wc -l ) == 1 ]; then
    CC=$(which clang)
fi
$CC --version

header "MPI"
if [ $(which mpiexec 2>/dev/null | wc -l ) == 1 ]; then
    mpiexec --version
elif [ $(which mpiexec.hydra 2>/dev/null | wc -l ) == 1 ]; then
    mpiexec.hydra --version
elif [ $(which mpirun 2>/dev/null | wc -l ) == 1 ]; then
    mpirun --version
else
    echo "No MPI found"
fi

header "Operating System"
cat /etc/*release*
header "Operating System Kernel"
uname -a
header "Hostname"
hostname -f

if [ $(which nvidia-smi 2>/dev/null | wc -l ) == 1 ]; then
    header "Nvidia GPUs"
    nvidia-smi
fi

if [ $(which veosinfo 2>/dev/null | wc -l ) == 1 ]; then
    header "NEC Tsubasa"
    veosinfo
fi

if [ $# -ge 1 ]; then
    header "Executable"
    echo -n "Name: "
    echo $1
    if [ $($1 --version 2>/dev/null | wc -l) -gt 0 ]; then
        echo -n "Version: "
        $1 --version
    fi
    if [ $(which $1 2>/dev/null | wc -l ) == 1 ]; then
        echo "Libraries:"
        ldd $(which $1)
    fi
fi


