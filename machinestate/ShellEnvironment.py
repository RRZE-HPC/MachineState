from .common import InfoGroup, os, re, getuser, getgrgid

################################################################################
# Infos about environ variables
################################################################################
class ShellEnvironment(InfoGroup):
    '''Class to read the shell environment (os.environ)'''
    def __init__(self, extended=False, anonymous=False):
        super(ShellEnvironment, self).__init__(extended=extended, anonymous=anonymous)
        self.name = "ShellEnvironment"
        for k,v in os.environ.items():
            value = v
            if self.anonymous:
                value = ShellEnvironment.anonymous_shell_var(k, v)
            self.const(k, value)

    def update(self):
        super(ShellEnvironment, self).update()
        outdict = {}
        for k,v in os.environ.items():
            value = v
            if self.anonymous:
                value = ShellEnvironment.anonymous_shell_var(k, v)
            self._data[k] = value

    @staticmethod
    def anonymous_shell_var(key, value):
        out = value
        ipregex = re.compile(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")
        for ipaddr in ipregex.findall(value):
            out = out.replace(ipaddr, "XXX.XXX.XXX.XXX")
        out = out.replace(getuser(), "anonuser")
        for i, group in enumerate(os.getgroups()):
            gname = getgrgid(group)
            out = out.replace(gname.gr_name, "group{}".format(i))
        return out