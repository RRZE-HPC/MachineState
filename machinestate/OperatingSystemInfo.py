from .common import get_ostype
from .common import InfoGroup

################################################################################
# Infos about operating system
################################################################################
class OSInfoMacOS(InfoGroup):
    def __init__(self, extended=False, anonymous=False):
        super(OSInfoMacOS, self).__init__(anonymous=anonymous, extended=extended)
        self.name = "OperatingSystemInfo"
        ostype = get_ostype()
        self.const("Type", ostype)
        self.required("Type")
        self.addc("Version", "sysctl", "-n kern.osproductversion", r"([\d\.]+)")
        self.required("Version")

class OperatingSystemInfo(InfoGroup):
    def __init__(self, extended=False, anonymous=False):
        super(OperatingSystemInfo, self).__init__(anonymous=anonymous, extended=extended)
        self.name = "OperatingSystemInfo"
        ostype = get_ostype()
        self.const("Type", ostype)
        self.required("Type")
        self.addf("Name", "/etc/os-release", r"NAME=[\"]*([^\"]+)[\"]*\s*")
        self.addf("Version", "/etc/os-release", r"VERSION=[\"]*([^\"]+)[\"]*\s*")

        self.required(["Name", "Version"])
        if extended:
            self.addf("URL", "/etc/os-release", r"HOME_URL=[\"]*([^\"]+)[\"]*\s*")