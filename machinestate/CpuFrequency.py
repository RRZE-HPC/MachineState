from .common import pjoin, re, tohertzlist, tohertz, pexists, tostrlist, struct
from .common import platform
from .common import InfoGroup, MultiClassInfoGroup, PathMatchInfoGroup

################################################################################
# CPU Frequency
################################################################################
class CpuFrequencyMacOsCpu(InfoGroup):
    def __init__(self, extended=False, anonymous=False):
        super(CpuFrequencyMacOsCpu, self).__init__(extended=extended, anonymous=anonymous)
        self.name = "Cpus"
        if platform.machine() == "x86_64":
            self.addc("MaxFreq", "sysctl", "-a", r"hw.cpufrequency_max: (\d+)", int)
            self.addc("MinFreq", "sysctl", "-a", r"hw.cpufrequency_min: (\d+)", int)
        elif platform.machine() == "arm64":
            # AppleSilicon
            self.addc("Freqs-E-Core", "ioreg", "-k voltage-states1-sram | grep voltage-states1-sram", parse=CpuFrequencyMacOsCpu.get_ioreg_states)
            self.addc("Freqs-P-Core", "ioreg", "-k voltage-states5-sram | grep voltage-states5-sram", parse=CpuFrequencyMacOsCpu.get_ioreg_states)

    @staticmethod
    def get_ioreg_states(string):
        bytestr = re.match(r".*<([0-9A-Fa-f]+)>", string)
        if bytestr:
            bytestr = bytestr.group(1)
            # numbers consecutive in 4-byte little-endian
            states_int = struct.unpack("<" + int(len(bytestr)/8) * "I", bytes.fromhex(bytestr))
            # voltage states are in pairs of (freq, voltage)
            states_int = [x for x in states_int if states_int.index(x)%2 == 0]
            return states_int
        return string

class CpuFrequencyMacOsBus(InfoGroup):
    def __init__(self, extended=False, anonymous=False):
        super(CpuFrequencyMacOsBus, self).__init__(extended=extended, anonymous=anonymous)
        self.name = "Bus"
        self.addc("MaxFreq", "sysctl", "-a", r"hw.busfrequency_max: (\d+)", int)
        self.addc("MinFreq", "sysctl", "-a", r"hw.busfrequency_min: (\d+)", int)

class CpuFrequencyMacOs(MultiClassInfoGroup):
    def __init__(self, extended=False, anonymous=False):
        super(CpuFrequencyMacOs, self).__init__(extended=extended, anonymous=anonymous)
        self.name = "CpuFrequency"
        # Apple Silicon with MacOS does not easily print out CPU/BUS freqs, see
        # https://github.com/giampaolo/psutil/issues/1892
        if platform.machine() == "x86_64":
            self.classlist = [CpuFrequencyMacOsCpu, CpuFrequencyMacOsBus]
        elif platform.machine() == "arm64":
            self.classlist = [CpuFrequencyMacOsCpu]
        self.classargs = [{} for c in self.classlist]
        self.addc("TimerFreq", "sysctl", "-a", r"hw.tbfrequency: (\d+)", int)

class CpuFrequencyClass(InfoGroup):
    def __init__(self, ident, extended=False, anonymous=False):
        super(CpuFrequencyClass, self).__init__(
            name="Cpu{}".format(ident), anonymous=anonymous, extended=extended)
        self.ident = ident
        base = "/sys/devices/system/cpu/cpu{}/cpufreq".format(ident)
        if pexists(pjoin(base, "scaling_max_freq")):
            self.addf("MaxFreq", pjoin(base, "scaling_max_freq"), r"(\d+)", tohertz)
        if pexists(pjoin(base, "scaling_max_freq")):
            self.addf("MinFreq", pjoin(base, "scaling_min_freq"), r"(\d+)", tohertz)
        if pexists(pjoin(base, "scaling_governor")):
            self.addf("Governor", pjoin(base, "scaling_governor"), r"(.+)")
        if pexists(pjoin(base, "energy_performance_preference")):
            fname = pjoin(base, "energy_performance_preference")
            self.addf("EnergyPerfPreference", fname, r"(.+)")
        self.required(list(self.files.keys()))

class CpuFrequency(PathMatchInfoGroup):
    def __init__(self, extended=False, anonymous=False):
        super(CpuFrequency, self).__init__(extended=extended, anonymous=anonymous)
        self.name = "CpuFrequency"
        base = "/sys/devices/system/cpu/cpu0/cpufreq"
        if pexists(base):
            self.searchpath = "/sys/devices/system/cpu/cpu*"
            self.match = r".*/cpu(\d+)$"
            self.subclass = CpuFrequencyClass
            if pexists(pjoin(base, "scaling_driver")):
                self.addf("Driver", pjoin(base, "scaling_driver"), r"(.*)")
                self.required("Driver")
            if extended:
                if pexists(pjoin(base, "cpuinfo_transition_latency")):
                    fname = pjoin(base, "cpuinfo_transition_latency")
                    self.addf("TransitionLatency", fname, r"(\d+)", int)
                if pexists(pjoin(base, "cpuinfo_max_freq")):
                    self.addf("MaxAvailFreq", pjoin(base, "cpuinfo_max_freq"), r"(\d+)", tohertz)
                if pexists(pjoin(base, "cpuinfo_min_freq")):
                    self.addf("MinAvailFreq", pjoin(base, "cpuinfo_min_freq"), r"(\d+)", tohertz)
                if pexists(pjoin(base, "scaling_available_frequencies")):
                    fname = pjoin(base, "scaling_available_frequencies")
                    self.addf("AvailFrequencies", fname, r"(.*)", tohertzlist)
                if pexists(pjoin(base, "scaling_available_governors")):
                    fname = pjoin(base, "scaling_available_governors")
                    self.addf("AvailGovernors", fname, r"(.*)", tostrlist)
                if pexists(pjoin(base, "energy_performance_available_preferences")):
                    fname = pjoin(base, "energy_performance_available_preferences")
                    self.addf("AvailEnergyPerfPreferences", fname, r"(.*)", tostrlist)