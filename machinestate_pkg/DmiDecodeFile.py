from .common import InfoGroup, pexists

################################################################################
# Infos from the dmidecode file (if DMIDECODE_FILE is available)
################################################################################
class DmiDecodeFile(InfoGroup):
    '''Class to read the content of a file containing the output of the dmidecode command which is
    commonly only usable with sufficient permissions. If a system administrator has dumped the
    content to a user readable file, this class includes the file.
    '''
    def __init__(self, dmifile, extended=False, anonymous=False):
        super(DmiDecodeFile, self).__init__(name="DmiDecodeFile",
                                            extended=extended,
                                            anonymous=anonymous)
        self.dmifile = dmifile
        if pexists(dmifile):
            self.addf("DmiDecode", dmifile)