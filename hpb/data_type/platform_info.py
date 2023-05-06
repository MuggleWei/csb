import distro
import json
import platform

from typing import OrderedDict


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

    def __str__(self) -> str:
        return json.dumps(self.get_ordered_dict(), indent=2)

    def __repr__(self) -> str:
        return self.__str__()

    @property
    def distr(self):
        if self.system == "linux":
            str_distr = self.distr_id
            if len(self.distr_ver) > 0:
                str_distr = str_distr + "-" + self.distr_ver
            return str_distr
        else:
            return self.version

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
        else:
            self.distr_id = ""
            self.distr_ver = ""
