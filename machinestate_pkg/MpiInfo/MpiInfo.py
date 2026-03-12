from .common import InfoGroup, ListInfoGroup
from .common import which, re

################################################################################
# Infos about MPI libraries
################################################################################
class MpiInfoClass(InfoGroup):
    '''Class to read information about an MPI or job scheduler executable'''
    def __init__(self, executable, extended=False, anonymous=False):
        super(MpiInfoClass, self).__init__(name=executable, extended=extended, anonymous=anonymous)
        self.executable = executable
        self.addc("Version", executable, "--version", None, MpiInfoClass.mpiversion)
        self.addc("Implementor", executable, "--version", None, MpiInfoClass.mpivendor)
        abscmd = which(executable)
        if abscmd and len(abscmd) > 0:
            self.const("Path", abscmd)
        self.required(["Version", "Implementor"])

    @staticmethod
    def mpivendor(value):
        if "Open MPI" in value or "OpenRTE" in value:
            return "OpenMPI"
        elif "Intel" in value and "MPI" in value:
            return "IntelMPI"
        elif "slurm" in value.lower():
            return "Slurm"
        elif "fujitsu" in value.lower():
            return "Fujitsu"
        return "Unknown"

    @staticmethod
    def mpiversion(value):
        for line in value.split("\n"):
            mat = re.search(r"(\d+\.\d+\.\d+)", line)
            if mat:
                return mat.group(1)
            mat = re.search(r"Version (\d+) Update (\d+) Build (\d+) \(id: (\d+)\)", line)
            if mat:
                return "{}.{}".format(mat.group(1), mat.group(2))

class MpiInfo(ListInfoGroup):
    '''Class to spawn subclasses for various MPI/job scheduler commands'''
    def __init__(self, extended=False, anonymous=False):
        super(MpiInfo, self).__init__(name="MpiInfo", extended=extended)
        self.mpilist = ["mpiexec", "mpiexec.hydra", "mpirun", "srun", "aprun"]
        self.subclass = MpiInfoClass
        self.userlist = [m for m in self.mpilist if which(m)]
        if extended:
            ompi = which("ompi_info")
            if ompi and len(ompi) > 0 and extended:
                ompi_args = "--parseable --params all all --level 9"
                self.addc("OpenMpiParams", ompi, ompi_args, parse=MpiInfo.openmpiparams)
            impi = which("impi_info")
            if impi and len(impi) > 0 and extended:
                self.addc("IntelMpiParams", impi, "| grep \"|\"", parse=MpiInfo.intelmpiparams)
    @staticmethod
    def openmpiparams(value):
        outdict = {}
        for line in value.split("\n"):
            if not line.strip(): continue
            if ":help:" in line or ":type:" in line: continue
            llist = re.split(r":", line)
            outdict[":".join(llist[:-1])] = llist[-1]
        return outdict
    @staticmethod
    def intelmpiparams(value):
        outdict = {}
        # process output to overcome bug in impi_info 2021
        value = value.replace("\n", "").replace("|I_MPI", "\n|I_MPI")
        for line in value.split("\n"):
            if "I_MPI" not in line: continue
            if not line.strip(): continue
            llist = [x.strip() for x in line.split("|")]
            outdict[llist[1]] = llist[2]
        return outdict