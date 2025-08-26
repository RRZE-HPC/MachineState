from .common import pjoin, masktolist
from .common import InfoGroup

################################################################################
# Infos about the writeback workqueue
################################################################################
class WritebackWorkqueue(InfoGroup):
    def __init__(self, extended=False, anonymous=False):
        super(WritebackWorkqueue, self).__init__(name="WritebackWorkqueue",
                                                 extended=extended,
                                                 anonymous=anonymous)
        base = "/sys/bus/workqueue/devices/writeback"
        self.addf("CPUmask", pjoin(base, "cpumask"), r"([0-9a-fA-F]+)", masktolist)
        self.addf("MaxActive", pjoin(base, "max_active"), r"(\d+)", int)
        self.addf("NUMA", pjoin(base, "numa"), r"(\d+)", int)
        self.required(["CPUmask", "MaxActive", "NUMA"])