import datetime
import getopt
import logging
import json
import os
import selectors
import subprocess
import sys

from constant_var import APP_NAME
from log_handle import LogHandle
from meta_handle import MetaHandle
from yaml_handle import YamlHandle
import __version__


class BuilderConfig:
    def __init__(self):
        self.working_dir = ""
        self.art_search_dir = []
        self.params = []
        self.config_path = ""
        self.task_id = ""
        self.task_name = ""
        self.force_override = True
        self.output_dir = ""


class Builder:
    """
    package builder
    """

    def __init__(self):
        self._usage_str = "Usage: {} build [OPTIONS]\n" \
            "\n" \
            "Commands: \n" \
            "  -c, --config string     [REQUIRED] build config file\n" \
            "    , --task-name string  [OPTIONAL] build task name, if empty, use config file without suffix as task-name\n" \
            "    , --task-id string    [OPTIONAL] build task id, if empty, set 'yyyymmddHHMMSSxxxx' as task-id\n" \
            "    , --work-dir string   [OPTIONAL] working directory(by default, use current working directory)\n" \
            "    , --art-dir list      [OPTIONAL] search artifacts directory(by default, use working_dir/_artifacts\n" \
            "  -p, --params list       [OPTIONAL] build parameters, e.g. --params foo=123 -p bar=456\n" \
            "    , --override bool     [OPTIONAL] if build directory already exists, override or exit\n" \
            "  -o, --output-dir string [OPTIONAL] output directory\n" \
            "".format(APP_NAME)

    def run(self, args):
        """
        run package builder
        """
        if self._init(args=args) is False:
            return False

        yaml_handle = YamlHandle()
        self._fillup_yaml_default_var(yaml_handle)
        for k, v in self._params.items():
            yaml_handle.set_param(k, v)
        yaml_handle.load(self._task_cfg)

        return True

    def _init(self, args):
        """
        init arguments
        """
        cfg = self._parse_args(args)
        if cfg is None:
            return False

        if self._set_args(cfg) is False:
            return False

        # check build dir is already exists and create it
        if os.path.exists(self._build_dir):
            if self._force_override is False:
                print("Error! build dir already exists")
                return False

        os.makedirs(self._build_dir, exist_ok=True)
        os.makedirs(self._output_dir, exist_ok=True)
        LogHandle.init_log(
            os.path.join(self._build_dir, "log", "build.log"),
            console_level=logging.DEBUG,
            file_level=logging.DEBUG,
            use_rotate=False)

        os.chdir(self._working_dir)

        # output arguments
        self._output_args()

        return True

    def _parse_args(self, args):
        """
        parse input arguments
        """
        cfg = BuilderConfig()
        opts, _ = getopt.getopt(
            args, "hc:p:o:",
            [
                "help", "config=", "task-name=", "task-id=",
                "work-dir=", "art-dir=", "params=", "override=",
                "output-dir="
            ]
        )
        artifacts_dir = ""
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                print(self._usage_str)
                sys.exit(0)
            elif opt in ("-c", "--config"):
                cfg.config_path = arg
            elif opt in ("--task-name"):
                cfg.task_name = arg
            elif opt in ("--task-id"):
                cfg.task_id = arg
            elif opt in ("--work-dir"):
                cfg.working_dir = arg
            elif opt in ("--art-dir"):
                artifacts_dir = arg
            elif opt in ("-p", "--params"):
                cfg.params.append(arg)
            elif opt in ("--override"):
                force_override = arg.lower()
                if force_override == "true":
                    cfg.force_override = True
                elif force_override == "false":
                    cfg.force_override = False
                else:
                    print("Error! invalid field 'override' value: {}\n\n{}".format(
                        force_override, self._usage_str))
                    return None
            elif opt in ("-o", "--output-dir"):
                cfg.output_dir = arg

        cfg.config_path = os.path.expanduser(cfg.config_path)
        cfg.working_dir = os.path.expanduser(cfg.working_dir)
        if len(artifacts_dir) > 0:
            art_search_dirs = artifacts_dir.split(" ")
            for i in range(len(art_search_dirs)):
                cfg.art_search_dir[i] = os.path.expanduser(art_search_dirs[i])
        return cfg

    def _set_args(self, cfg: BuilderConfig):
        """
        init config arguments
        """
        # set config filepath
        if len(cfg.config_path) == 0:
            print("Error! field 'config' missing\n\n{}".format(self._usage_str))
            return False
        self._task_cfg = cfg.config_path

        # set task name
        if len(cfg.task_name) == 0:
            cfg_filename = os.path.basename(self._task_cfg).split(".")[0]
            self._task_name = cfg_filename
        else:
            self._task_name = cfg.task_name

        # set task id
        if len(cfg.task_id) == 0:
            now = datetime.datetime.now()
            micro_sec = "{:06}".format(now.strftime("%f"))
            self._task_id = "{}-{}".format(
                now.strftime("%Y%m%d-%H%M%S"), micro_sec)
        else:
            self._task_id = cfg.task_id

        # set working dir
        if len(cfg.working_dir) == 0:
            self._working_dir = os.getcwd()
        else:
            self._working_dir = cfg.working_dir
        if not os.path.isabs(self._working_dir):
            self._working_dir = os.path.abspath(self._working_dir)

        if not os.path.isabs(self._task_cfg):
            self._task_cfg = os.path.join(self._working_dir, self._task_cfg)

        # set search artifacts dir
        default_arts_dir = os.path.join(self._working_dir, "_artifacts")
        default_arts_dir = os.path.abspath(default_arts_dir)
        if len(cfg.art_search_dir) == 0:
            self._artifacts_dir = [
                default_arts_dir
            ]
        else:
            self._artifacts_dir.extend(cfg.art_search_dir)
            self._artifacts_dir.append(default_arts_dir)

        for i in range(len(self._artifacts_dir)):
            art_dir = self._artifacts_dir[i]
            if not os.path.isabs(art_dir):
                self._artifacts_dir[i] = os.path.abspath(art_dir)

        # set params
        self._params = {}
        if len(cfg.params) > 0:
            for param in cfg.params:
                kv = param.split("=")
                if len(kv) != 2:
                    continue
                self._params[kv[0]] = kv[1]

        # set override
        self._force_override = cfg.force_override

        # set output dir
        if len(cfg.output_dir) == 0:
            self._output_dir = default_arts_dir
        else:
            self._output_dir = cfg.output_dir

        # set build dir
        self._build_dir = os.path.join(
            self._working_dir, "build", self._task_name, self._task_id)

        return True

    def _output_args(self):
        """
        output arguments
        """
        logging.debug(
            "\n-------- builder args --------\n"
            "task_cfg={}\n"
            "task_name={}\n"
            "task_id={}\n"
            "working_dir={}\n"
            "artifacts_search_dir={}\n"
            "params={}\n"
            "force_override={}\n"
            "build_dir={}\n"
            "output_dir={}\n"
            "".format(
                self._task_cfg,
                self._task_name,
                self._task_id,
                self._working_dir,
                self._artifacts_dir,
                self._params,
                self._force_override,
                self._build_dir,
                self._output_dir,
            )
        )

    def _fillup_yaml_default_var(self, yml_handle: YamlHandle):
        """
        fillup default variable
        """
        yml_handle.set_param("BP_ROOT_DIR", self._build_dir)
        yml_handle.set_param("BP_OUTPUT_DIR", self._output_dir)
        yml_handle.set_param("BP_TASK_NAME", self._task_name)
        yml_handle.set_param("BP_TASK_ID", self._task_id)



# def parse_args():
#     if len(sys.argv) == 2 and \
#             (sys.argv[1] == "--version" or sys.argv[1] == "-v"):
#         print("{}".format(__version__.__version__))
#         sys.exit(0)
#
#     usage_str = "Usage: {0} -n <name> -t <tag> -o <os>\n" \
#         "    @param name repository name, e.g. googletest, openssl, etc...\n" \
#         "    @param tag  repostiory version tag\n" \
#         "    @param os   OS with version, e.g. ubuntu:22.04, alpine:3.17\n" \
#         "e.g.\n" \
#         "    {0} -n googletest -t v1.13.0 -o ubuntu:22.04\n" \
#         "    {0} -n openssl -t openssl-3.1.0 -o alpine:3.17\n".format(
#             sys.argv[0])
#
#     name = None
#     tag = None
#     os_ver = None
#     res_dir = "./res"
#     opts, _ = getopt.getopt(
#         sys.argv[1:], "hn:o:t:r:", ["help", "name", "tag", "os", "res_dir"])
#     for opt, arg in opts:
#         if opt in ("-h", "--help"):
#             print(usage_str)
#             sys.exit(0)
#         if opt in ("-n", "--name"):
#             name = arg
#         elif opt in ("-t", "--tag"):
#             tag = arg
#         elif opt in ("-o", "--os"):
#             os_ver = arg
#         elif opt in ("-r", "--res_dir"):
#             res_dir = arg
#
#     if name is None or tag is None or os_ver is None:
#         print("Input Arguments Error!!!\n{}".format(usage_str))
#         sys.exit(1)
#
#     return name, tag, os_ver, res_dir
#
#
# def exec_subporcess(p):
#     """
#     exec subporcess
#     :param p: subprocess
#     """
#     sel = selectors.DefaultSelector()
#     sel.register(p.stdout, selectors.EVENT_READ)
#     sel.register(p.stderr, selectors.EVENT_READ)
#     while True:
#         for key, _ in sel.select():
#             data = key.fileobj.read1().decode()
#             if not data:
#                 return
#             if key.fileobj is p.stdout:
#                 print(data, end="")
#             else:
#                 print(data, end="", file=sys.stderr)
#
#
# def exec_command(args):
#     """
#     exec command
#     :param args: command
#     """
#     logging.info("start exec \"{}\"".format(" ".join(args)))
#     p = subprocess.Popen(
#         args=args,
#         stdin=subprocess.PIPE,
#         stdout=subprocess.PIPE,
#         stderr=subprocess.PIPE)
#     try:
#         # p.communicate()
#         exec_subporcess(p)
#     except Exception as e:
#         logging.warning("wait subprocess finish except: {}".format(e))
#         p.terminate()
#         return False
#     logging.info("completed exec \"{}\"".format(" ".join(args)))
#     return True
#
#
# if __name__ == "__main__":
#     # parse input arguments
#     name, tag, os_ver, res_dir = parse_args()
#
#     v = os_ver.split(":")
#     if len(v) != 2:
#         logging.error("invalid os: {}, expect: <os>:<ver> format".format(
#             os_ver))
#         sys.exit(1)
#     use_os = v[0]
#     use_os_ver = v[1]
#
#     # init log
#     LogHandle.init_log(
#         "log/builder.log",
#         console_level=logging.DEBUG,
#         file_level=logging.DEBUG,
#         use_rotate=True)
#
#     logging.info("-----------------------------")
#     logging.info("start build {}-{} in {}".format(name, tag, os_ver))
#     logging.info("try find res in {}".format(res_dir))
#
#     # find meta file
#     meta_dir = os.path.join(res_dir, name)
#     meta_filepath = "{}.json".format(os.path.join(meta_dir, name))
#     if not os.path.exists(meta_filepath):
#         logging.error("failed found meta file: {}".format(meta_filepath))
#         sys.exit(1)
#     else:
#         logging.info("find meta file: {}".format(meta_filepath))
#
#     # load meta file and get yml file path
#     meta_handle = MetaHandle()
#     if meta_handle.load(filepath=meta_filepath) is False:
#         logging.error("failed load meta file, exit")
#         sys.exit(1)
#
#     yml_filepath = meta_handle.get_yml(tag=tag)
#     logging.info("{}-{} use yml: {}".format(
#         name, tag, yml_filepath))
#
#     # # exec docker build
#     # registry = "lpb"
#     # output_tag = "{}/{}:{}-{}{}".format(registry, name, tag, use_os, use_os_ver)
#     # args = [
#     #     "docker", "build",
#     #     "--network=host",
#     #     "--build-arg", "REGISTRY={}".format(registry),
#     #     "--build-arg", "OS={}".format(os_ver),
#     #     "--build-arg", "GIT_REPO={}".format(git_repo),
#     #     "--build-arg", "GIT_TAG={}".format(tag),
#     #     "-f", dockerfile,
#     #     "-t", output_tag,
#     #     meta_dir
#     # ]
#     # ret = exec_command(args=args)
#     # if ret is False:
#     #     logging.error("failed exec \"{}\"".format(" ".join(args)))
#     #     sys.exit(1)
#
#     # # get artifacts
#     # artifacts_dir = "./artifacts"
#     # if not os.path.exists(artifacts_dir):
#     #     os.mkdir(artifacts_dir)
#     # container_name = "{}{}-extract".format(name, tag)
#
#     # args = [
#     #     "docker", "container", "create",
#     #     "--name", container_name,
#     #     output_tag
#     # ]
#     # ret = exec_command(args=args)
#     # if ret is False:
#     #     logging.error("failed exec \"{}\"".format(" ".join(args)))
#     #     sys.exit(1)
#
#     # args = [
#     #     "docker", "container", "cp",
#     #     "{}:/opt/{}/{}-{}.tar.gz".format(container_name, name, name, tag),
#     #     os.path.join(artifacts_dir, "{}-{}-{}.tar.gz".format(name, tag, os_ver))
#     # ]
#     # if not exec_command(args=args):
#     #     logging.error("failed exec \"{}\"".format(" ".join(args)))
#     #     sys.exit(1)
#
#     # args = [
#     #     "docker", "container", "rm",
#     #     container_name
#     # ]
#     # ret = exec_command(args=args)
#     # if ret is False:
#     #     logging.error("failed exec \"{}\"".format(" ".join(args)))
#     #     sys.exit(1)
