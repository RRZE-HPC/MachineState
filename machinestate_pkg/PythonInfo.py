from .common import InfoGroup, ListInfoGroup
from .common import which

################################################################################
# Infos about Python interpreters
################################################################################
class PythonInfoClass(InfoGroup):
    '''Class to read information about a Python executable'''
    def __init__(self, executable, extended=False, anonymous=False):
        super(PythonInfoClass, self).__init__(
            name=executable, extended=extended, anonymous=anonymous)
        self.executable = executable
        abspath = which(executable)
        if abspath and len(abspath) > 0:
            self.addc("Version", abspath, "--version 2>&1", r"(\d+\.\d+\.\d+)")
            self.const("Path", abspath)
        self.required("Version")

class PythonInfo(ListInfoGroup):
    '''Class to spawn subclasses for various Python commands'''
    def __init__(self, extended=False, anonymous=False):
        self.interpreters = ["python2", "python3", "python"]
        super(PythonInfo, self).__init__(name="PythonInfo",
                                         extended=extended,
                                         anonymous=anonymous,
                                         subclass=PythonInfoClass,
                                         userlist=[i for i in self.interpreters if which(i)])
