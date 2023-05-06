import json
import platform
from typing import OrderedDict

from hpb.component.command_handle import CommandHandle


class LinkInfo:
    def __init__(self):
        self.libc = ""
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
            ("libc", self.libc),
            ("libc_ver", self.libc_ver),
        ])

    def load(self, obj):
        """
        load object
        """
        self.libc = obj.get("libc", "")
        self.libc_ver = obj.get("libc_ver", "")

    def load_local_libc(self):
        """
        get libc info
        """
        # libc info
        libc_ver_pair = platform.libc_ver()
        if len(libc_ver_pair) > 0 and len(libc_ver_pair[0]) == 0:
            # maybe musl libc
            libc_ver_pair = self._get_musl_info()

        if len(libc_ver_pair) > 0:
            self.libc = libc_ver_pair[0]
        if len(libc_ver_pair) > 1:
            self.libc_ver = libc_ver_pair[1]

    def _get_musl_info(self):
        """
        get musl libc information
        """
        outs, errs = CommandHandle().call("ldd --version")
        if len(errs) > 0:
            return ("", "")

        libc = ""
        libc_ver = ""
        for line in outs:
            if "musl" in line:
                libc = "musl-libc"

            line.find("Version")
            v = line.split("")
            libc_ver = v[-1]

        return (libc, libc_ver)
