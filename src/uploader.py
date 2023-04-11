import getopt
import os
import shutil
import sys
from constant_var import APP_NAME
from settings_handle import SettingsHandle
from utils import Utils


class UploaderConfig:
    def __init__(self):
        self.pkg = ""
        self.owner = ""
        self.repo = ""
        self.ver = ""
        self.config = ""
        self.build_type = ""
        self.settings_path = ""


class Uploader:
    """
    package uplader
    """

    def __init__(self):
        """
        init package uploader
        """
        self._usage_str = "Usage: {0} upload [OPTIONS]\n" \
            "\n" \
            "Options: \n" \
            "  -p, --pkg string        [REQUIRED] package file\n" \
            "    , --owner string      [REQUIRED] repository owner\n" \
            "    , --repo string       [REQUIRED] repository name\n" \
            "  -v, --ver string        [REQUIRED] package version\n" \
            "  -c, --config string     [OPTIONAL] package build config file\n" \
            "  -t, --build-type string [OPTIONAL] package build type, by default set release\n" \
            "  -s, --settings string   [OPTIONAL] manual set settings.xml\n" \
            "\n" \
            "e.g.\n" \
            "  {0} upload -p googletest-release-v1.13.0.tar.gz " \
            "--owner google --repo googletest --ver v1.13.0\n" \
            "  {0} upload -p mugglec-debug-v1.0.0.zip -c muggle.yml " \
            "--owner muggle --repo mugglec -v 1.0.0\n" \
            "".format(APP_NAME)

    def run(self, args):
        """
        run package uploader
        """
        if self._init(args=args) is False:
            return False

        if self._output_repo.kind == "local":
            art_output_dir = os.path.join(
                self._output_repo.path,
                self.cfg.owner,
                self.cfg.repo,
                self.cfg.ver,
                self.cfg.build_type
            )
            os.makedirs(art_output_dir, exist_ok=True)
            print("upload {} -> {}".format(self.cfg.pkg, art_output_dir))
            shutil.copy2(self.cfg.pkg, art_output_dir)

            if len(self.cfg.config) > 0:
                print("upload {} -> {}".format(self.cfg.config, art_output_dir))
                shutil.copy2(self.cfg.config, art_output_dir)
        else:
            print("WARNING! "
                  "Artifacts upload remote repo currently not support")

        return True

    def _init(self, args):
        """
        init input arguments
        """
        self.cfg = self._parse_args(args=args)
        if self.cfg is None:
            return False

        if len(self.cfg.pkg) == 0:
            print("Error! field 'pkg' missing\n\n{}".format(self._usage_str))
            return False
        if len(self.cfg.owner) == 0:
            print("Error! field 'owner' missing\n\n{}".format(self._usage_str))
            return False
        if len(self.cfg.repo) == 0:
            print("Error! field 'repo' missing\n\n{}".format(self._usage_str))
            return False
        if len(self.cfg.ver) == 0:
            print("Error! field 'ver' missing\n\n{}".format(self._usage_str))
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

    def _parse_args(self, args):
        """
        init arguments
        """
        cfg = UploaderConfig()
        opts, _ = getopt.getopt(
            args, "hp:v:o:c:t:s:",
            [
                "help", "pkg=", "owner=", "repo=",
                "ver=", "config=", "build-type=",
                "settings="
            ]
        )
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                print(self._usage_str)
                sys.exit(0)
            elif opt in ("-p", "--pkg"):
                cfg.pkg = arg
            elif opt in ("--owner"):
                cfg.owner = arg
            elif opt in ("--repo"):
                cfg.repo = arg
            elif opt in ("-v", "--ver"):
                cfg.ver = arg
            elif opt in ("-c", "--config"):
                cfg.config = arg
            elif opt in ("-t", "--build-type"):
                cfg.build_type = arg
            elif opt in ("-s", "--settings"):
                cfg.settings_path = arg

        cfg.config = Utils.expand_path(cfg.config)
        if len(cfg.build_type) == 0:
            cfg.build_type = "release"

        return cfg
