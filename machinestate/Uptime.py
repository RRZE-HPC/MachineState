from .common import InfoGroup, re, datetime, timedelta

################################################################################
# Infos about the uptime of the system
################################################################################
class UptimeMacOs(InfoGroup):
    def __init__(self, extended=False, anonymous=False):
        super(UptimeMacOs, self).__init__(name="Uptime", extended=extended, anonymous=anonymous)
        timematch = re.compile(r"\d+:\d+.*\s+(\d+:\d+).*")
        self.addc("Uptime", "uptime", cmd_opts=None, match=r"(.*)", parse=UptimeMacOs.parsetime)
        self.addc("UptimeReadable", "uptime", None, None, UptimeMacOs.parsereadable)
        self.required("Uptime")
    @staticmethod
    def parsetime(string):
        timematch = re.compile(r"\d+:\d+.*\s+(\d+):(\d+).*")
        daymatch = re.compile(r"\d+:\d+\s+up (\d+) days.*")
        tm = timematch.match(string)
        if tm:
            days = 0
            dm = daymatch.match(string)
            if dm:
                days = dm.group(1)
            hours, minutes = tm.groups()
            uptime = int(days) * 86400 + int(hours) * 3600 + int(minutes) * 60
            return float(uptime)
        return None
    @staticmethod
    def parsereadable(string):
        uptime = UptimeMacOs.parsetime(string)
        if uptime is not None:
            return Uptime.totimedelta(uptime)
        return "Cannot parse uptime"


class Uptime(InfoGroup):
    def __init__(self, extended=False, anonymous=False):
        super(Uptime, self).__init__(name="Uptime", extended=extended, anonymous=anonymous)
        fname = "/proc/uptime"
        self.addf("Uptime", fname, r"([\d\.]+)\s+[\d\.]+", float)
        self.addf("UptimeReadable", fname, r"([\d\.]+)\s+[\d\.]+", Uptime.totimedelta)

        self.required("Uptime")
        if extended:
            self.addf("CpusIdle", fname, r"[\d\.]+\s+([\d\.]+)", float)
    @staticmethod
    def totimedelta(value):
        ivalue = int(float(value))
        msec = int((float(value) - ivalue)*1000)
        minutes = int(ivalue/60)
        hours = int(minutes/60)
        days = int(hours/24)
        weeks = int(days/7)
        seconds = ivalue % 60
        date = datetime.now() - timedelta(weeks=weeks,
                                          days=days,
                                          hours=hours,
                                          minutes=minutes,
                                          seconds=seconds,
                                          milliseconds=msec)
        return date.ctime()