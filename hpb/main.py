import logging
import sys

from hpb.__version__ import __version__
from hpb.command.builder import Builder
from hpb.command.dbsync import DbSync
from hpb.command.downloader import Downloader
from hpb.command.packer import Packer
from hpb.command.searcher import Searcher
from hpb.command.uploader import Uploader
from hpb.component.settings_handle import SettingsHandle
from hpb.utils.log_handle import LogHandle


def run_builder():
    """
    run builder
    """
    builder = Builder()
    if builder.run(sys.argv[2:]) is False:
        sys.exit(1)


def run_push():
    """
    upload package
    """
    uploader = Uploader()
    if uploader.run(sys.argv[2:]) is False:
        sys.exit(1)


def run_search():
    """
    search package
    """
    searcher = Searcher()
    if searcher.run(sys.argv[2:]) is False:
        sys.exit(1)


def run_pull():
    """
    pull package
    """
    downloader = Downloader()
    if downloader.run(sys.argv[2:]) is False:
        sys.exit(1)


def run_pack():
    """
    pack package
    """
    packer = Packer()
    if packer.run(sys.argv[2:]) is False:
        sys.exit(1)


def run_dbsync():
    """
    sync local db and local packages directory
    """
    db_sync = DbSync()
    if db_sync.run(sys.argv[2:]) is False:
        sys.exit(1)


def init_log():
    """
    init log
    """
    log_level = LogHandle.log_level(SettingsHandle().log_console_level)
    LogHandle.init_log(filename=None, console_level=log_level)


def main():
    usage_str = "Usage: {} COMMAND [OPTIONS]\n" \
        "\n" \
        "Commands:\n" \
        "  build    build package\n" \
        "  push     upload package\n" \
        "  search   search package\n" \
        "  pull     pull package\n" \
        "  pack     pack package\n" \
        "  dbsync   sync local db and local package dirctory\n" \
        "".format(sys.argv[0])

    if len(sys.argv) < 2:
        print(usage_str)
        sys.exit(1)

    if sys.argv[1] in ("-h", "--help"):
        print(usage_str)
        sys.exit(0)

    if sys.argv[1] in ("-v", "--version"):
        print("hpb {}".format(__version__))
        sys.exit(0)

    # init settings
    try:
        SettingsHandle().init()
    except Exception as e:
        print("{}".format(str(e)))
        sys.exit(1)

    command_dict = {
        "build": run_builder,
        "push": run_push,
        "search": run_search,
        "pull": run_pull,
        "pack": run_pack,
        "dbsync": run_dbsync,
    }

    command = sys.argv[1]
    func = command_dict.get(command, None)
    try:
        if func is not None:
            if command != "build":
                init_log()
            func()
        else:
            print(usage_str)
            sys.exit(1)
    except Exception as e:
        logging.exception("{}".format(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
