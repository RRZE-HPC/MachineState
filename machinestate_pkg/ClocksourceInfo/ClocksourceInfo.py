from .common import InfoGroup, PathMatchInfoGroup, pjoin, tostrlist

################################################################################
# Infos about the clock sources provided by the kernel
################################################################################
class ClocksourceInfoClass(InfoGroup):
    '''Class to read information for one clocksource device'''
    def __init__(self, ident, extended=False, anonymous=False):
        super(ClocksourceInfoClass, self).__init__(anonymous=anonymous, extended=extended)
        self.ident = ident
        self.name = "Clocksource{}".format(ident)
        base = "/sys/devices/system/clocksource/clocksource{}".format(ident)
        self.addf("Current", pjoin(base, "current_clocksource"), r"(\S+)", str)
        if extended:
            self.addf("Available", pjoin(base, "available_clocksource"), r"(.+)", tostrlist)
        self.required("Current")

class ClocksourceInfo(PathMatchInfoGroup):
    '''Class to spawn subclasses for all clocksourse devices
    /sys/devices/system/clocksource/clocksource*
    '''
    def __init__(self, extended=False, anonymous=False):
        super(ClocksourceInfo, self).__init__(anonymous=anonymous, extended=extended)
        self.name = "ClocksourceInfo"
        self.searchpath = "/sys/devices/system/clocksource/clocksource*"
        self.match = r".*/clocksource(\d+)$"
        self.subclass = ClocksourceInfoClass