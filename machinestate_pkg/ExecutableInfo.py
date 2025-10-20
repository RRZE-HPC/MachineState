from .common import InfoGroup, MultiClassInfoGroup, psize, pexists, which, hashlib, re, os

################################################################################
# Infos about the executable (if given on cmdline)
################################################################################
class ExecutableInfoExec(InfoGroup):
    '''Class to read basic information of given executable'''
    def __init__(self, extended=False, anonymous=False, executable=None):
        super(ExecutableInfoExec, self).__init__(
            name="ExecutableInfo", anonymous=anonymous, extended=extended)
        self.executable = executable

        if executable is not None:
            abscmd = which(self.executable)
            self.const("Name", str(self.executable))
            self.required("Name")
            if abscmd and len(abscmd) > 0:
                self.const("Abspath", abscmd)
                self.const("Size", psize(abscmd))
                self.required("Size")
                if which("readelf"):
                    comp_regex = r"\s*\[\s*\d+\]\s+(.+)"
                    self.addc("CompiledWith", "readelf", "-p .comment {}".format(abscmd), comp_regex)
                    flags_regex = r"^\s*\<c\>\s+DW_AT_producer\s+:\s+\(.*\):\s*(.*)$"
                    self.addc("CompilerFlags", "readelf", "-wi {}".format(abscmd), flags_regex)
                if extended:
                    self.const("MD5sum", ExecutableInfoExec.getmd5sum(abscmd))
                    self.required("MD5sum")
            self.required(["Name", "Size"])

    @staticmethod
    def getmd5sum(filename):
        hash_md5 = hashlib.md5()
        with open(filename, "rb") as md5fp:
            for chunk in iter(lambda: md5fp.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    @staticmethod
    def getcompiledwith(value):
        for line in re.split(r"\n", value):
            if "CC" in line:
                return line
        return "Not detectable"


class ExecutableInfo(MultiClassInfoGroup):
    '''Class to spawn subclasses for analyzing a given executable'''
    def __init__(self, executable, extended=False, anonymous=False):
        super(ExecutableInfo, self).__init__(
            name="ExecutableInfo", extended=extended, anonymous=anonymous)
        self.executable = executable
        absexe = executable
        if executable is not None and not os.access(absexe, os.X_OK):
            absexe = which(executable)
        if absexe is not None:
            self.executable = absexe
            ldd = which("ldd")
            objd = which("objdump")
            self.classlist = [ExecutableInfoExec]
            clsargs = {"executable" : self.executable}
            self.classargs = [clsargs for i in range(len(self.classlist))]
            if self.executable is not None:
                if ldd is not None:
                    self.addc("LinkedLibraries", ldd, absexe, r"(.*)", ExecutableInfo.parseLdd)
                if objd is not None:
                    parser = ExecutableInfo.parseNeededLibs
                    self.addc("NeededLibraries", objd, "-p {}".format(absexe), parse=parser)
    @staticmethod
    def parseLdd(lddinput):
        libdict = {}
        if lddinput:
            libregex = re.compile(r"\s*([^\s]+)\s+.*")
            pathregex = re.compile(r"\s*[^\s]+\s+=>\s+([^\s(]+).*")
            for line in lddinput.split("\n"):
                libmat = libregex.search(line)
                if libmat:
                    lib = libmat.group(1)
                    pathmat = pathregex.search(line)
                    if pathmat:
                        libdict.update({lib : pathmat.group(1)})
                    elif pexists(lib):
                        libdict.update({lib : lib})
                    else:
                        libdict.update({lib : None})
        return libdict
    @staticmethod
    def parseNeededLibs(data):
        libs = []
        for line in data.split("\n"):
            m = re.match(r"^\s+NEEDED\s+(.*)$", line)
            if m:
                libs.append(m.group(1))
        return libs
