from .common import InfoGroup, ListInfoGroup, process_cmd, PathMatchInfoGroup
from .common import pjoin, tobytes, tointlist, platform, re, pexists, fopen, ENCODING, glob


################################################################################
# Cache Topology
################################################################################
class CacheTopologyMacOSClass(InfoGroup):
    def __init__(self, ident, extended=False, anonymous=False):
        super(CacheTopologyMacOSClass, self).__init__(
            name=ident.upper(), extended=extended, anonymous=anonymous)
        self.ident = ident
        self.addc("Size", "sysctl", "-n hw.{}cachesize".format(ident), r"(\d+)", int)
        self.const("Level", re.match(r"l(\d+)[id]*", ident).group(1))
        if re.match(r"l\d+([id]*)", ident).group(1) == 'i':
            self.const("Type", "Instruction")
        elif re.match(r"l\d+([id]*)", ident).group(1) == 'd':
            self.const("Type", "Data")
        else:
            self.const("Type", "Unified")
        self.const("CpuList", CacheTopologyMacOSClass.getcpulist(ident))
        if extended:
            self.addc("CoherencyLineSize", "sysctl", "-n hw.cachelinesize", r"(\d+)", int)
            key = "machdep.cpu.cache.{}_associativity".format(self.name)
            out = process_cmd(("sysctl", "-n {}".format(key), r"(\d+)", int))
            if isinstance(out, int):
                self.addc("Associativity", "sysctl", "-n {}".format(key), r"(\d+)", int)
    @staticmethod
    def getcpulist(arg):
        clist = []
        level = re.match(r"l(\d+)[id]*", arg).group(1)
        if level and int(level) > 0:
            ncpus = process_cmd(("sysctl", "-n hw.ncpu", r"(\d+)", int))
            cconfig = process_cmd(("sysctl", "-n hw.cacheconfig", r"([\d\s]+)", tointlist))
            if cconfig and ncpus:
                sharedbycount = int(cconfig[int(level)])
                if sharedbycount:
                    for i in range(ncpus//sharedbycount):
                        clist.append(list(range(i*sharedbycount, (i+1)*sharedbycount)))
        return clist



class CacheTopologyMacOS(ListInfoGroup):
    def __init__(self, extended=False, anonymous=False):
        super(CacheTopologyMacOS, self).__init__(anonymous=anonymous, extended=extended)
        march = platform.machine()
        self.name = "CacheTopology"
        if march in ["x86_64"]:
            self.userlist = ["l1i", "l1d", "l2", "l3"]
        elif march in ["arm64"]:
            self.userlist = ["l1i", "l1d", "l2"]
        self.subclass = CacheTopologyMacOSClass



class CacheTopologyClass(InfoGroup):
    def __init__(self, ident, extended=False, anonymous=False):
        super(CacheTopologyClass, self).__init__(
            name="L{}".format(ident), extended=extended, anonymous=anonymous)
        self.ident = ident
        base = "/sys/devices/system/cpu/cpu0/cache/index{}".format(ident)
        fparse = CacheTopologyClass.kBtoBytes
        if pexists(base):
            self.addf("Size", pjoin(base, "size"), r"(\d+)", fparse)
            self.addf("Level", pjoin(base, "level"), r"(\d+)", int)
            self.addf("Type", pjoin(base, "type"), r"(.+)")
            self.const("CpuList", CacheTopologyClass.getcpulist(ident))
            if extended:
                self.addf("Sets", pjoin(base, "number_of_sets"), r"(\d+)", int)
                self.addf("Associativity", pjoin(base, "ways_of_associativity"), r"(\d+)", int)
                self.addf("CoherencyLineSize", pjoin(base, "coherency_line_size"), r"(\d+)", fparse)
                phys_line_part = pjoin(base, "physical_line_partition")
                if pexists(phys_line_part):

                    self.addf("PhysicalLineSize", phys_line_part, r"(\d+)", fparse)
                alloc_policy = pjoin(base, "allocation_policy")
                if pexists(alloc_policy):
                    self.addf("AllocPolicy", alloc_policy, r"(.+)")
                write_policy = pjoin(base, "write_policy")
                if pexists(write_policy):
                    self.addf("WritePolicy", write_policy, r"(.+)", int)
        self.required(list(self.files.keys()))
        #"CpuList" : (pjoin(self.searchpath, "shared_cpu_list"), r"(.+)", tointlist),
    @staticmethod
    def getcpulist(arg):
        base = "/sys/devices/system/cpu/cpu*"
        cmat = re.compile(r".*/cpu(\d+)$")
        cpus = sorted([int(cmat.match(x).group(1)) for x in glob(base) if cmat.match(x)])
        cpulist = []
        slist = []
        cpath = "cache/index{}/shared_cpu_list".format(arg)
        for cpu in cpus:
            path = pjoin("/sys/devices/system/cpu/cpu{}".format(cpu), cpath)
            filefp = fopen(path)
            if filefp:
                data = filefp.read().decode(ENCODING).strip()
                clist = tointlist(data)
                if str(clist) not in slist:
                    cpulist.append(clist)
                    slist.append(str(clist))
                filefp.close()
        return cpulist
    @staticmethod
    def kBtoBytes(value):
        return tobytes("{} kB".format(value))
    def get(self, meta=True):
        d = super(CacheTopologyClass, self).get(meta=meta)
        if "Level" in d:
            self.name = "L{}".format(d["Level"])
            if "Type" in d:
                ctype = d["Type"]
                if ctype == "Data":
                    self.name += "D"
                elif ctype == "Instruction":
                    self.name += "I"
        return d

class CacheTopology(PathMatchInfoGroup):
    def __init__(self, extended=False, anonymous=False):
        super(CacheTopology, self).__init__(anonymous=anonymous, extended=extended)
        self.name = "CacheTopology"
        self.searchpath = "/sys/devices/system/cpu/cpu0/cache/index*"
        self.match = r".*/index(\d+)$"
        self.subclass = CacheTopologyClass