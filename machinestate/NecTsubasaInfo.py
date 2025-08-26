from .common import InfoGroup, ListInfoGroup, process_cmd, which, pjoin, pexists, totitle, re, os

################################################################################
# Infos from veosinfo (NEC Tsubasa)
################################################################################
class NecTsubasaInfoTemps(InfoGroup):
    '''Class to read temperature information for one NEC Tsubasa device (uses the vecmd command)'''
    def __init__(self, tempkeys, vecmd_path="", extended=False, anonymous=False, device=0):
        super(NecTsubasaInfoTemps, self).__init__(
            name="Temperatures", extended=extended, anonymous=anonymous)
        self.tempkeys = tempkeys
        self.vecmd_path = vecmd_path
        self.deive = device
        vecmd = pjoin(vecmd_path, "vecmd")
        veargs = "-N {} info".format(device)
        for tempkey in tempkeys:
            self.addc(tempkey, vecmd, veargs, r"\s+{}\s+:\s+([\d\.]+\sC)".format(tempkey))

class NecTsubasaInfoClass(InfoGroup):
    '''Class to read information for one NEC Tsubasa device (uses the vecmd command)'''
    def __init__(self, device, vecmd_path="", extended=False, anonymous=False):
        super(NecTsubasaInfoClass, self).__init__(
            name="Card{}".format(device), extended=extended, anonymous=anonymous)
        self.device = device
        self.vecmd_path = vecmd_path
        vecmd = pjoin(vecmd_path, "vecmd")
        veargs = "-N {} info".format(device)
        if pexists(vecmd):
            self.addc("State", vecmd, veargs, r"VE State\s+:\s+(.+)", totitle)
            self.addc("Model", vecmd, veargs, r"VE Model\s+:\s+(\d+)")
            self.addc("ProductType", vecmd, veargs, r"Product Type\s+:\s+(\d+)")
            self.addc("DriverVersion", vecmd, veargs, r"VE Driver Version\s+:\s+([\d\.]+)")
            self.addc("Cores", vecmd, veargs, r"Cores\s+:\s+(\d+)")
            self.addc("MemTotal", vecmd, veargs, r"Memory Size\s+:\s+(\d+)")
            if extended:
                regex = r"Negotiated Link Width\s+:\s+(x\d+)"
                self.addc("PciLinkWidth", vecmd, veargs, regex)
            ve_temps = process_cmd((vecmd, veargs, None, NecTsubasaInfoClass.gettempkeys))
            tempargs = {"device" : device, "vecmd_path" : vecmd_path}
            cls = NecTsubasaInfoTemps(ve_temps, extended=extended, anonymous=anonymous, **tempargs)
            self._instances.append(cls)
    @staticmethod
    def gettempkeys(value):
        keys = []
        for line in re.split("\n", value):
            if re.match(r"(.+):\s+[\d\.]+\sC$", line):
                key = re.match(r"(.+):\s+[\d\.]+\sC$", line).group(1).strip()
                keys.append(key)
        return keys


class NecTsubasaInfo(ListInfoGroup):
    '''Class to spawn subclasses for each NEC Tsubasa device (uses the vecmd command)'''
    def __init__(self, vecmd_path="", extended=False, anonymous=False):
        super(NecTsubasaInfo, self).__init__(name="NecTsubasaInfo",
                                             extended=extended,
                                             anonymous=anonymous)
        self.vecmd_path = vecmd_path
        vecmd = pjoin(vecmd_path, "vecmd")
        if not pexists(vecmd):
            vecmd = which("vecmd")
            if vecmd is not None:
                vecmd_path = os.path.dirname(vecmd)
        if vecmd and len(vecmd) > 0:
            num_ves = process_cmd((vecmd, "info", r"Attached VEs\s+:\s+(\d+)", int))
            if num_ves > 0:
                self.userlist = [i for i in range(num_ves)]
                self.subclass = NecTsubasaInfoClass
                self.subargs = {"vecmd_path" : vecmd_path}