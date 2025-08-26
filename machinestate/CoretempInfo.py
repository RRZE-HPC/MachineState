from .common import InfoGroup, PathMatchInfoGroup, pjoin, process_file, platform

################################################################################
# Infos about the temperature using coretemp
################################################################################
class CoretempInfoHwmonClassX86(InfoGroup):
    '''Class to read information for one X86 coretemps sensor inside one hwmon entry and device'''
    def __init__(self, sensor, extended=False, anonymous=False, socket=0, hwmon=0):
        base = "/sys/devices/platform/coretemp.{}/hwmon/hwmon{}/".format(socket, hwmon)
        super(CoretempInfoHwmonClassX86, self).__init__(
            name=process_file((pjoin(base, "temp{}_label".format(sensor)),)),
            extended=extended,
            anonymous=anonymous)
        self.sensor = sensor
        self.socket = socket
        self.hwmon = hwmon
        self.addf("Input", pjoin(base, "temp{}_input".format(sensor)), r"(\d+)", int)
        self.required("Input")
        if extended:
            self.addf("Critical", pjoin(base, "temp{}_crit".format(sensor)), r"(\d+)", int)
            self.addf("Alarm", pjoin(base, "temp{}_crit_alarm".format(sensor)), r"(\d+)", int)
            self.addf("Max", pjoin(base, "temp{}_max".format(sensor)), r"(\d+)", int)

class CoretempInfoHwmonX86(PathMatchInfoGroup):
    '''Class to spawn subclasses for one hwmon entry inside a X86 coretemps device'''
    def __init__(self, hwmon, extended=False, anonymous=False, socket=0):
        super(CoretempInfoHwmonX86, self).__init__(
            name="Hwmon{}".format(hwmon), extended=extended, anonymous=anonymous)
        self.hwmon = hwmon
        self.socket = socket
        self.subclass = CoretempInfoHwmonClassX86
        self.subargs = {"socket" : socket, "hwmon" : hwmon}
        base = "/sys/devices/platform/coretemp.{}".format(socket)
        self.searchpath = pjoin(base, "hwmon/hwmon{}/temp*_label".format(hwmon))
        self.match = r".*/temp(\d+)_label$"

class CoretempInfoSocketX86(PathMatchInfoGroup):
    '''Class to spawn subclasses for one X86 coretemps device'''
    def __init__(self, socket, extended=False, anonymous=False):
        super(CoretempInfoSocketX86, self).__init__(
            name="Package{}".format(socket), extended=extended, anonymous=anonymous)
        self.socket = socket
        self.subargs = {"socket" : socket}
        self.subclass = CoretempInfoHwmonX86
        self.searchpath = "/sys/devices/platform/coretemp.{}/hwmon/hwmon*".format(self.socket)
        self.match = r".*/hwmon(\d+)$"

class CoretempInfoHwmonClassARM(InfoGroup):
    '''Class to read information for one ARM coretemps sensor inside one hwmon entry'''
    def __init__(self, sensor, extended=False, anonymous=False, hwmon=0):
        super(CoretempInfoHwmonClassARM, self).__init__(
            name="Core{}".format(sensor), extended=extended, anonymous=anonymous)
        self.sensor = sensor
        self.hwmon = hwmon
        base = "/sys/devices/virtual/hwmon/hwmon{}".format(hwmon)
        self.addf("Input", pjoin(base, "temp{}_input".format(sensor)), r"(\d+)", int)
        self.required("Input")
        if extended:
            self.addf("Critical", pjoin(base, "temp{}_crit".format(sensor)), r"(\d+)", int)

class CoretempInfoSocketARM(PathMatchInfoGroup):
    '''Class to spawn subclasses for ARM coretemps for one hwmon entry'''
    def __init__(self, hwmon, extended=False, anonymous=False):
        super(CoretempInfoSocketARM, self).__init__(
            name="Hwmon{}".format(hwmon), extended=extended, anonymous=anonymous)
        self.hwmon = hwmon
        self.searchpath = "/sys/devices/virtual/hwmon/hwmon{}/temp*_input".format(hwmon)
        self.match = r".*/temp(\d+)_input$"
        self.subclass = CoretempInfoHwmonClassARM
        self.subargs = {"hwmon" : hwmon}

class CoretempInfo(PathMatchInfoGroup):
    '''Class to spawn subclasses to get all information for coretemps
    X86 path: /sys/devices/platform/coretemp.*
    ARM64 path: /sys/devices/virtual/hwmon/hwmon*
    '''
    def __init__(self, extended=False, anonymous=False):
        super(CoretempInfo, self).__init__(name="CoretempInfo",
                                           extended=extended,
                                           anonymous=anonymous)
        machine = platform.machine()
        if machine in ["x86_64", "i386"]:
            self.subclass = CoretempInfoSocketX86
            self.searchpath = "/sys/devices/platform/coretemp.*"
            self.match = r".*/coretemp\.(\d+)$"
        elif machine in ["aarch64"]:
            self.subclass = CoretempInfoSocketARM
            self.searchpath = "/sys/devices/virtual/hwmon/hwmon*"
            self.match = r".*/hwmon(\d+)$"
