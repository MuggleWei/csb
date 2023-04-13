import getopt
import os
import shutil
import sys
from constant_var import APP_NAME
from package_meta import PackageMeta
from settings_handle import SettingsHandle
from utils import Utils
from yaml_handle import YamlHandle


class UploaderConfig:
    def __init__(self):
        self.pkg_dir = ""
        self.pkg_file = ""
        self.settings_path = ""


class Uploader:
    """
    package uplader
    """

    def __init__(self):
        """
        init package uploader
        """
        self._usage_str = "Usage: {0} push [OPTIONS]\n" \
            "\n" \
            "Options: \n" \
            "  -d, --pkg-dir string    [OPTIONAL] package directory, by default, search ./pkg.yml to find package directory\n" \
            "  -p, --pkg-file string   [OPTIONAL] package file, by default, search ./pkg.yml to find package directory\n" \
            "  -s, --settings string   [OPTIONAL] manual set settings.xml\n" \
            "\n" \
            "e.g.\n" \
            "  {0} push" \
            "  {0} push -p ./pkg.yml" \
            "  {0} push -d pkg" \
            "\n" \
            "NOTE: \n" \
            "  When specify -d and -p in the same time, will ignore -p\n" \
            "".format(APP_NAME)

    def run(self, args):
        """
        run package uploader
        """
        if self._init(args=args) is False:
            return False

        self.meta_file = os.path.join(self.pkg_dir, "{}.yml".format(APP_NAME))
        self.pkg_meta = PackageMeta()
        if self.pkg_meta.load(filepath=self.meta_file) is False:
            return False

        if self._output_repo.kind == "local":
            dir_name = self.pkg_meta.gen_pkg_dirname()
            art_output_dir = os.path.join(
                self._output_repo.path,
                self.pkg_meta.maintainer,
                self.pkg_meta.repo,
                dir_name,
            )
            if os.path.exists(art_output_dir):
                shutil.rmtree(art_output_dir)
            print("push {} -> {}".format(self.pkg_dir, art_output_dir))
            shutil.copytree(self.pkg_dir, art_output_dir)
        else:
            print("WARNING! "
                  "Artifacts push to remote repo currently not support")

        return True

    def _init(self, args):
        """
        init input arguments
        """
        self.cfg = self._parse_args(args=args)
        if self.cfg is None:
            return False

        self.pkg_dir = ""
        self.pkg_file = Utils.expand_path("./pkg.yml")
        if len(self.cfg.pkg_dir) != 0:
            self.pkg_dir = self.cfg.pkg_dir
        if len(self.cfg.pkg_file) != 0:
            self.pkg_file = self.cfg.pkg_file

        if len(self.pkg_dir) == 0:
            self.pkg_dir = self._get_pkg_dir_from_yml(self.pkg_file)
        if len(self.pkg_dir) == 0:
            return False

        user_settings = []
        if len(self.cfg.settings_path) > 0:
            user_settings.append(self.cfg.settings_path)
        self._settings_handle = SettingsHandle.load_settings(user_settings)

        if self._settings_handle.pkg_upload_repo is None:
            print("ERROR! 'artifacts/upload' not be set in settings file")
            return False
        self._output_repo = self._settings_handle.pkg_upload_repo

        return True

    def _get_pkg_dir_from_yml(self, filepath):
        """
        get pkg dir from yml file
        """
        yaml_handle = YamlHandle()
        pkg_info = yaml_handle.load(filepath)
        if pkg_info is None:
            print("failed load package config file: {}".format(filepath))
            return ""
        return pkg_info["pkg_dir"]

    def _parse_args(self, args):
        """
        parse arguments
        """
        cfg = UploaderConfig()
        opts, _ = getopt.getopt(
            args, "hd:p:s:",
            [
                "help", "pkg-dir=", "pkg-file=", "settings="
            ]
        )
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                print(self._usage_str)
                sys.exit(0)
            elif opt in ("-d", "--pkg-dir"):
                cfg.pkg_dir = arg
            elif opt in ("-p", "--pkg-file"):
                cfg.pkg_file = arg
            elif opt in ("-s", "--settings"):
                cfg.settings_path = arg

        cfg.pkg_dir = Utils.expand_path(cfg.pkg_dir)
        cfg.pkg_file = Utils.expand_path(cfg.pkg_file)

        return cfg
