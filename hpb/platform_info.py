import json
import platform
from typing import OrderedDict

import distro


class PlatformInfo:
    """
    platform informations
    """

    def __init__(self):
        """
        init platform infos
        """
        self.system = ""
        self.release = ""
        self.ver = ""
        self.machine = ""
        self.distr_id = ""
        self.distr_ver = ""
        self.distr = ""
        self.libc_id = ""
        self.libc_ver = ""
        self.libc = ""

    def __str__(self) -> str:
        return json.dumps(OrderedDict([
            ("system", self.system),
            ("release", self.release),
            ("version", self.ver),
            ("machine", self.machine),
            ("distr_id", self.distr_id),
            ("distr_ver", self.distr_ver),
            ("distr", self.distr),
            ("libc_id", self.libc_id),
            ("libc_ver", self.libc_ver),
            ("libc", self.libc),
        ]), indent=2)

    def __repr__(self) -> str:
        return self.__str__()

    def load(self, obj):
        """
        load from object
        """
        self.system = obj.get("system", "")
        self.release = obj.get("release", "")
        self.version = obj.get("version", "")
        self.machine = obj.get("machine", "")
        self.distr_id = obj.get("distr_id", "")
        self.distr_ver = obj.get("distr_ver", "")
        self.distr = obj.get("distr", "")
        self.libc_id = obj.get("libc_id", "")
        self.libc_ver = obj.get("libc_ver", "")
        self.libc = obj.get("libc", "")

    def load_local(self):
        """
        load local platform infos
        """
        self.system = platform.system().lower()
        self.release = platform.release()
        self.ver = platform.version()
        self.machine = platform.machine()

        if self.system == "linux":
            self.distr_id = distro.id()
            self.distr_ver = distro.version()
            if len(self.distr_ver) > 0:
                self.distr = "{}_{}".format(
                    self.distr_id, self.distr_ver)
            else:
                self.distr = self.distr_id

            v = platform.libc_ver()
            if len(v) > 0:
                self.libc_id = v[0]
            else:
                self.libc_id = ""
            if len(v) > 1:
                self.libc_ver = v[1]
            else:
                self.libc_ver = ""
            self.libc = "-".join(v)
        else:
            self.distr_id = ""
            self.distr_ver = ""
            self.distr = platform.version()
            self.libc_id = ""
            self.libc_ver = ""
            self.libc = ""
