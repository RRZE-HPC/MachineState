from .common import pjoin, tobool
from .common import InfoGroup

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