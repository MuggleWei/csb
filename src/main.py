import sys
import __version__

from builder import Builder
from searcher import Searcher
from uploader import Uploader


if __name__ == "__main__":
    usage_str = "Usage: {} COMMAND [OPTIONS]\n" \
        "\n" \
        "Commands:\n" \
        "  build    build package\n" \
        "  push     upload package\n" \
        "  search   search package\n" \
        "".format(sys.argv[0])

    if len(sys.argv) < 2:
        print(usage_str)
        sys.exit(1)

    if sys.argv[1] in ("-h", "--help"):
        print(usage_str)
        sys.exit(0)

    if sys.argv[1] in ("-v", "--version"):
        print("{}".format(__version__.__version__))
        sys.exit(0)

    command = sys.argv[1]
    if command == "build":
        builder = Builder()
        if builder.run(sys.argv[2:]) is False:
            sys.exit(1)
    elif command == "push":
        uploader = Uploader()
        if uploader.run(sys.argv[2:]) is False:
            sys.exit(1)
    elif command == "search":
        searcher = Searcher()
        if searcher.run(sys.argv[2:]) is False:
            sys.exit(1)
    else:
        print(usage_str)
        sys.exit(1)
