from .common import tostrlist, platform, pexists, int_from_str, tobool
from .common import InfoGroup

################################################################################
# Infos about the CPU
################################################################################

class CpuInfoMacOS(InfoGroup):
    def __init__(self, extended=False, anonymous=False):
        super(CpuInfoMacOS, self).__init__(name="CpuInfo", extended=extended, anonymous=anonymous)
        march = platform.machine()
        self.const("MachineType", march)
        if march in ["x86_64"]:
            self.addc("Vendor", "sysctl", "-a", r"machdep.cpu.vendor: (.*)")
            self.addc("Name", "sysctl", "-a", r"machdep.cpu.brand_string: (.*)")
            self.addc("Family", "sysctl", "-a", r"machdep.cpu.family: (\d+)", int)
            self.addc("Model", "sysctl", "-a", r"machdep.cpu.model: (\d+)", int)
            self.addc("Stepping", "sysctl", "-a", r"machdep.cpu.stepping: (\d+)", int)
            if extended:
                self.addc("Flags", "sysctl", "-a", r"machdep.cpu.features: (.*)", tostrlist)
                self.addc("ExtFlags", "sysctl", "-a", r"machdep.cpu.extfeatures: (.*)", tostrlist)
                self.addc("Leaf7Flags", "sysctl", "-a", r"machdep.cpu.leaf7_features: (.*)", tostrlist)
                self.addc("Microcode", "sysctl", "-a", r"machdep.cpu.microcode_version: (.*)")
                self.addc("ExtFamily", "sysctl", "-a", r"machdep.cpu.extfamily: (\d+)", int)
                self.addc("ExtModel", "sysctl", "-a", r"machdep.cpu.extmodel: (\d+)", int)
            self.required(["Vendor", "Family", "Model", "Stepping"])
        elif march in ["arm64"]:
            # TODO: Is there a way to get Vendor?
            self.const("Vendor", "Apple")
            self.addc("Name", "sysctl", "-a", r"machdep.cpu.brand_string: (.*)")
            self.addc("Family", "sysctl", "-a", r"hw.cpufamily: (\d+)", int)
            self.addc("Model", "sysctl", "-a", r"hw.cputype: (\d+)", int)
            self.addc("Stepping", "sysctl", "-a", r"hw.cpusubtype: (\d+)", int)
            if extended:
                self.addc("Flags", "sysctl", "-a hw.optional", parse=CpuInfoMacOS.getflags_arm64)
            self.required(["Vendor", "Family", "Model", "Stepping"])

    @staticmethod
    def getflags_arm64(string):
        outlist = []
        for line in string.split("\n"):
            key, value = [
                    field.split(":") for field in line.split("hw.optional.") if len(field)
                ][0]
            if int(value):
                key = key.replace("arm.", "")
                outlist.append(key)
        return outlist


class CpuInfo(InfoGroup):
    def __init__(self, extended=False, anonymous=False):
        super(CpuInfo, self).__init__(name="CpuInfo", extended=extended, anonymous=anonymous)
        march = platform.machine()
        self.const("MachineType", march)

        if march in ["x86_64", "i386"]:
            self.addf("Vendor", "/proc/cpuinfo", r"vendor_id\s+:\s(.*)")
            self.addf("Name", "/proc/cpuinfo", r"model name\s+:\s(.+)")
            self.addf("Family", "/proc/cpuinfo", r"cpu family\s+:\s(.+)", int)
            self.addf("Model", "/proc/cpuinfo", r"model\s+:\s(.+)", int)
            self.addf("Stepping", "/proc/cpuinfo", r"stepping\s+:\s(.+)", int)
        elif march in ["aarch64"]:
            self.addf("Vendor", "/proc/cpuinfo", r"CPU implementer\s+:\s([x0-9a-fA-F]+)")
            self.addf("Family", "/proc/cpuinfo", r"CPU architecture\s*:\s([x0-9a-fA-F]+)",
                      int_from_str)
            self.addf("Model", "/proc/cpuinfo", r"CPU variant\s+:\s([x0-9a-fA-F]+)",
                      int_from_str)
            self.addf("Stepping", "/proc/cpuinfo", r"CPU revision\s+:\s([x0-9a-fA-F]+)",
                      int_from_str)
            self.addf("Variant", "/proc/cpuinfo", r"CPU part\s+:\s([x0-9a-fA-F]+)",
                      int_from_str)
        elif march in ["ppc64le", "ppc64"]:
            self.addf("Platform", "/proc/cpuinfo", r"platform\s+:\s(.*)")
            self.addf("Name", "/proc/cpuinfo", r"model\s+:\s(.+)")
            self.addf("Family", "/proc/cpuinfo", r"cpu\s+:\s(POWER\d+).*")
            self.addf("Model", "/proc/cpuinfo", r"model\s+:\s(.+)")
            self.addf("Stepping", "/proc/cpuinfo", r"revision\s+:\s(.+)")


        if pexists("/sys/devices/system/cpu/smt/active"):
            self.addf("SMT", "/sys/devices/system/cpu/smt/active", r"(\d+)", tobool)
            self.required("SMT")
        if extended:
            if march in ["x86_64", "i386"]:
                self.addf("Flags", "/proc/cpuinfo", r"flags\s+:\s(.+)", tostrlist)
                self.addf("Microcode", "/proc/cpuinfo", r"microcode\s+:\s(.+)")
                self.addf("Bugs", "/proc/cpuinfo", r"bugs\s+:\s(.+)", tostrlist)
                self.required("Microcode")
            elif march in ["aarch64"]:
                self.addf("Flags", "/proc/cpuinfo", r"Features\s+:\s(.+)", tostrlist)

        self.required(["Vendor", "Family", "Model", "Stepping"])