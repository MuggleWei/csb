from enum import Enum
import json
import os

from typing import OrderedDict
from hpb.component.yaml_handle import YamlHandle
from hpb.data_type.build_info import BuildInfo
from hpb.data_type.platform_info import PlatformInfo
from hpb.data_type.semver_item import SemverItem
from hpb.data_type.source_info import SourceInfo


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
        self.build_info: BuildInfo = BuildInfo()
        self.platform: PlatformInfo = PlatformInfo()
        self.deps = []

    def __str__(self):
        return json.dumps(self.get_ordered_dict(), indent=2)

    def __repr__(self) -> str:
        return self.__str__()

    def get_ordered_dict(self):
        """
        get field ordered dict
        """
        return OrderedDict([
            ("name", self.source_info.name),
            ("maintainer", self.source_info.maintainer),
            ("tag", self.source_info.tag),
            ("platform", self.platform.get_ordered_dict()),
            ("build", self.build_info.get_ordered_dict()),
            ("deps", self.deps),
        ])

    def get_desc(self):
        """
        get desc string
        """
        desc_list = []
        desc_list.append("maintainer={}".format(self.source_info.maintainer))
        desc_list.append("name={}".format(self.source_info.name))
        desc_list.append("tag={}".format(self.source_info.tag))
        desc_list.append("system={}".format(self.platform.system))
        desc_list.append("machine={}".format(self.platform.machine))
        if self.platform.system == "linux":
            distr = ""
            if len(self.platform.distr_id) > 0:
                distr += self.platform.distr_id
            if len(self.platform.distr_ver) > 0:
                distr += "-{}".format(self.platform.distr_ver)
            desc_list.append("dist={}".format(distr))
        desc_list.append("build_type={}".format(self.build_info.build_type))
        desc_list.append("fat_pkg={}".format(self.build_info.fat_pkg))
        if self.platform.system != "windows":
            cc = ""
            if len(self.build_info.compiler_info.compiler_c) > 0:
                cc += self.build_info.compiler_info.compiler_c
            if len(self.build_info.compiler_info.compiler_c_ver) > 0:
                cc += "-{}".format(self.build_info.compiler_info.compiler_c_ver)
            desc_list.append("cc={}".format(cc))

            cxx = ""
            if len(self.build_info.compiler_info.compiler_cpp) > 0:
                cxx += self.build_info.compiler_info.compiler_cpp
            if len(self.build_info.compiler_info.compiler_cpp_ver) > 0:
                cxx += "-{}".format(
                    self.build_info.compiler_info.compiler_cpp_ver)
            desc_list.append("cxx={}".format(cxx))

            libc = ""
            if len(self.build_info.link_info.libc) > 0:
                libc += self.build_info.link_info.libc
            if len(self.build_info.link_info.libc_ver) > 0:
                libc += "-{}".format(self.build_info.link_info.libc_ver)
            desc_list.append("libc={}".format(libc))

        return ", ".join(desc_list)

    def load(self, obj):
        """
        load from object
        """
        self.source_info.load(obj)
        build_obj = obj.get("build", {})
        self.build_info.load(build_obj)
        platform_obj = obj.get("platform", {})
        self.platform.load(platform_obj)
        self.deps = obj.get("deps", [])

    def load_from_file(self, filepath):
        """
        load package metas
        """
        yaml_handle = YamlHandle()
        obj = yaml_handle.load(filepath)
        if obj is None:
            return False
        self.load(obj=obj)
        return True

    def dump(self, filepath):
        """
        dump to file
        """
        obj = json.loads(self.__str__())
        dirname = os.path.dirname(filepath)
        if not os.path.exists(dirname):
            os.makedirs(dirname, exist_ok=True)
        yaml_handle = YamlHandle()
        yaml_handle.write(filepath, obj)

    def gen_pkg_dirpath(self):
        """
        generate package directory path
        """
        dirpath = os.path.join(
            self.source_info.maintainer, self.source_info.name)
        semver = SemverItem()
        if semver.load(self.source_info.tag) is False:
            v = self.source_info.tag.split("_")
            if len(v) == 2:
                branch = v[0]
                commit_id = v[1]
                dirpath = os.path.join(dirpath, branch, commit_id)
            else:
                dirpath = os.path.join(dirpath, self.source_info.tag)
        else:
            dirpath = os.path.join(dirpath, self.source_info.tag)

        dirname = self.gen_pkg_dirname()

        return os.path.join(dirpath, dirname)

    def gen_pkg_dirname(self):
        """
        generate package dir name
        """
        return "{}-{}-{}-{}".format(
            self.build_info.build_type,
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
        if self.build_info.build_type != "":
            filename += "-{}".format(self.build_info.build_type)
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
        meta_build_type = self.build_info.build_type.lower()
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
