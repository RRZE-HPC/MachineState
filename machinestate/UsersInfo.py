from .common import InfoGroup, re

################################################################################
# Infos about logged in users (only count to avoid logging user names)
################################################################################
class UsersInfo(InfoGroup):
    '''Class to get count of logged in users. Does not print out the usernames'''
    def __init__(self, extended=False, anonymous=False):
        super(UsersInfo, self).__init__(name="UsersInfo", extended=extended, anonymous=anonymous)
        self.addc("LoggedIn", "users", "", r"(.*)", UsersInfo.countusers)
        self.required("LoggedIn")
    @staticmethod
    def countusers(value):
        if not value or len(value) == 0:
            return 0
        return len(list(set(re.split(r"[,\s]", value))))