from .common import InfoGroup, PathMatchInfoGroup, masktolist

################################################################################
# Infos about interrupt handling
# see https://pyperf.readthedocs.io/en/latest/system.html#system-cmd-ops
################################################################################
class IrqAffinityClass(InfoGroup):
    '''Class to read information about one interrupt affinity'''
    def __init__(self, irq, extended=False, anonymous=False):
        super(IrqAffinityClass, self).__init__(name="irq{}".format(irq),
                                               extended=extended,
                                               anonymous=anonymous)
        self.irq = irq
        self.addf("SMPAffinity", "/proc/irq/{}/smp_affinity".format(irq), parse=masktolist)

class IrqAffinity(PathMatchInfoGroup):
    '''Class to read information about one interrupt affinity'''
    def __init__(self, extended=False, anonymous=False):
        super(IrqAffinity, self).__init__(name="IrqAffinity",
                                          extended=extended,
                                          anonymous=anonymous,
                                          searchpath="/proc/irq/*",
                                          match=r".*/(\d+)",
                                          subclass=IrqAffinityClass)
        self.addf("DefaultSMPAffinity", "/proc/irq/default_smp_affinity", parse=masktolist)
