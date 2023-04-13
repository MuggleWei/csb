from enum import Enum
import json

from yaml_handle import YamlHandle


class MetaMatch(Enum):
    match = 1
    ignore = 2
    mismatch = 3


class PackageMeta:
    """
    package meta
    """

    def __init__(self):
        pass

    def __str__(self):
        return json.dumps({
            "maintainer": self.maintainer,
            "repo": self.repo,
            "build_type": self.build_type,
            "platform": {
                "name": self.platform_name,
                "release": self.platform_release,
                "ver": self.platform_ver,
                "machine": self.platform_machine,
                "distr_id": self.platform_distro_id,
                "distr_ver": self.platform_distro_ver,
                "libc": self.platform_libc,
            }
        }, indent=2)

    def __repr__(self) -> str:
        return self.__str__()

    def load(self, filepath):
        """
        load package metas
        """
        yaml_handle = YamlHandle()
        self.meta_info = yaml_handle.load(filepath)
        if self.meta_info is None:
            return False

        self.maintainer = self.meta_info.get("maintainer", "")
        self.repo = self.meta_info.get("repo", "")
        self.tag = self.meta_info.get("tag", "")
        self.build_type = self.meta_info.get("build_type", "")

        self.platform = self.meta_info.get("platform", {})
        self.platform_name = self.platform.get("system", "")
        self.platform_release = self.platform.get("release", "")
        self.platform_ver = self.platform.get("version", "")
        self.platform_machine = self.platform.get("machine", "")
        self.platform_distro_id = self.platform.get("distr_id", "")
        self.platform_distro_ver = self.platform.get("distr_ver", "")
        self.platform_distro = self.platform.get("distr", "")
        self.platform_libc = self.platform.get("libc", "")

        self.deps = self.meta_info.get("deps", [])
        self.is_fat_pkg = self.meta_info.get("fat_pkg", False)

        return True

    def gen_pkg_dirname(self):
        """
        generate package dir name
        """
        return "{}-{}-{}-{}-{}".format(
            self.tag,
            self.build_type,
            self.platform_name,
            self.platform_distro,
            self.platform_machine,
        )

    def gen_pkg_name(self):
        """
        generate package file name without suffix
        """
        filename = "{}".format(self.repo)
        if self.tag != "":
            filename += "-{}".format(self.tag)
        if self.build_type != "":
            filename += "-{}".format(self.build_type)
        if self.platform_name != "":
            filename += "-{}".format(self.platform_name)
        if self.platform_machine != "":
            filename += "-{}".format(self.platform_machine)
        return filename

    def is_tag_match(self, tag):
        """
        check is tag match
        :param tag: compare tag
        """
        if len(tag) == 0:
            return MetaMatch.ignore
        if len(self.tag) == 0:
            return MetaMatch.ignore
        if self.tag != tag:
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
        meta_system_name = self.platform_name.lower()
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
        if len(self.platform_distro_id) == 0:
            return MetaMatch.ignore

        distr_id = ""
        distr_ver = ""
        v = distr_info.split("-")
        distr_id = v[0]
        if len(v) > 1:
            distr_ver = v[1]

        meta_distr_id = ""
        meta_distr_ver = ""
        v = self.platform_distro.split("_")
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
        if len(self.platform_machine) == 0:
            return MetaMatch.ignore
        if machine != self.platform_machine:
            return MetaMatch.mismatch
        return MetaMatch
