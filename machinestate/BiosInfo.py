from .common import InfoGroup, pexists, pjoin

################################################################################
# Infos about the BIOS
################################################################################
class BiosInfo(InfoGroup):
    '''Class to read BIOS information (/sys/devices/virtual/dmi/id)'''
    def __init__(self, extended=False, anonymous=False):
        super(BiosInfo, self).__init__(name="BiosInfo",
                                       extended=extended,
                                       anonymous=anonymous)
        base = "/sys/devices/virtual/dmi/id"
        if pexists(base):
            self.addf("BiosDate", pjoin(base, "bios_date"))
            self.addf("BiosVendor", pjoin(base, "bios_vendor"))
            self.addf("BiosVersion", pjoin(base, "bios_version"))
            self.addf("SystemVendor", pjoin(base, "sys_vendor"))
            self.addf("ProductName", pjoin(base, "product_name"))
            if pexists(pjoin(base, "product_vendor")):
                self.addf("ProductVendor", pjoin(base, "product_vendor"))
            self.required(list(self.files.keys()))