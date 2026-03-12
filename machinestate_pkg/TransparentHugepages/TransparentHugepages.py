from .common import pjoin, tobool
from .common import InfoGroup

################################################################################
# Infos about transparent hugepages
################################################################################
class TransparentHugepagesDaemon(InfoGroup):
    def __init__(self, extended=False, anonymous=False):
        super(TransparentHugepagesDaemon, self).__init__(name="TransparentHugepagesDaemon",
                                                         extended=extended,
                                                         anonymous=anonymous)
        base = "/sys/kernel/mm/transparent_hugepage/khugepaged"
        self.addf("Defrag", pjoin(base, "defrag"), r"(\d+)", int)
        self.addf("PagesToScan", pjoin(base, "pages_to_scan"), r"(\d+)", int)
        self.addf("ScanSleepMillisecs", pjoin(base, "scan_sleep_millisecs"), r"(\d+)", int)
        self.addf("AllocSleepMillisecs", pjoin(base, "alloc_sleep_millisecs"), r"(\d+)", int)
        self.required(["Defrag", "PagesToScan", "ScanSleepMillisecs", "AllocSleepMillisecs"])

class TransparentHugepages(InfoGroup):
    def __init__(self, extended=False, anonymous=False):
        super(TransparentHugepages, self).__init__(name="TransparentHugepages",
                                                   extended=extended,
                                                   anonymous=anonymous)
        base = "/sys/kernel/mm/transparent_hugepage"
        self.addf("State", pjoin(base, "enabled"), r".*\[(.*)\].*")
        self.addf("Defrag", pjoin(base, "defrag"), r".*\[(.*)\].*")
        self.addf("ShmemEnabled", pjoin(base, "shmem_enabled"), r".*\[(.*)\].*")
        self.addf("UseZeroPage", pjoin(base, "use_zero_page"), r"(\d+)", tobool)
        self.required(["State", "UseZeroPage", "Defrag", "ShmemEnabled"])
        self._instances = [TransparentHugepagesDaemon(extended, anonymous)]
