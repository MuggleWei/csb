import getopt
import os
import shutil
import sys
import tarfile

from .constant_var import APP_NAME
from .package_meta import PackageMeta
from .utils import Utils
from .yaml_handle import YamlHandle


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

        if self._pack_output() is False:
            return False

        if self._copy_meta_files() is False:
            return False

        return True

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

        self.meta_file = pkg_info["meta_file"]
        self.output_dir = pkg_info["output_dir"]
        self.pkg_dir = pkg_info["pkg_dir"]

        self.pkg_meta = PackageMeta()
        if self.pkg_meta.load(filepath=self.meta_file) is False:
            return False

        return True

    def _pack_output(self):
        """
        pack output files
        """
        filename = self.pkg_meta.gen_pkg_name()
        filename += ".tar.gz"

        origin_dir = os.path.abspath(os.curdir)
        os.chdir(self.output_dir)
        print("change dir to: {}".format(self.output_dir))

        print("tar: {}".format(filename))
        files = os.listdir(self.output_dir)
        with tarfile.open(filename, "w:gz") as tar:
            for f in files:
                print("add {}".format(f))
                tar.add(f)

        os.chdir(origin_dir)
        print("restore dir to: {}".format(origin_dir))

        src_filepath = os.path.join(self.output_dir, filename)
        dst_filepath = os.path.join(self.pkg_dir, filename)
        shutil.move(src_filepath, dst_filepath)

    def _copy_meta_files(self):
        """
        copy meta files
        """
        shutil.copy(self.meta_file, self.pkg_dir)

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
