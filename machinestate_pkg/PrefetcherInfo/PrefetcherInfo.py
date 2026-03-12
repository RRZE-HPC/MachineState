from .common import InfoGroup, PathMatchInfoGroup, process_cmd, pexists, pjoin, tobool, which, os

################################################################################
# Infos about CPU prefetchers (LIKWID only)
################################################################################
class PrefetcherInfoClass(InfoGroup):
    '''Class to read prefetcher settings for one HW thread (uses the likwid-features command)'''
    def __init__(self, ident, extended=False, anonymous=False, likwid_base=None):
        super(PrefetcherInfoClass, self).__init__(
            name="Cpu{}".format(ident), extended=extended, anonymous=anonymous)
        self.ident = ident
        self.likwid_base = likwid_base
        names = ["HW_PREFETCHER", "CL_PREFETCHER", "DCU_PREFETCHER", "IP_PREFETCHER"]
        cmd_opts = "-c {} -l".format(ident)
        cmd = "likwid-features"
        abscmd = cmd
        if likwid_base and os.path.isdir(likwid_base):
            abscmd = pjoin(likwid_base, cmd)
        if not pexists(abscmd):
            abscmd = which(cmd)

        if abscmd:
            for name in names:
                self.addc(name, abscmd, cmd_opts, r"{}\s+(\w+)".format(name), tobool)
        self.required(names)

class PrefetcherInfo(PathMatchInfoGroup):
    '''Class to spawn subclasses for all HW threads returned by likwid-features'''
    def __init__(self, extended=False, anonymous=False, likwid_base=None):
        super(PrefetcherInfo, self).__init__(name="PrefetcherInfo",
                                             extended=extended,
                                             anonymous=anonymous)
        self.likwid_base = likwid_base
        cmd = "likwid-features"
        abscmd = cmd
        if likwid_base and os.path.isdir(likwid_base):
            abscmd = pjoin(likwid_base, cmd)
        if not pexists(abscmd):
            abscmd = which(cmd)

        if abscmd:
            for r in [r"Feature\s+HWThread\s(\d+)", r"Feature\s+CPU\s(\d+)"]:
                data = process_cmd((abscmd, "-l -c 0", r, str))
                intdata = -1
                try:
                    intdata = int(data)
                    if intdata == 0:
                        self.searchpath = "/sys/devices/system/cpu/cpu*"
                        self.match = r".*/cpu(\d+)$"
                        self.subclass = PrefetcherInfoClass
                        self.subargs = {"likwid_base" : likwid_base}
                        break
                except:
                    pass
                