from .common import InfoGroup

################################################################################
# Infos about the load of the system
################################################################################
class LoadAvgMacOs(InfoGroup):
    def __init__(self, extended=False, anonymous=False):
        super(LoadAvgMacOs, self).__init__(name="LoadAvg", extended=extended, anonymous=anonymous)
        self.addc("LoadAvg1m", "uptime", None, r".*load averages:\s+([\d\.]+)", float)
        self.addc("LoadAvg5m", "uptime", None, r".*load averages:\s+[\d\.]+\s+([\d+\.]+)", float)
        self.addc("LoadAvg15m", "uptime", None, r".*load averages:\s+[\d\.]+\s+[\d+\.]+\s+([\d+\.]+)", float)


class LoadAvg(InfoGroup):
    def __init__(self, extended=False, anonymous=False):
        super(LoadAvg, self).__init__(name="LoadAvg", extended=extended, anonymous=anonymous)
        self.addf("LoadAvg1m", "/proc/loadavg", r"([\d\.]+)", float)
        self.addf("LoadAvg5m", "/proc/loadavg", r"[\d\.]+\s+([\d+\.]+)", float)
        self.addf("LoadAvg15m", "/proc/loadavg", r"[\d\.]+\s+[\d+\.]+\s+([\d+\.]+)", float)
        #self.required(["LoadAvg15m"])
        if extended:
            rpmatch = r"[\d+\.]+\s+[\d+\.]+\s+[\d+\.]+\s+(\d+)"
            self.addf("RunningProcesses", "/proc/loadavg", rpmatch, int)
            apmatch = r"[\d+\.]+\s+[\d+\.]+\s+[\d+\.]+\s+\d+/(\d+)"
            self.addf("AllProcesses", "/proc/loadavg", apmatch, int)
