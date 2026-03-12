from .common import which, process_cmd, pexists, pjoin, tohertz, InfoGroup, re, os

################################################################################
# Infos about the turbo frequencies (LIKWID only)
################################################################################
class TurboInfo(InfoGroup):
    '''Class to read information about CPU/Uncore frequencies and perf-energy-bias
    (uses the likwid-powermeter command)
    '''
    def __init__(self, extended=False, anonymous=False, likwid_base=None):
        super(TurboInfo, self).__init__(name="TurboInfo", extended=extended, anonymous=anonymous)
        self.likwid_base = likwid_base
        cmd = "likwid-powermeter"
        cmd_opts = "-i 2>&1"
        error_matches = [r".*Cannot gather values.*",
                         r".*Cannot get access.*",
                         r".*Query Turbo Mode only supported.*",
                         r"^Failed.*",
                         r"^ERROR .*"]
        names = ["BaseClock", "MinClock", "MinUncoreClock", "MaxUncoreClock"]
        matches = [r"Base clock:\s+([\d\.]+ MHz)",
                   r"Minimal clock:\s+([\d\.]+ MHz)",
                   r"Minimal Uncore frequency:\s+([\d\.]+ MHz)",
                   r"Maximal Uncore frequency:\s+([\d\.]+ MHz)",
                  ]
        if likwid_base and len(likwid_base) > 0 and os.path.isdir(likwid_base):
            tmpcmd = pjoin(likwid_base, cmd)
            if pexists(tmpcmd):
                abscmd = tmpcmd
        else:
            abscmd = which(cmd)
        if abscmd:
            data = process_cmd((abscmd, cmd_opts, matches[0]))
            if len(data) > 0:
                err = False
                for l in data.split("\n"):
                    for regex in error_matches:
                        if re.match(regex, data):
                            err = True
                            break
                if not err:
                    for name, regex in zip(names, matches):
                        self.addc(name, abscmd, cmd_opts, regex, tohertz)
                        self.required(name)
                    regex = r"^Performance energy bias:\s+(\d+)"
                    self.addc("PerfEnergyBias", abscmd, cmd_opts, regex, int)
                    self.required("PerfEnergyBias")
                    freqfunc = TurboInfo.getactivecores
                    self.addc("TurboFrequencies", abscmd, cmd_opts, None, freqfunc)
    @staticmethod
    def getactivecores(indata):
        freqs = []
        for line in re.split(r"\n", indata):
            mat = re.match(r"C(\d+)\s+([\d\.]+ MHz)", line)
            if mat:
                freqs.append(tohertz(mat.group(2)))
        return freqs