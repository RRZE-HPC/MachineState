from .common import pjoin, tointlist, glob, os, re, fopen, pexists, ENCODING
from .common import process_cmd
from .common import InfoGroup, ListInfoGroup, PathMatchInfoGroup


################################################################################
# CPU Topology
################################################################################
class CpuTopologyMacOSClass(InfoGroup):
    def __init__(self, ident, extended=False, anonymous=False, ncpu=1, ncores=1, ncores_pack=1):
        super(CpuTopologyMacOSClass, self).__init__(
            name="Cpu{}".format(ident), anonymous=anonymous, extended=extended)
        self.ident = ident
        self.ncpu = ncpu
        self.ncores = ncores
        self.ncores_pack = ncores_pack
        smt = ncpu/ncores
        self.const("ThreadId", int(ident % smt))
        self.const("CoreId", int(ident//smt))
        self.const("PackageId", int(ident//ncores_pack))
        self.const("HWThread", ident)
        self.required("CoreId", "PackageId", "HWThread", "ThreadId")

class CpuTopologyMacOS(ListInfoGroup):
    def __init__(self, extended=False, anonymous=False):
        super(CpuTopologyMacOS, self).__init__(
            name="CpuTopology", anonymous=anonymous, extended=extended)
        ncpu = process_cmd(("sysctl", "-a", r"hw.logicalcpu: (\d+)", int))
        ncores_pack = process_cmd(("sysctl", "-a", r"machdep.cpu.cores_per_package: (\d+)", int))
        ncores = process_cmd(("sysctl", "-a", r"machdep.cpu.core_count: (\d+)", int))
        if isinstance(ncpu, int) and isinstance(ncores_pack, int) and isinstance(ncores, int):
            self.userlist = list(range(ncpu))
            self.subclass = CpuTopologyMacOSClass
            self.subargs = {"ncpu" : ncpu, "ncores" : ncores, "ncores_pack" : ncores_pack}
            self.const("NumHWThreads", ncpu)
            self.const("SMTWidth", ncpu//ncores)
            self.const("NumCores", ncores)
            self.const("NumSockets", ncpu//ncores_pack)
            self.const("NumNUMANodes", ncpu//ncores_pack)

class CpuTopologyClass(InfoGroup):
    def __init__(self, ident, extended=False, anonymous=False):
        super(CpuTopologyClass, self).__init__(anonymous=anonymous, extended=extended)
        self.name = "Cpu{}".format(ident)
        self.ident = ident
        base = "/sys/devices/system/cpu/cpu{}".format(ident)
        self.addf("CoreId", pjoin(base, "topology/core_id"), r"(\d+)", int)
        self.addf("PackageId", pjoin(base, "topology/physical_package_id"), r"(\d+)", int)
        self.const("DieId", CpuTopologyClass.getdieid(ident))
        self.const("HWThread", ident)
        self.const("ThreadId", CpuTopologyClass.getthreadid(ident))
        if os.access(pjoin(base, "topology/cluster_id"), os.R_OK):
            self.addf("ClusterId", pjoin(base, "topology/cluster_id"), r"(\d+)", int)
        if extended:
            self.const("Present", CpuTopologyClass.inlist("present", ident))
            self.const("Online", CpuTopologyClass.inlist("online", ident))
            self.const("Isolated", CpuTopologyClass.inlist("isolated", ident))
            self.const("Possible", CpuTopologyClass.inlist("possible", ident))
            self.const("NumaNode", CpuTopologyClass.getnumnode(ident))
            self.required("Online", "Possible", "Isolated")
        self.required("CoreId", "PackageId", "HWThread", "ThreadId")

    @staticmethod
    def getthreadid(hwthread):
        base = "/sys/devices/system/cpu/cpu{}/topology/thread_siblings_list".format(hwthread)
        outfp = fopen(base)
        tid = 0
        if outfp:
            data = outfp.read().decode(ENCODING).strip()
            outfp.close()
            if data:
                dlist = tointlist(data)
                if len(dlist) > 0:
                    return dlist.index(hwthread)

        return tid
    @staticmethod
    def inlist(filename, hwthread):
        fp = fopen(pjoin("/sys/devices/system/cpu", filename))
        if fp is not None:
            data = fp.read().decode(ENCODING).strip()
            if data is not None and len(data) > 0:
                l = tointlist(data)
                return int(hwthread) in l
        return False

    @staticmethod
    def getnumnode(hwthread):
        base = "/sys/devices/system/cpu/cpu{}/node*".format(hwthread)
        nmatch = re.compile(r".+/node(\d+)")
        dlist = [f for f in glob(base) if nmatch.match(f) ]
        if len(dlist) > 1:
            print("WARN: Hardware thread {} contains to {} NUMA nodes".format(hwthread, len(dlist)))
        return max(int(nmatch.match(dlist[0]).group(1)), 0)

    @staticmethod
    def getdieid(hwthread):
        base = "/sys/devices/system/cpu/cpu{}/topology/".format(hwthread)
        path = pjoin(base, "die_id")
        if not os.access(path, os.R_OK):
            path = pjoin(base, "physical_package_id")
        fp = fopen(path)
        if fp is not None:
            data = fp.read().decode(ENCODING).strip()
            return int(data)

class CpuTopology(PathMatchInfoGroup):
    def __init__(self, extended=False, anonymous=False):
        super(CpuTopology, self).__init__(extended=extended, anonymous=anonymous)
        self.name = "CpuTopology"
        self.searchpath = "/sys/devices/system/cpu/cpu*"
        self.match = r".*/cpu(\d+)$"
        self.subclass = CpuTopologyClass
        self.const("NumHWThreads", CpuTopology.getnumcpus())
        self.const("NumNUMANodes", CpuTopology.getnumnumanodes())
        self.const("SMTWidth", CpuTopology.getsmtwidth())
        self.const("NumSockets", CpuTopology.getnumpackages())
        self.const("NumCores", CpuTopology.getnumcores())

    @staticmethod
    def getnumcpus():
        searchpath = "/sys/devices/system/cpu/cpu*"
        match = r".*/cpu(\d+)$"
        if searchpath and match and pexists(os.path.dirname(searchpath)):
            mat = re.compile(match)
            base = searchpath
            glist = sorted([int(mat.match(f).group(1)) for f in glob(base) if mat.match(f)])
            return max(len(glist), 1)
        return 0
    @staticmethod
    def getnumnumanodes():
        searchpath = "/sys/devices/system/node/node*"
        match = r".*/node(\d+)$"
        if searchpath and match and pexists(os.path.dirname(searchpath)):
            mat = re.compile(match)
            base = searchpath
            glist = sorted([int(mat.match(f).group(1)) for f in glob(base) if mat.match(f)])
            return max(len(glist), 1)
        return 0
    @staticmethod
    def getsmtwidth():
        filefp = fopen("/sys/devices/system/cpu/cpu0/topology/thread_siblings_list")
        if filefp:
            data = filefp.read().decode(ENCODING).strip()
            filefp.close()
            if data:
                dlist = tointlist(data)
                if dlist:
                    return max(len(dlist), 1)
        return 1
    @staticmethod
    def getnumpackages():
        flist = glob("/sys/devices/system/cpu/cpu*/topology/physical_package_id")
        plist = []
        for fname in flist:
            filefp = fopen(fname)
            if filefp:
                data = filefp.read().decode(ENCODING).strip()
                filefp.close()
                if data:
                    pid = int(data)
                    if pid not in plist:
                        plist.append(pid)
        return max(len(plist), 1)
    @staticmethod
    def getnumcores():
        dlist = glob("/sys/devices/system/cpu/cpu*/topology")
        pcdict = {}
        for dname in dlist:
            cfname = pjoin(dname, "core_id")
            pfname = pjoin(dname, "physical_package_id")
            with fopen(pfname) as pfp:
                with fopen(cfname) as cfp:
                    pdata = pfp.read().decode(ENCODING).strip()
                    cdata = cfp.read().decode(ENCODING).strip()
                    if pdata and cdata:
                        pid = int(pdata)
                        cid = int(cdata)
                        if pid in pcdict:
                            if cid not in pcdict[pid]:
                                pcdict[pid].append(cid)
                        else:
                            pcdict[pid] = [cid]
        pcsum = [len(pcdict[x]) for x in pcdict]
        pcmin = min(pcsum)
        pcmax = max(pcsum)
        pcavg = sum(pcsum)/len(pcsum)
        if pcmin != pcavg or pcmax != pcavg:
            print("WARN: Unbalanced CPU cores per socket")
        return max(sum(pcsum), 1)