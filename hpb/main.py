import sys

from .__version__ import __version__
from .builder import Builder
from .downloader import Downloader
from .packer import Packer
from .searcher import Searcher
from .uploader import Uploader


def run_builde():
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
    pack artifacts
    """
    packer = Packer()
    if packer.run(sys.argv[2:]) is False:
        sys.exit(1)


def main():
    usage_str = "Usage: {} COMMAND [OPTIONS]\n" \
        "\n" \
        "Commands:\n" \
        "  build    build package\n" \
        "  push     upload package\n" \
        "  search   search package\n" \
        "  pull     pull package\n" \
        "  pack     pack artifacts\n" \
        "".format(sys.argv[0])

    if len(sys.argv) < 2:
        print(usage_str)
        sys.exit(1)

    if sys.argv[1] in ("-h", "--help"):
        print(usage_str)
        sys.exit(0)

    if sys.argv[1] in ("-v", "--version"):
        print("{}".format(__version__))
        sys.exit(0)

    command_dict = {
        "build": run_builde,
        "push": run_push,
        "search": run_search,
        "pull": run_pull,
        "pack": run_pack,
    }

    command = sys.argv[1]
    func = command_dict.get(command, None)
    if func is not None:
        func()
    else:
        print(usage_str)
        sys.exit(1)


if __name__ == "__main__":
    main()
