import getopt
import logging
import os
import shutil
import sys
import tarfile

from hpb.component.yaml_handle import YamlHandle
from hpb.data_type.constant_var import APP_NAME
from hpb.data_type.package_meta import PackageMeta
from hpb.utils.utils import Utils


class PackerConfig:
    def __init__(self):
        self.config = ""
        self.copy_to = ""
        self.move_to = ""


class Packer:
    """
    artifacts packer
    """

    def __init__(self):
        self._usage_str = "Usage: {0} pack [OPTIONS]\n" \
            "\n" \
            "Options: \n" \
            "  -o, --copy-to string [OPTIONAL] copy generated artifacts to destination directory\n" \
            "    , --move-to string [OPTIONAL] move generated artifacts to destination directory, if it's be set, --copy-to will be ignored\n" \
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

        self._handle_fat_pkg()

        if self._pack_output() is False:
            return False

        if self._copy_meta_files() is False:
            return False

        self._user_copy()

        return True

    def _init(self, args):
        """
        init input arguments
        """
        self.cfg = self._parse_args(args=args)

        if len(self.cfg.config) == 0:
            logging.info("search pkg.yml in current directory")
            working_dir = os.path.abspath(os.curdir)
            self.cfg.config = os.path.join(working_dir, "pkg.yml")

        if not os.path.exists(self.cfg.config):
            logging.error("file not exists: {}".format(self.cfg.config))
            return False

        return True

    def _load_pkg_info(self):
        """
        load package info
        """
        yaml_handle = YamlHandle()
        pkg_info = yaml_handle.load(self.cfg.config)
        if pkg_info is None:
            logging.error(
                "failed load package config file: {}".format(self.cfg.config))
            return False

        self.meta_file = pkg_info["meta_file"]
        self.output_dir = pkg_info["output_dir"]
        self.pkg_dir = pkg_info["pkg_dir"]
        self.deps_dir = pkg_info["deps_dir"]

        self.pkg_meta = PackageMeta()
        if self.pkg_meta.load_from_file(filepath=self.meta_file) is False:
            logging.error(
                "failed load package meta file: {}".format(self.meta_file))
            return False

        return True

    def _handle_fat_pkg(self):
        """
        handle fat package
        """
        if not self.pkg_meta.build_info.fat_pkg:
            return

        if not os.path.exists(self.deps_dir):
            return

        shutil.copytree(
            src=self.deps_dir,
            dst=self.output_dir,
            symlinks=True,
            dirs_exist_ok=True
        )

    def _pack_output(self):
        """
        pack output files
        """
        filename = self.pkg_meta.gen_pkg_name()
        filename += ".tar.gz"

        origin_dir = os.path.abspath(os.curdir)
        os.chdir(self.output_dir)
        logging.info("change dir to: {}".format(self.output_dir))

        logging.info("tar: {}".format(filename))
        files = os.listdir(self.output_dir)
        with tarfile.open(filename, "w:gz", format=tarfile.GNU_FORMAT) as tar:
            for f in files:
                logging.info("add {}".format(f))
                tar.add(f)

        os.chdir(origin_dir)
        logging.info("restore dir to: {}".format(origin_dir))

        src_filepath = os.path.join(self.output_dir, filename)
        dst_filepath = os.path.join(self.pkg_dir, filename)

        shutil.move(src_filepath, dst_filepath)

        logging.info("move package to {}".format(dst_filepath))

    def _copy_meta_files(self):
        """
        copy meta files
        """
        shutil.copy(self.meta_file, self.pkg_dir)

    def _user_copy(self):
        """
        copy or move
        """
        if len(self.cfg.move_to) == 0 and len(self.cfg.copy_to) == 0:
            return

        files = os.listdir(self.pkg_dir)
        for f in files:
            src_f = os.path.join(self.pkg_dir, f)
            if len(self.cfg.move_to) != 0:
                dst_dir = self.cfg.move_to
                logging.info("move {} -> {}".format(src_f, dst_dir))
                shutil.move(src_f, dst_dir)
            elif len(self.cfg.copy_to) != 0:
                dst_dir = self.cfg.copy_to
                logging.info("copy {} -> {}".format(src_f, dst_dir))
                shutil.copytree(
                    self.pkg_dir, self.cfg.copy_to, dirs_exist_ok=True)

    def _parse_args(self, args):
        """
        init arguments
        """
        cfg = PackerConfig()
        try:
            opts, _ = getopt.getopt(
                args, "hc:o:", [
                    "help", "config=", "copy-to=", "move-to="
                ]
            )
        except Exception as e:
            logging.error("{}, exit...".format(str(e)))
            sys.exit(1)

        for opt, arg in opts:
            if opt in ("-h", "--help"):
                print(self._usage_str)
                sys.exit(0)
            elif opt in ("-c", "--config"):
                cfg.config = arg
            elif opt in ("-o", "--copy-to"):
                cfg.copy_to = arg
            elif opt in ("--move-to"):
                cfg.move_to = arg

        cfg.config = Utils.expand_path(cfg.config)

        return cfg
