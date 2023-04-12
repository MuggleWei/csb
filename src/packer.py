import getopt
import os
import sys
from constant_var import APP_NAME
from utils import Utils
from yaml_handle import YamlHandle


class PackerConfig:
    def __init__(self):
        self.config = ""


class Packer:
    """
    artifacts packer
    """

    def __init__(self):
        self._usage_str = "Usage: {0} pack [OPTIONS]\n" \
            "\n" \
            "Options: \n" \
            "  -c, --config string  [OPTIONAL] pkg.yml whick builder generated, if not be set, search in current working dir\n" \
            "".format(APP_NAME)

    def run(self, args):
        """
        run pack
        """
        if self._init(args=args) is False:
            return False

        if self._load_pkg_info() is False:
            return False

    def _init(self, args):
        """
        init input arguments
        """
        self.cfg = self._parse_args(args=args)

        if len(self.cfg.config) == 0:
            print("search pkg.yml in current directory")
            working_dir = os.path.abspath(os.curdir)
            self.cfg.config = os.path.join(working_dir, "pkg.yml")

        if not os.path.exists(self.cfg.config):
            return False

        return True

    def _load_pkg_info(self):
        """
        load package info
        """
        yaml_handle = YamlHandle()
        pkg_info = yaml_handle.load(self.cfg.config)
        if pkg_info is None:
            print("failed load package config file: {}".format(self.cfg.config))
            return False

        self.deps_filepath = pkg_info["deps_file"]
        self.output_dir = pkg_info["output_dir"]
        self.pkg_dir = pkg_info["pkg_dir"]

        return True

    def _pack_output(self):
        """
        pack output files
        """
        origin_dir = os.path.abspath(os.curdir)
        os.chdir(self.output_dir)
        # TODO:
        os.chdir(origin_dir)

    def _parse_args(self, args):
        """
        init arguments
        """
        cfg = PackerConfig()
        opts, _ = getopt.getopt(
            args, "hc:", ["help", "config="]
        )

        for opt, arg in opts:
            if opt in ("-h", "--help"):
                print(self._usage_str)
                sys.exit(0)
            elif opt in ("-c", "--config"):
                cfg.config = arg

        cfg.config = Utils.expand_path(cfg.config)

        return cfg
