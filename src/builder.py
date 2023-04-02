import getopt
import logging
import json
import os
import selectors
import subprocess
import sys

from log_handle import LogHandle
import __version__


def parse_args():
    if len(sys.argv) == 2 and \
            (sys.argv[1] == "--version" or sys.argv[1] == "-v"):
        print("{}".format(__version__.__version__))
        sys.exit(0)

    usage_str = "Usage: {0} -n <name> -t <tag> -o <os>\n" \
        "    @param name repository name, e.g. googletest, openssl, etc...\n" \
        "    @param tag  repostiory version tag\n" \
        "    @param os   OS with version, e.g. ubuntu:22.04, alpine:3.17\n" \
        "e.g.\n" \
        "    {0} -n googletest -t v1.13.0 -o ubuntu:22.04\n" \
        "    {0} -n openssl -t openssl-3.1.0 -o alpine:3.17\n".format(
            sys.argv[0])

    name = None
    tag = None
    os_ver = None
    res_dir = "./res"
    opts, _ = getopt.getopt(
        sys.argv[1:], "hn:o:t:r:", ["help", "name", "tag", "os", "res_dir"])
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(usage_str)
            sys.exit(0)
        if opt in ("-n", "--name"):
            name = arg
        elif opt in ("-t", "--tag"):
            tag = arg
        elif opt in ("-o", "--os"):
            os_ver = arg
        elif opt in ("-r", "--res_dir"):
            res_dir = arg

    if name is None or tag is None or os_ver is None:
        print("Input Arguments Error!!!\n{}".format(usage_str))
        sys.exit(1)

    return name, tag, os_ver, res_dir


def load_metafile(filepath):
    """
    load meta file
    :param filepath: meta file path
    :return: git repository and meta dict
    """
    try:
        logging.info("load meta file: {}".format(filepath))
        with open(meta_filepath, "r") as f:
            meta_obj = json.load(f)
    except Exception as e:
        logging.error("faild load meta file, {}", str(e))
        return None, None

    git_repo = meta_obj.get("git_repo", None)
    if git_repo is None:
        logging.error("failed found 'git_repo' field in meta object")
        return None, None

    metas = meta_obj.get("metas", [])
    if len(metas) == 0:
        logging.error("failed found 'metas' field in meta object")
        return None, None

    meta_dict = {}
    for meta in metas:
        repo_tag = meta.get("tag", None)
        if repo_tag is None:
            logging.warning("skip invalid meta that without 'tag' field")
            continue

        repo_deps = meta.get("deps", None)
        if repo_deps is None:
            repo_deps = []

        repo_dockerfile = meta.get("dockerfile", None)
        if repo_dockerfile is None:
            logging.warning(
                "skip invalid meta(tag={}) "
                "that without 'dockerfile' field".format(repo_tag))
            continue

        if repo_tag in meta_dict:
            logging.warning("repeated tag: {}, ignore".format(repo_tag))
            continue

        logging.debug("load meta: tag={}, dockerfile={}, deps={}".format(
            repo_tag, repo_dockerfile, repo_deps))
        meta_dict[repo_tag] = meta
    return git_repo, meta_dict


def exec_subporcess(p):
    """
    exec subporcess
    :param p: subprocess
    """
    sel = selectors.DefaultSelector()
    sel.register(p.stdout, selectors.EVENT_READ)
    sel.register(p.stderr, selectors.EVENT_READ)
    while True:
        for key, _ in sel.select():
            data = key.fileobj.read1().decode()
            if not data:
                return
            if key.fileobj is p.stdout:
                print(data, end="")
            else:
                print(data, end="", file=sys.stderr)


def exec_command(args):
    """
    exec command
    :param args: command
    """
    logging.info("start exec \"{}\"".format(" ".join(args)))
    p = subprocess.Popen(
        args=args,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    try:
        # p.communicate()
        exec_subporcess(p)
    except Exception as e:
        logging.warning("wait subprocess finish except: {}".format(e))
        p.terminate()
        return False
    logging.info("completed exec \"{}\"".format(" ".join(args)))
    return True


if __name__ == "__main__":
    # parse input arguments
    name, tag, os_ver, res_dir = parse_args()

    v = os_ver.split(":")
    if len(v) != 2:
        logging.error("invalid os: {}, expect: <os>:<ver> format".format(
            os_ver))
        sys.exit(1)
    use_os = v[0]
    use_os_ver = v[1]

    # init log
    LogHandle.init_log(
        "log/builder.log",
        console_level=logging.DEBUG,
        file_level=logging.DEBUG,
        use_rotate=True)

    logging.info("-----------------------------")
    logging.info("start build {}-{} in {}".format(name, tag, os_ver))
    logging.info("try find res in {}".format(res_dir))

    # find meta file
    meta_dir = os.path.join(res_dir, name)
    meta_filepath = "{}.json".format(os.path.join(meta_dir, name))
    if not os.path.exists(meta_filepath):
        logging.error("failed found meta file: {}".format(meta_filepath))
    else:
        logging.info("find meta file: {}".format(meta_filepath))

    # load meta file
    git_repo, meta_dict = load_metafile(filepath=meta_filepath)
    if git_repo is None or meta_dict is None:
        logging.error("failed load meta file, exit")
        sys.exit(1)

    # get dockerfile
    if tag in meta_dict:
        meta = meta_dict[tag]
    elif "default" in meta_dict:
        meta = meta_dict["default"]
    else:
        logging.error("failed found corresponding tag: {}".format(tag))
        sys.exit(1)

    dockerfile = meta["dockerfile"]
    if not os.path.isabs(dockerfile):
        dockerfile = os.path.join(meta_dir, dockerfile)
    dockerfile = os.path.abspath(dockerfile)
    logging.info("{}-{} use dockerfile: {}".format(
        name, tag, dockerfile))

    # exec docker build
    registry = "csb"
    output_tag = "{}/{}:{}-{}{}".format(registry, name, tag, use_os, use_os_ver)
    args = [
        "docker", "build",
        "--network=host",
        "--build-arg", "REGISTRY={}".format(registry),
        "--build-arg", "OS={}".format(os_ver),
        "--build-arg", "GIT_REPO={}".format(git_repo),
        "--build-arg", "GIT_TAG={}".format(tag),
        "-f", dockerfile,
        "-t", output_tag,
        meta_dir
    ]
    ret = exec_command(args=args)
    if ret is False:
        logging.error("failed exec \"{}\"".format(" ".join(args)))
        sys.exit(1)

    # get artifacts
    artifacts_dir = "./artifacts"
    if not os.path.exists(artifacts_dir):
        os.mkdir(artifacts_dir)
    container_name = "{}{}-extract".format(name, tag)

    args = [
        "docker", "container", "create",
        "--name", container_name,
        output_tag
    ]
    ret = exec_command(args=args)
    if ret is False:
        logging.error("failed exec \"{}\"".format(" ".join(args)))
        sys.exit(1)

    args = [
        "docker", "container", "cp",
        "{}:/opt/{}/{}-{}.tar.gz".format(container_name, name, name, tag),
        os.path.join(artifacts_dir, "{}-{}-{}.tar.gz".format(name, tag, os_ver))
    ]
    if not exec_command(args=args):
        logging.error("failed exec \"{}\"".format(" ".join(args)))
        sys.exit(1)

    args = [
        "docker", "container", "rm",
        container_name
    ]
    ret = exec_command(args=args)
    if ret is False:
        logging.error("failed exec \"{}\"".format(" ".join(args)))
        sys.exit(1)
