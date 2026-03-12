from .common import InfoGroup, PathMatchInfoGroup, pjoin, pexists

################################################################################
# Infos about InfiniBand adapters
################################################################################
class InfinibandInfoClassPort(InfoGroup):
    '''Class to read the information of a single port of an InfiniBand/OmniPath driver.'''
    def __init__(self, port, extended=False, anonymous=False, driver=""):
        super(InfinibandInfoClassPort, self).__init__(
            name="Port{}".format(port), extended=extended, anonymous=anonymous)
        self.port = port
        self.driver = driver
        ibpath = "/sys/class/infiniband/{}/ports/{}".format(driver, port)
        self.addf("Rate", pjoin(ibpath, "rate"), r"(.+)")
        self.addf("PhysState", pjoin(ibpath, "phys_state"), r"(.+)")
        self.addf("LinkLayer", pjoin(ibpath, "link_layer"), r"(.+)")


class InfinibandInfoClass(PathMatchInfoGroup):
    '''Class to read the information of an InfiniBand/OmniPath driver.'''
    def __init__(self, driver, extended=False, anonymous=False):
        super(InfinibandInfoClass, self).__init__(
            name=driver, extended=extended, anonymous=anonymous)
        self.driver = driver
        ibpath = "/sys/class/infiniband/{}".format(driver)
        self.addf("BoardId", pjoin(ibpath, "board_id"), r"(.+)")
        self.addf("FirmwareVersion", pjoin(ibpath, "fw_ver"), r"([\d\.]+)")
        self.addf("HCAType", pjoin(ibpath, "hca_type"), r"([\w\d\.]+)")
        self.addf("HWRevision", pjoin(ibpath, "hw_rev"), r"([\w\d\.]+)")
        self.addf("NodeType", pjoin(ibpath, "node_type"), r"(.+)")

        if not anonymous:
            self.addf("NodeGUID", pjoin(ibpath, "node_guid"), r"(.+)")
            self.addf("NodeDescription", pjoin(ibpath, "node_desc"), r"(.+)")
            self.addf("SysImageGUID", pjoin(ibpath, "sys_image_guid"), r"(.+)")
        self.searchpath = "/sys/class/infiniband/{}/ports/*".format(driver)
        self.match = r".*/(\d+)$"
        self.subclass = InfinibandInfoClassPort
        self.subargs = {"driver" : driver}

class InfinibandInfo(PathMatchInfoGroup):
    '''Class to read InfiniBand/OmniPath (/sys/class/infiniband).'''
    def __init__(self, extended=False, anonymous=False):
        super(InfinibandInfo, self).__init__(extended=extended, anonymous=anonymous)
        self.name = "InfinibandInfo"
        if pexists("/sys/class/infiniband"):
            self.searchpath = "/sys/class/infiniband/*"
            self.match = r".*/(.*)$"
            self.subclass = InfinibandInfoClass