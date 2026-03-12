from .common import InfoGroup, ListInfoGroup, process_cmd, PathMatchInfoGroup
from .common import pjoin, tobytes, tointlist
from .MemInfo import MemInfoMacOS


################################################################################
# NUMA Topology
################################################################################
class NumaInfoMacOSClass(InfoGroup):
    def __init__(self, node, anonymous=False, extended=False):
        super(NumaInfoMacOSClass, self).__init__(
            name="NumaNode{}".format(node), anonymous=anonymous, extended=extended)
        self.node = node
        self.addc("MemTotal", "sysctl", "-a", r"hw.memsize: (\d+)", int)
        self.addc("MemFree", "sysctl", "-a", r"vm.page_free_count: (\d+)", MemInfoMacOS.pagescale)
        self.addc("CpuList", "sysctl", "-a", r"hw.cacheconfig: (\d+)", NumaInfoMacOSClass.cpulist)
    @staticmethod
    def cpulist(value):
        ncpu = process_cmd(("sysctl", "-n hw.ncpu", r"(\d+)", int))
        clist = []
        if isinstance(ncpu, int):
            for i in range(ncpu//int(value)):
                clist.append(list(range(i*ncpu, (i+1)*ncpu)))
        return clist

class NumaInfoMacOS(ListInfoGroup):
    def __init__(self, anonymous=False, extended=False):
        super(NumaInfoMacOS, self).__init__(name="NumaInfo", anonymous=anonymous, extended=extended)
        self.subclass = NumaInfoMacOSClass
        num_packs = process_cmd(("sysctl", "-n hw.packages", r"(\d+)", int))
        if num_packs is not None and num_packs > 0:
            self.userlist = list(range(num_packs))

class NumaInfoHugepagesClass(InfoGroup):
    def __init__(self, size, extended=False, anonymous=False, node=0):
        super(NumaInfoHugepagesClass, self).__init__(name="Hugepages-{}".format(size),
                                                     extended=extended,
                                                     anonymous=anonymous)
        self.size = size
        self.node = node
        base = "/sys/devices/system/node/node{}/hugepages/hugepages-{}".format(node, size)
        self.addf("Count", pjoin(base, "nr_hugepages"), r"(\d+)", int)
        self.addf("Free", pjoin(base, "free_hugepages"), r"(\d+)", int)
        self.required(["Count", "Free"])

class NumaInfoClass(PathMatchInfoGroup):
    def __init__(self, node, anonymous=False, extended=False):
        super(NumaInfoClass, self).__init__(anonymous=anonymous, extended=extended)
        self.node = node
        self.name = "NumaNode{}".format(node)
        base = "/sys/devices/system/node/node{}".format(node)
        meminfo = pjoin(base, "meminfo")
        prefix = "Node {}".format(node)
        regex = r"(\d+\s[kKMG][B])"
        self.addf("MemTotal", meminfo, r"{} MemTotal:\s+{}".format(prefix, regex), tobytes)
        self.addf("MemFree", meminfo, r"{} MemFree:\s+{}".format(prefix, regex), tobytes)
        self.addf("MemUsed", meminfo, r"{} MemUsed:\s+{}".format(prefix, regex), tobytes)
        self.addf("Distances", pjoin(base, "distance"), r"(.*)", tointlist)
        self.addf("CpuList", pjoin(base, "cpulist"), r"(.*)", tointlist)

        if extended:
            self.addf("Writeback", meminfo, r"{} Writeback:\s+{}".format(prefix, regex), tobytes)

        self.required("MemTotal", "MemFree", "CpuList")
        self.searchpath = "/sys/devices/system/node/node{}/hugepages/hugepages-*".format(node)
        self.match = r".*/hugepages-(\d+[kKMG][B])$"
        self.subclass = NumaInfoHugepagesClass
        self.subargs = {"node" : node}

class NumaInfo(PathMatchInfoGroup):
    def __init__(self, extended=False, anonymous=False):
        super(NumaInfo, self).__init__(name="NumaInfo", extended=extended, anonymous=anonymous)
        self.searchpath = "/sys/devices/system/node/node*"
        self.match = r".*/node(\d+)$"
        self.subclass = NumaInfoClass