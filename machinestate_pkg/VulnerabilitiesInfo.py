from .common import InfoGroup, pjoin, totitle, glob, os

################################################################################
# Infos about CPU vulnerabilities
################################################################################
class VulnerabilitiesInfo(InfoGroup):
    '''Class to read vulnerabilities information (/sys/devices/system/cpu/vulnerabilities)'''
    def __init__(self, extended=False, anonymous=False):
        super(VulnerabilitiesInfo, self).__init__(extended=extended, anonymous=anonymous)
        self.name = "VulnerabilitiesInfo"
        base = "/sys/devices/system/cpu/vulnerabilities"
        for vfile in glob(pjoin(base, "*")):
            vkey = totitle(os.path.basename(vfile))
            self.addf(vkey, vfile)
            self.required(vkey)