from enum import Enum
import json
from typing import OrderedDict

from hpb.platform_info import PlatformInfo
from hpb.source_info import SourceInfo

from .yaml_handle import YamlHandle


class MetaMatch(Enum):
    match = 1
    ignore = 2
    mismatch = 3


class PackageMeta:
    """
    package meta
    """

    def __init__(self):
        """
        init package meta
        """
        self.source_info: SourceInfo = SourceInfo()
        self.build_type = ""
        self.platform: PlatformInfo = PlatformInfo()
        self.deps = []
        self.is_fat_pkg = False

    def __str__(self):
        return json.dumps(OrderedDict([
            ("maintainer", self.source_info.maintainer),
            ("name", self.source_info.name),
            ("tag", self.source_info.tag),
            ("build_type", self.build_type),
            ("platform", self.platform),
            ("deps", self.deps),
        ]), indent=2)

    def __repr__(self) -> str:
        return self.__str__()

    def load(self, filepath):
        """
        load package metas
        """
        yaml_handle = YamlHandle()
        meta_info = yaml_handle.load(filepath)
        if meta_info is None:
            return False

        self.source_info.load(meta_info)
        self.build_type = meta_info.get("build_type", "")
        self.platform.load(meta_info.get("platform", {}))
        self.deps = meta_info.get("deps", [])
        self.is_fat_pkg = meta_info.get("fat_pkg", False)

        return True

    def gen_pkg_dirname(self):
        """
        generate package dir name
        """
        return "{}-{}-{}-{}-{}".format(
            self.source_info.tag,
            self.build_type,
            self.platform.system,
            self.platform.distr,
            self.platform.machine,
        )

    def gen_pkg_name(self):
        """
        generate package file name without suffix
        """
        filename = "{}".format(self.source_info.name)
        if self.source_info.tag != "":
            filename += "-{}".format(self.source_info.tag)
        if self.build_type != "":
            filename += "-{}".format(self.build_type)
        if self.platform.system != "":
            filename += "-{}".format(self.platform.system)
        if self.platform.machine != "":
            filename += "-{}".format(self.platform.machine)
        return filename

    def is_tag_match(self, tag):
        """
        check is tag match
        :param tag: compare tag
        """
        if len(tag) == 0:
            return MetaMatch.ignore
        if len(self.source_info.tag) == 0:
            return MetaMatch.ignore
        if self.source_info.tag != tag:
            return MetaMatch.mismatch
        return MetaMatch.match

    def is_build_type_match(self, build_type):
        """
        check is build type match
        :param build_type: build type
        """
        build_type = build_type.lower()
        meta_build_type = self.build_type.lower()
        if len(build_type) == 0:
            return MetaMatch.ignore
        if len(meta_build_type) == 0:
            return MetaMatch.ignore
        if meta_build_type != build_type:
            return MetaMatch.mismatch
        return MetaMatch.match

    def is_system_match(self, system_name):
        """
        check is system match
        """
        system_name = system_name.lower()
        meta_system_name = self.platform.system
        if len(system_name) == 0:
            return MetaMatch.ignore
        if len(meta_system_name) == 0:
            return MetaMatch.ignore
        if system_name != meta_system_name:
            return MetaMatch.mismatch
        return MetaMatch.match

    def is_distr_match(self, distr_info):
        """
        check is distrbution info match
        """
        if len(distr_info) == 0:
            return MetaMatch.ignore
        if len(self.platform.distr_id) == 0:
            return MetaMatch.ignore

        distr_id = ""
        distr_ver = ""
        v = distr_info.split("-")
        distr_id = v[0]
        if len(v) > 1:
            distr_ver = v[1]

        meta_distr_id = ""
        meta_distr_ver = ""
        v = self.platform.distr.split("_")
        meta_distr_id = v[0]
        if len(v) > 1:
            meta_distr_ver = v[1]

        if distr_id != meta_distr_id:
            return MetaMatch.mismatch
        if len(distr_ver) > 0 \
                and len(meta_distr_ver) > 0 \
                and distr_ver != meta_distr_ver:
            return MetaMatch.mismatch

        return MetaMatch.match

    def is_machine_match(self, machine):
        """
        check is machine match
        """
        if len(machine) == 0:
            return MetaMatch.ignore
        if len(self.platform.machine) == 0:
            return MetaMatch.ignore
        if machine != self.platform.machine:
            return MetaMatch.mismatch
        return MetaMatch
