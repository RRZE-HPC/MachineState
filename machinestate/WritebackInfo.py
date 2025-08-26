from .common import pjoin, InfoGroup

################################################################################
# Infos about the writeback behavior
################################################################################
class WritebackInfo(InfoGroup):
    def __init__(self, extended=False, anonymous=False):
        super(WritebackInfo, self).__init__(name="WritebackInfo",
                                            extended=extended,
                                            anonymous=anonymous)
        base = "/proc/sys/vm"
        self.addf("DirtyRatio", pjoin(base, "dirty_ratio"), r"(\d+)", int)
        self.addf("DirtyBackgroundRatio", pjoin(base, "dirty_background_ratio"), r"(\d+)", int)
        self.addf("DirtyBytes", pjoin(base, "dirty_bytes"), r"(\d+)", int)
        self.addf("DirtyBackgroundBytes", pjoin(base, "dirty_background_bytes"), r"(\d+)", int)
        self.addf("DirtyExpireCentisecs", pjoin(base, "dirty_expire_centisecs"), r"(\d+)", int)
        self.required(["DirtyRatio",
                       "DirtyBytes",
                       "DirtyBackgroundRatio",
                       "DirtyBackgroundBytes"])