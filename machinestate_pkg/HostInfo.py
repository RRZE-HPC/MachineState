from .common import InfoGroup

################################################################################
# Infos about the host
################################################################################
class HostInfo(InfoGroup):
    def __init__(self, extended=False, anonymous=False):
        super(HostInfo, self).__init__(anonymous=anonymous, extended=extended)
        self.name = "HostInfo"
        if not anonymous:
            self.addc("Hostname", "hostname", "-s", r"(.+)")
            if extended:
                self.addc("Domainname", "hostname", "-d", r"(.+)")
                self.addc("FQDN", "hostname", "-f", r"(.+)")