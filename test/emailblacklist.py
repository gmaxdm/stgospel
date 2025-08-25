
class EmailBlacklist:

    @classmethod
    def blacklist(cls):
        if not hasattr(cls, "_bl"):
            cls._bl = set()
            with open("../email_blacklist.txt") as f:
                for line in f:
                    cls._bl.add(line.strip())
        return cls._bl

    @classmethod
    def userlist(cls):
        if not hasattr(cls, "_ubl"):
            cls._ubl = set()
            with open("../user_blacklist.txt") as f:
                for line in f:
                    cls._ubl.add(line.strip())
        return cls._ubl

    @classmethod
    def is_ban(cls, email):
        if email in cls.blacklist():
            return True
        try:
            username = email.split("@")[0]
        except IndexError:
            return True
        username = username.replace(".", "")
        if username in cls.userlist():
            return True
        return False


