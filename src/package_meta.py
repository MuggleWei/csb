from yaml_handle import YamlHandle


class PackageMeta:
    """
    package meta
    """

    def __init__(self):
        pass

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
        self.platform_distro = self.platform.get("distr", "")
        self.platform_libc = self.platform.get("libc", "")

        return True

    def gen_pkg_dirname(self):
        """
        generate package dir name
        """
        return "{}@{}@{}@{}@{}".format(
            self.tag,
            self.build_type,
            self.platform_name,
            self.platform_distro,
            self.platform_machine,
        )
