from .common import InfoGroup, PathMatchInfoGroup
from .common import pjoin


################################################################################
# Infos about hugepages
################################################################################
class HugepagesClass(InfoGroup):
    '''Class to read information about one size of hugepages'''
    def __init__(self, size, extended=False, anonymous=False):
        name = "Hugepages-{}".format(size)
        super(HugepagesClass, self).__init__(name=name, extended=extended, anonymous=anonymous)
        self.size = size
        base = "/sys/kernel/mm/hugepages/hugepages-{}".format(size)
        self.addf("Count", pjoin(base, "nr_hugepages"), r"(\d+)", int)
        self.addf("Free", pjoin(base, "free_hugepages"), r"(\d+)", int)
        self.addf("Reserved", pjoin(base, "resv_hugepages"), r"(\d+)", int)

class Hugepages(PathMatchInfoGroup):
    '''Class to spawn subclasses for all hugepages sizes (/sys/kernel/mm/hugepages/hugepages-*)'''
    def __init__(self, extended=False, anonymous=False):
        super(Hugepages, self).__init__(extended=extended, anonymous=anonymous)
        self.name = "Hugepages"
        self.searchpath = "/sys/kernel/mm/hugepages/hugepages-*"
        self.match = r".*/hugepages-(\d+[kKMG][B])"
        self.subclass = HugepagesClass