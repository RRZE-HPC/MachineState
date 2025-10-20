from .common import InfoGroup, PathMatchInfoGroup, totitle, tobool, fopen, pjoin, pexists
from .common import ENCODING, platform, glob


################################################################################
# Infos about powercapping
#################################################################################
class PowercapInfoConstraintClass(InfoGroup):
    '''Class to read information about one powercap constraint'''
    def __init__(self, ident, extended=False, anonymous=False, package=0, domain=-1):
        super(PowercapInfoConstraintClass, self).__init__(name="Constraint{}".format(ident),
                                                          extended=extended,
                                                          anonymous=anonymous)
        self.ident = ident
        self.package = package
        self.domain = domain
        base = "/sys/devices/virtual/powercap/intel-rapl/intel-rapl:{}".format(package)
        fptr = fopen(pjoin(base, "constraint_{}_name".format(ident)))
        if fptr:
            self.name = totitle(fptr.read().decode(ENCODING).strip())
            fptr.close()
        if domain >= 0:
            base = pjoin(base, "intel-rapl:{}:{}".format(package, domain))
        names = ["PowerLimitUw",
                 "TimeWindowUs"]
        files = ["constraint_{}_power_limit_uw".format(ident),
                 "constraint_{}_time_window_us".format(ident)]
        for key, fname in zip(names, files):
            self.addf(key, pjoin(base, fname), r"(.+)", int)
        self.required(names)

class PowercapInfoClass(PathMatchInfoGroup):
    '''Class to spawn subclasses for each contraint in a powercap domain'''
    def __init__(self, ident, extended=False, anonymous=False, package=0):
        super(PowercapInfoClass, self).__init__(extended=extended, anonymous=anonymous)
        self.ident = ident
        self.package = package
        base = "/sys/devices/virtual/powercap/intel-rapl"
        base = pjoin(base, "intel-rapl:{}/intel-rapl:{}:{}".format(package, package, ident))
        fptr = fopen(pjoin(base, "name".format(ident)))
        if fptr:
            self.name = totitle(fptr.read().decode(ENCODING).strip())
            fptr.close()
        self.addf("Enabled", pjoin(base, "enabled"), r"(\d+)", tobool)
        self.searchpath = pjoin(base, "constraint_*_name")
        self.match = r".*/constraint_(\d+)_name"
        self.subclass = PowercapInfoConstraintClass
        self.subargs = {"package" : package, "domain" : ident}

class PowercapInfoPackageClass(PathMatchInfoGroup):
    '''Class to spawn subclasses for powercap package domain
    (/sys/devices/virtual/powercap/intel-rapl/intel-rapl:*)
    '''
    def __init__(self, ident, extended=False, anonymous=False):
        base = "/sys/devices/virtual/powercap/intel-rapl/intel-rapl:{}".format(ident)
        super(PowercapInfoPackageClass, self).__init__(name="Package",
                                                       extended=extended,
                                                       anonymous=anonymous,
                                                       searchpath=pjoin(base, "constraint_*_name"),
                                                       match=r".*/constraint_(\d+)_name",
                                                       subclass=PowercapInfoConstraintClass,
                                                       subargs={"package" : ident})
        self.ident = ident
        self.addf("Enabled", pjoin(base, "enabled"), r"(\d+)", tobool)

class PowercapInfoPackage(PathMatchInfoGroup):
    '''Class to spawn subclasses for one powercap device/package
    (/sys/devices/virtual/powercap/intel-rapl/intel-rapl:<package>*:*)
    '''
    def __init__(self, package, extended=False, anonymous=False):
        base = "/sys/devices/virtual/powercap/intel-rapl/intel-rapl:{}".format(package)
        super(PowercapInfoPackage, self).__init__(extended=extended,
                                                  anonymous=anonymous,
                                                  subargs={"package" : package},
                                                  match=r".*/intel-rapl\:\d+:(\d+)",
                                                  subclass=PowercapInfoClass)
        self.package = package
        fptr = fopen(pjoin(base, "name"))
        if fptr:
            self.name = totitle(fptr.read().decode(ENCODING).strip())
            fptr.close()
        else:
            self.name = "PowercapInfoPackage{}".format(package)
        self.searchpath = pjoin(base, "intel-rapl:{}:*".format(package))
        self.package = package

    def generate(self):
        super(PowercapInfoPackage, self).generate()
        cls = PowercapInfoPackageClass(self.package, extended=self.extended)
        cls.generate()
        self._instances.append(cls)


class PowercapInfo(PathMatchInfoGroup):
    '''Class to spawn subclasses for all powercap devices
    X86 path: /sys/devices/virtual/powercap
    POWER path: /sys/firmware/opal/powercap/system-powercap
    '''
    def __init__(self, extended=False, anonymous=False):
        super(PowercapInfo, self).__init__(name="PowercapInfo",
                                           extended=extended,
                                           anonymous=anonymous)
        if platform.machine() in ["x86_64", "i386"]:
            self.subclass = PowercapInfoPackage
            self.searchpath = "/sys/devices/virtual/powercap/intel-rapl/intel-rapl:*"
            self.match = r".*/intel-rapl\:(\d+)"
        else:
            base = "/sys/firmware/opal/powercap/system-powercap"
            if pexists(base):
                self.addf("PowerLimit", pjoin(base, "powercap-current"), r"(\d+)", int)
                if extended:
                    self.addf("PowerLimitMax", pjoin(base, "powercap-max"), r"(\d+)", int)
                    self.addf("PowerLimitMin", pjoin(base, "powercap-min"), r"(\d+)", int)
            base = "/sys/firmware/opal/psr"
            if pexists(base):
                for i, fname in enumerate(glob(pjoin(base, "cpu_to_gpu_*"))):
                    key = "CpuToGpu{}".format(i)
                    self.addf(key, fname, r"(\d+)", int)
