import getopt
import logging
import sys

from hpb.component.settings_handle import SettingsHandle
from hpb.data_type.constant_var import APP_NAME
from hpb.utils.log_handle import LogHandle


class DbSyncConfig:
    def __init__(self):
        self.settings_path = ""


class DbSync:
    """
    sync local db and local artifacts directory
    """

    def __init__(self):
        self._usage_str = "Usage: {0} dbsync [OPTIONS]\n" \
            "\n" \
            "Options: \n" \
            "  -s, --settings string   [OPTIONAL] manual set settings.xml\n" \
            "".format(APP_NAME)

    def run(self, args):
        """
        run db sync
        """
        if self._init(args=args) is False:
            return False

        logging.info("run dbsync: {}".format(args))

        return True

    def _init(self, args):
        """
        init input arguments
        """
        cfg = self._parse_args(args=args)
        if cfg is None:
            return False

        try:
            self._settings_handle = \
                SettingsHandle.load_settings(cfg.settings_path)
        except Exception as e:
            print("ERROR! {}".format(str(e)))
            return False

        log_level = LogHandle.log_level(self._settings_handle.log_console_level)
        LogHandle.init_log(
            filename=None,
            console_level=log_level,
            formatter=logging.Formatter("%(message)s")
        )

        return True

    def _parse_args(self, args) -> DbSyncConfig:
        """
        parse arguments
        """
        cfg = DbSyncConfig()
        try:
            opts, _ = getopt.getopt(
                args, "hs:",
                [
                    "help", "settings="
                ]
            )
        except Exception as e:
            print("{}, exit...".format(str(e)))
            sys.exit(1)

        for opt, arg in opts:
            if opt in ("-h", "--help"):
                print(self._usage_str)
                sys.exit(0)
            elif opt in ("-s", "--settings"):
                cfg.settings_path = arg
        return cfg
