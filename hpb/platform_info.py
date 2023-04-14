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
        self.version = ""
        self.machine = ""
        self.distr_id = ""
        self.distr_ver = ""
        self.libc_id = ""
        self.libc_ver = ""

    def __str__(self) -> str:
        return json.dumps(self.get_ordered_dict(), indent=2)

    def __repr__(self) -> str:
        return self.__str__()

    def get_ordered_dict(self):
        """
        get field ordered dict
        """
        return OrderedDict([
            ("system", self.system),
            ("release", self.release),
            ("version", self.version),
            ("machine", self.machine),
            ("distr_id", self.distr_id),
            ("distr_ver", self.distr_ver),
            ("libc_id", self.libc_id),
            ("libc_ver", self.libc_ver),
        ])

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
        self.libc_id = obj.get("libc_id", "")
        self.libc_ver = obj.get("libc_ver", "")

    def load_local(self):
        """
        load local platform infos
        """
        self.system = platform.system().lower()
        self.release = platform.release()
        self.version = platform.version()
        self.machine = platform.machine()

        if self.system == "linux":
            self.distr_id = distro.id()
            self.distr_ver = distro.version()

            v = platform.libc_ver()
            if len(v) > 0:
                self.libc_id = v[0]
            else:
                self.libc_id = ""
            if len(v) > 1:
                self.libc_ver = v[1]
            else:
                self.libc_ver = ""
        else:
            self.distr_id = ""
            self.distr_ver = ""
            self.libc_id = ""
            self.libc_ver = ""
