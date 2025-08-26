from .common import InfoGroup, process_cmd, tobytes

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