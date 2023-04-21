import getopt
import logging
import os
import shutil
import sys
import tarfile
from hpb.component.settings_handle import SettingsHandle

from hpb.data_type.constant_var import APP_NAME
from hpb.utils.log_handle import LogHandle
from hpb.utils.utils import Utils


class DownloaderConfig:
    def __init__(self):
        self.repo_type = ""
        self.path = ""
        self.dest = ""
        self.extract = False


class Downloader:
    """
    package downloader
    """

    def __init__(self):
        """
        init package downloader
        """
        self._usage_str = "Usage: {0} pull [OPTIONS]\n" \
            "\n" \
            "Options: \n" \
            "  -p, --path string    [REQUIRED] package dir/path or url\n" \
            "  -d, --dest string    [OPTIONAL] download destination\n" \
            "  -x, --extract string [OPTIONAL] extract files from packags\n" \
            "e.g.\n" \
            "  {0} pull -p ~/.hpb/artifacts/google/googletest/v1.13.0-release-linux-arch-x86_64\n" \
            "".format(APP_NAME)

    def run(self, args):
        """
        run package downloader
        """
        try:
            cfg = self._init(args=args)
        except Exception as e:
            print("{}".format(str(e)))
            return False

        return self.download(cfg=cfg)

    def _init(self, args):
        """
        init input arguments
        """
        cfg = self._parse_args(args=args)

        if len(cfg.path) == 0:
            errmsg = "pull package without field 'path'\n\n{}".format(self._usage_str)
            raise Exception(errmsg)
        if len(cfg.repo_type) == 0:
            cfg.repo_type = self._guess_type(cfg.path)
        if len(cfg.dest) == 0:
            cfg.dest = os.path.abspath(".")

        self._settings_handle = SettingsHandle.load_settings("")
        log_level = LogHandle.log_level(self._settings_handle.log_console_level)
        LogHandle.init_log(
            filename=None,
            console_level=log_level,
            formatter=logging.Formatter("%(message)s")
        )

        return cfg

    def _guess_type(self, path):
        """
        guess download repo type
        """
        # TODO: now, only have local
        if path.startswith(""):
            pass
        return "local"

    def download(self, cfg):
        """
        download package
        """
        self.cfg: DownloaderConfig = cfg
        if self.cfg.repo_type == "local":
            ret = self._download_local()
        else:
            print("unregconize repot_type: {}".format(self.cfg.repo_type))
            ret = False

        if ret is False:
            return ret

        if self.cfg.extract is True:
            self._extract(self.cfg)

        return True

    def _extract(self, cfg):
        """
        extract artifacts
        """
        dest = Utils.expand_path(cfg.dest)
        if dest.endswith("tar.gz"):
            dest = os.path.dirname(dest)

        filename = os.path.basename(cfg.path)

        origin_dir = os.path.abspath(os.curdir)
        os.chdir(dest)

        with tarfile.open(filename) as f:
            f.extractall(".")
        os.remove(filename)

        os.chdir(origin_dir)

    def _download_local(self):
        """
        download local artifacts
        """
        self.cfg.path = Utils.expand_path(self.cfg.path)
        if os.path.isdir(self.cfg.path):
            files = os.listdir(self.cfg.path)
            candidates = []
            for f in files:
                if f.endswith("tar.gz"):
                    candidates.append(f)
            if len(candidates) == 0:
                logging.error("failed find package in {}".format(self.cfg.path))
                return False
            if len(candidates) > 1:
                logging.error("multiple package in {}".format(self.cfg.path))
                return False
            pkg_filepath = os.path.join(self.cfg.path, candidates[0])
        else:
            pkg_filepath = self.cfg.path

        dest = Utils.expand_path(self.cfg.dest)
        if dest.endswith("tar.gz"):
            dest = os.path.dirname(dest)

        if not os.path.isdir(dest):
            os.makedirs(dest, exist_ok=True)

        logging.info(
            "download local package: {} -> {}".format(pkg_filepath, dest))
        shutil.copy(pkg_filepath, dest)

        return True

    def _parse_args(self, args):
        """
        parse arguments
        """
        opts, _ = getopt.getopt(
            args, "hp:d:x",
            [
                "help", "path=", "dest=", "extract"
            ]
        )

        cfg = DownloaderConfig()
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                print(self._usage_str)
                sys.exit(0)
            elif opt in ("-p", "--path"):
                cfg.path = arg
            elif opt in ("-d", "--dest"):
                cfg.dest = arg
            elif opt in ("-x", "--extract"):
                cfg.extract = True
        return cfg
