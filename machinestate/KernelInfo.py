from .common import InfoGroup, ListInfoGroup, pjoin, tobool, tointlist, pexists

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
        self.command = command
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
        self.addf("Swappiness", "/proc/sys/vm/swappiness", parse=int)
        self.addf("MinFreeBytes", "/proc/sys/vm/min_free_kbytes", parse=lambda x: int(x)*1024)
        self.addf("WatermarkScaleFactor", "/proc/sys/vm/watermark_scale_factor", parse=int)
        self.addf("VFSCachePressure", "/proc/sys/vm/vfs_cache_pressure", parse=int)
        self.required("Version", "CmdLine", "NMIWatchdog", "Watchdog")

        cls = KernelSchedInfo(extended=extended,
                              anonymous=anonymous)
        self._instances.append(cls)
        self.userlist = ["rcu_sched", "rcu_bh", "rcu_tasks_kthre"]
        self.subclass = KernelRcuInfo