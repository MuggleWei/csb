import json
from typing import OrderedDict
from hpb.component.command_handle import CommandHandle


class CompilerInfo:
    """
    compiler information
    """

    def __init__(self):
        self.compiler_c = ""
        self.compiler_c_ver = ""
        self.compiler_cpp = ""
        self.compiler_cpp_ver = ""

    def __str__(self) -> str:
        return json.dumps(self.get_ordered_dict(), indent=2)

    def __repr__(self) -> str:
        return self.__str__()

    def get_ordered_dict(self):
        """
        get field ordered dict
        """
        return OrderedDict([
            ("cc", self.compiler_c),
            ("cc_ver", self.compiler_c_ver),
            ("cxx", self.compiler_cpp),
            ("cxx_ver", self.compiler_cpp_ver),
        ])

    def load(self, obj):
        """
        load object
        """
        self.compiler_c = obj.get("cc", "")
        self.compiler_c_ver = obj.get("cc_ver", "")
        self.compiler_cpp = obj.get("cxx", "")
        self.compiler_cpp_ver = obj.get("cxx_ver", "")

    def load_local_env(self, cc, cxx):
        """
        load by local env
        """
        return self._load_local_gcc_like(cc, cxx)

    def load_local_gcc(self):
        """
        load local gcc information
        """
        return self._load_local_gcc_like(cc="gcc", cxx="g++")

    def load_local_clang(self):
        """
        load local clang information
        """
        return self._load_local_gcc_like(cc="clang", cxx="clang++")

    def load_local_musl_gcc(self):
        """
        load local musl-gcc information
        """
        return self._load_local_gcc_like(cc="musl-gcc", cxx="musl-g++")

    def _load_local_gcc_like(self, cc, cxx):
        # c compiler
        outs, errs = CommandHandle().call("{} -dumpversion".format(cc))
        if len(errs) > 0:
            return False
        self.compiler_c = cc
        self.compiler_c_ver = outs[0]

        # cpp compiler
        outs, errs = CommandHandle().call("{} -dumpversion".format(cxx))
        if len(errs) > 0:
            return False
        self.compiler_cpp = cxx
        self.compiler_cpp_ver = outs[0]

        return True
