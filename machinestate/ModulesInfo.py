from .common import InfoGroup, which, re, os

################################################################################
# Infos about loaded modules in the modules system
################################################################################
class ModulesInfo(InfoGroup):
    '''Class to read information from the modules system'''
    def __init__(self, extended=False, anonymous=False, modulecmd="modulecmd"):
        super(ModulesInfo, self).__init__(name="ModulesInfo",
                                          extended=extended,
                                          anonymous=anonymous)
        if os.getenv("LMOD_CMD"):
            modulecmd = os.getenv("LMOD_CMD")
        self.modulecmd = modulecmd
        parse = ModulesInfo.parsemodules
        cmd_opts = "sh -t list 2>&1"
        cmd = modulecmd
        abspath = which(cmd)
        if modulecmd is not None and len(modulecmd) > 0:
            path = "{}".format(modulecmd)
            path_opts = "{}".format(cmd_opts)
            if " " in path:
                tmplist = path.split(" ")
                path = which(tmplist[0])
                path_opts = "{} {}".format(" ".join(tmplist[1:]), path_opts)
            else:
                path = which(cmd)
            abscmd = path
            cmd_opts = path_opts
        if abscmd and len(abscmd) > 0:
            self.addc("Loaded", abscmd, cmd_opts, None, parse)
    @staticmethod
    def parsemodules(value):
        slist = [ x for x in re.split("\n", value) if ";" not in x ]
        if len(slist) == 0:
            # workaround for module output `echo '<module/x.y.z>';`
            slist = [ x.split("'")[1] for x in re.split("\n", value) if "echo" in x and "'" in x ]
        if re.match("^Currently Loaded.+$", slist[0]):
            slist = slist[1:]
        return slist