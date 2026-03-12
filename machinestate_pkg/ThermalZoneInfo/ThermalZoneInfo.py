from .common import InfoGroup, PathMatchInfoGroup, pjoin, pexists, tostrlist, ENCODING

################################################################################
# Infos about the thermal zones
################################################################################
class ThermalZoneInfoClass(InfoGroup):
    '''Class to read information for one thermal zone'''
    def __init__(self, zone, extended=False, anonymous=False):
        super(ThermalZoneInfoClass, self).__init__(name="ThermalZone{}".format(zone),
                                                   extended=extended,
                                                   anonymous=anonymous)
        self.zone = zone
        base = "/sys/devices/virtual/thermal/thermal_zone{}".format(zone)
        if pexists(pjoin(base, "device/description")):
            with (open(pjoin(base, "device/description"), "rb")) as filefp:
                self.name = filefp.read().decode(ENCODING).strip()
        self.addf("Temperature", pjoin(base, "temp"), r"(\d+)", int)
        if extended:
            self.addf("Policy", pjoin(base, "policy"), r"(.+)")
            avpath = pjoin(base, "available_policies")
            self.addf("AvailablePolicies", avpath, r"(.+)", tostrlist)
            self.addf("Type", pjoin(base, "type"), r"(.+)")

class ThermalZoneInfo(PathMatchInfoGroup):
    '''Class to read information for thermal zones (/sys/devices/virtual/thermal/thermal_zone*)'''
    def __init__(self, extended=False, anonymous=False):
        spath = "/sys/devices/virtual/thermal/thermal_zone*"
        super(ThermalZoneInfo, self).__init__(name="ThermalZoneInfo",
                                              extended=extended,
                                              anonymous=anonymous,
                                              match=r".*/thermal_zone(\d+)$",
                                              searchpath=spath,
                                              subclass=ThermalZoneInfoClass)