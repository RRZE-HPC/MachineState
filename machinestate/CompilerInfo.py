from .common import InfoGroup, ListInfoGroup, MultiClassInfoGroup
from .common import which, os

################################################################################
# Infos about compilers (C, C++ and Fortran)
################################################################################
class CompilerInfoClass(InfoGroup):
    '''Class to read version and path of a given executable'''
    def __init__(self, executable, extended=False, anonymous=False):
        super(CompilerInfoClass, self).__init__(extended=extended, anonymous=anonymous)
        self.executable = executable
        self.name = executable
        self.addc("Version", executable, "--version", r"(\d+\.\d+\.\d+)")
        abscmd = which(executable)
        if abscmd and len(abscmd) > 0:
            self.const("Path", abscmd)
        self.required("Version")


class CCompilerInfo(ListInfoGroup):
    '''Class to spawn subclasses for various C compilers'''
    def __init__(self, extended=False, anonymous=False):
        super(CCompilerInfo, self).__init__(name="C",
                                            extended=extended,
                                            subclass=CompilerInfoClass,
                                            anonymous=anonymous)

        self.compilerlist = ["gcc", "icc", "clang", "pgcc", "xlc", "xlC", "armclang", "fcc", "fccpx"]
        self.subclass = CompilerInfoClass
        if "CC" in os.environ:
            comp = os.environ["CC"]
            if comp not in self.compilerlist:
                self.compilerlist.append(comp)
        self.userlist = [c for c in self.compilerlist if which(c)]


class CPlusCompilerInfo(ListInfoGroup):
    '''Class to spawn subclasses for various C++ compilers'''
    def __init__(self, extended=False, anonymous=False):
        super(CPlusCompilerInfo, self).__init__(name="C++",
                                                extended=extended,
                                                subclass=CompilerInfoClass,
                                                anonymous=anonymous)

        self.compilerlist = ["g++", "icpc", "clang++", "pg++", "xlc++", "armclang++", "FCC", "FCCpx"]
        self.subclass = CompilerInfoClass
        if "CXX" in os.environ:
            comp = os.environ["CXX"]
            if comp not in self.compilerlist:
                self.compilerlist.append(comp)
        self.userlist = [c for c in self.compilerlist if which(c)]


class FortranCompilerInfo(ListInfoGroup):
    '''Class to spawn subclasses for various Fortran compilers'''
    def __init__(self, extended=False, anonymous=False):
        super(FortranCompilerInfo, self).__init__(name="Fortran",
                                                  extended=extended,
                                                  subclass=CompilerInfoClass,
                                                  anonymous=anonymous)

        self.compilerlist = ["gfortran", "ifort", "flang", "pgf90",
                             "xlf", "xlf90", "xlf95", "xlf2003", "xlf2008",
                             "armflang", "frt", "frtpx"]
        if "FC" in os.environ:
            comp = os.environ["FC"]
            if comp not in self.compilerlist:
                self.compilerlist.append(comp)
        self.userlist = [c for c in self.compilerlist if which(c)]

class AcceleratorCompilerInfo(ListInfoGroup):
    '''Class to spawn subclasses for various compilers used with accelerators'''
    def __init__(self, extended=False, anonymous=False):
        super(AcceleratorCompilerInfo, self).__init__(name="Accelerator",
                                                      extended=extended,
                                                      subclass=CompilerInfoClass,
                                                      anonymous=anonymous)
        self.compilerlist = ["nvcc", "hipcc", "icx", "icpx", "dpcpp",
                             "clocl", "nfort", "ncc", "nc++", "rocm-clang-ocl"]
        self.userlist = [c for c in self.compilerlist if which(c)]

class CompilerInfo(MultiClassInfoGroup):
    '''Class to spawn subclasses for various compilers'''
    def __init__(self, extended=False, anonymous=False):
        clist = [CCompilerInfo, CPlusCompilerInfo, FortranCompilerInfo, AcceleratorCompilerInfo]
        cargs = [{} for i in range(len(clist))]
        super(CompilerInfo, self).__init__(name="CompilerInfo",
                                           extended=extended,
                                           anonymous=anonymous,
                                           classlist=clist,
                                           classargs=cargs)