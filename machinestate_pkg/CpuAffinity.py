from .common import InfoGroup, pexists, which, tointlist, DO_LIKWID, LIKWID_PATH, os

################################################################################
# Infos about the CPU affinity
# Some Python versions provide a os.get_schedaffinity()
# If not available, use LIKWID (if allowed)
################################################################################
class CpuAffinity(InfoGroup):
    '''Class to read information the CPU affinity for the session using Python's
    os.get_schedaffinity or likwid-pin if available
    '''
    def __init__(self, extended=False, anonymous=False):
        super(CpuAffinity, self).__init__(name="CpuAffinity",
                                          extended=extended,
                                          anonymous=anonymous)
        if "get_schedaffinity" in dir(os):
            self.const("Affinity", os.get_schedaffinity())
        elif DO_LIKWID and LIKWID_PATH and pexists(LIKWID_PATH):
            abscmd = which("likwid-pin")
            if abscmd and len(abscmd) > 0:
                self.addc("Affinity", abscmd, "-c N -p 2>&1", r"(.*)", tointlist)
                self.required("Affinity")
        else:
            abscmd = which("taskset")
            if abscmd and len(abscmd) > 0:
                regex = r".*current affinity list: (.*)"
                self.addc("Affinity", abscmd, "-c -p $$", regex, tointlist)
                self.required("Affinity")
