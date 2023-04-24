import json
import logging
import os
import platform

from typing import OrderedDict
from hpb.data_type.compiler_info import CompilerInfo
from hpb.utils.utils import Utils


class BuildInfo:
    """
    build info
    """

    def __init__(self):
        self.build_type = ""
        self.fat_pkg = False
        self.compiler_info = CompilerInfo()

    def __str__(self) -> str:
        return json.dumps(self.get_ordered_dict(), indent=2)

    def __repr__(self) -> str:
        return self.__str__()

    def get_ordered_dict(self):
        """
        get field ordered dict
        """
        return OrderedDict([
            ("build_type", self.build_type),
            ("fat_pkg", self.fat_pkg),
            ("compiler", self.compiler_info.get_ordered_dict()),
        ])

    def load(self, obj):
        """
        load from object
        """
        self.build_type = obj.get("build_type", "")

        self.fat_pkg = obj.get("fat_pkg", False)
        self.fat_pkg = Utils.get_boolean(self.fat_pkg)

        self.compiler_info.load(obj.get("compiler", {}))

    def complement(self):
        """
        complement empty info
        """
        if self._complement_compiler_info() is True:
            logging.info("success complement compiler info")

    def _complement_compiler_info(self):
        """
        complement compiler information
        """
        curr_sys = platform.system()
        curr_sys = curr_sys.lower()
        if curr_sys == "windows":
            pass
        else:
            return self._complement_compiler_unix_like()

    def _complement_compiler_unix_like(self):
        """
        complement unix-like compiler information
        """
        env_cc = os.environ.get("CC", "")
        env_cxx = os.environ.get("CXX", "")
        if len(env_cc) != 0 and len(env_cxx) != 0:
            return self.compiler_info.load_local_env(cc=env_cc, cxx=env_cxx)
        else:
            if self.compiler_info.load_local_gcc() is True:
                return True
            if self.compiler_info.load_local_clang() is True:
                return True
        return False
