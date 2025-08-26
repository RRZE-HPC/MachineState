from .common import InfoGroup, process_file, re, pjoin, tointlist 

################################################################################
# Infos about CGroups
################################################################################
class CgroupInfo(InfoGroup):
    def __init__(self, extended=False, anonymous=False):
        super(CgroupInfo, self).__init__(name="Cgroups", extended=extended, anonymous=anonymous)
        csetmat = re.compile(r"\d+\:cpuset\:([/\w\d\-\._]*)")
        cset = process_file(("/proc/self/cgroup", csetmat))
        if cset is not None:
            base = pjoin("/sys/fs/cgroup/cpuset", cset.strip("/"))
            self.addf("CPUs", pjoin(base, "cpuset.cpus"), r"(.+)", tointlist)
            self.addf("Mems", pjoin(base, "cpuset.mems"), r"(.+)", tointlist)
            self.required("CPUs", "Mems")
            if extended:
                names = ["CPUs.effective", "Mems.effective"]
                files = ["cpuset.effective_cpus", "cpuset.effective_mems"]
                for key, fname in zip(names, files):
                    self.addf(key, pjoin(base, fname), r"(.+)", tointlist)
                    self.required(key)