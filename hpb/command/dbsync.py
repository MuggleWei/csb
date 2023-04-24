import getopt
import logging
import sys

from hpb.data_type.constant_var import APP_NAME


class DbSyncConfig:
    def __init__(self):
        self.settings_path = ""


class DbSync:
    """
    sync local db and local package directory
    """

    def __init__(self):
        self._usage_str = "Usage: {0} dbsync [OPTIONS]\n" \
            "\n" \
            "Options: \n" \
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

        return True

    def _parse_args(self, args) -> DbSyncConfig:
        """
        parse arguments
        """
        cfg = DbSyncConfig()
        try:
            opts, _ = getopt.getopt(
                args, "h",
                [
                    "help"
                ]
            )
        except Exception as e:
            print("{}, exit...".format(str(e)))
            sys.exit(1)

        for opt, _ in opts:
            if opt in ("-h", "--help"):
                print(self._usage_str)
                sys.exit(0)
        return cfg
