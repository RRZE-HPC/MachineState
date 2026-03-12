from .common import InfoGroup, process_file, re, pjoin, tointlist

################################################################################
# Helper: detect cgroup v2 and compute base path
################################################################################
def _v2_path():
    """
    Return (is_v2, base_path) for the current process.
    For v2, /proc/self/cgroup has a unified line like '0::/system.slice/...'.
    """
    try:
        with open("/proc/self/cgroup", "r", encoding="utf-8", errors="ignore") as f:
            lines = f.read().splitlines()
    except Exception:
        return False, "/sys/fs/cgroup"

    rel = "/"
    is_v2 = False
    for line in lines:
        parts = line.split(":", 2)
        # unified v2 line: controllers field empty, OR hierarchy id "0"
        if len(parts) == 3 and (parts[1] == "" or parts[0] == "0"):
            is_v2 = True
            rel = parts[2]
            break
    base = pjoin("/sys/fs/cgroup", rel.strip("/")) if rel else "/sys/fs/cgroup"
    return is_v2, base


################################################################################
# v1: keep your original logic (renamed to CgroupV1Info)
################################################################################
class CgroupV1Info:
    """Registrar for cgroup v1 cpuset info (your original logic)."""
    @staticmethod
    def register(into: InfoGroup, extended: bool):
        csetmat = re.compile(r"\d+\:cpuset\:([/\w\d\-\._]*)")
        cset = process_file(("/proc/self/cgroup", csetmat))
        if not cset:
            return
        base = pjoin("/sys/fs/cgroup/cpuset", cset.strip("/"))
        into.addf("CPUs", pjoin(base, "cpuset.cpus"), r"(.+)", tointlist)
        into.addf("Mems", pjoin(base, "cpuset.mems"), r"(.+)", tointlist)
        into.required("CPUs", "Mems")
        if extended:
            into.addf("CPUs.effective", pjoin(base, "cpuset.effective_cpus"), r"(.+)", tointlist)
            into.addf("Mems.effective", pjoin(base, "cpuset.effective_mems"), r"(.+)", tointlist)
            into.required("CPUs.effective", "Mems.effective")


################################################################################
# v2: unified hierarchy (correct filenames)
################################################################################
class CgroupV2Info:
    @staticmethod
    def register(into: InfoGroup, extended: bool):
        _, base = _v2_path()
        # Primary = effective (v2 leaf cpus/mems can be empty otherwise)
        into.addf("CPUs", pjoin(base, "cpuset.cpus.effective"), r"(.+)", tointlist)
        into.addf("Mems", pjoin(base, "cpuset.mems.effective"), r"(.+)", tointlist)
        into.required("CPUs", "Mems")
        if extended:
            # expose the same files under explicit names too (optional)
            into.addf("CPUs.effective", pjoin(base, "cpuset.cpus.effective"), r"(.+)", tointlist)
            into.addf("Mems.effective", pjoin(base, "cpuset.mems.effective"), r"(.+)", tointlist)
            # no extra required() needed


################################################################################
# Public dispatcher: keeps external API the same
################################################################################
class CgroupInfo(InfoGroup):
    def __init__(self, extended: bool = False, anonymous: bool = False):
        super().__init__(name="Cgroups", extended=extended, anonymous=anonymous)
        is_v2, _ = _v2_path()
        if is_v2:
            CgroupV2Info.register(self, extended)
        else:
            CgroupV1Info.register(self, extended)
