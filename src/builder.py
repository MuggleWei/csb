import datetime
import getopt
import logging
import os
import subprocess
import sys

from constant_var import APP_NAME
from kahn_algo import KahnAlgo
from log_handle import LogHandle
from settings_handle import SettingsHandle
from yaml_handle import YamlHandle


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
            "    , --art-dir list      [OPTIONAL] artifacts search directory, e.g. --art-dir=file://~/.local/\n" \
            "  -p, --params list       [OPTIONAL] build parameters, e.g. --params foo=123 -p bar=456\n" \
            "    , --override bool     [OPTIONAL] if build directory already exists, override or exit\n" \
            "  -o, --output-dir string [OPTIONAL] output directory\n" \
            "".format(APP_NAME)

    def run(self, args):
        """
        run package builder
        """
        # init arguments and prepare build/log directory
        if self._init(args=args) is False:
            return False

        # load yaml file and replace param variables
        yaml_handle = YamlHandle()
        for k, v in self._var_dict.items():
            var_name = "{}_{}".format(APP_NAME.upper(), k)
            yaml_handle.set_param(var_name, v)
        for k, v in self._params.items():
            yaml_handle.set_param(k, v)
        workflow = yaml_handle.load(self._cfg_file_path)
        if workflow is None:
            logging.error("failed get workflow")
            return False

        # run workflow
        self.run_workflow(workflow=workflow)

        return True

    def run_workflow(self, workflow):
        """
        run workflow
        :param workflow: like github actions workflow, the workflow is
            - workflow include some jobs
            - every jobs include some steps
            - every steps include some action
            - action is command
        """
        jobs = workflow.get("jobs", None)
        if jobs is None:
            logging.debug("workflow without jobs")
            return True

        job_order = self._sort_jobs(jobs)
        if job_order is None:
            logging.error("failed order job")
            return False
        logging.debug("workflow job order: {}".format(", ".join(job_order)))
        # TODO:

    def _sort_jobs(self, jobs):
        """
        sort jobs
        :param jobs: workflow jobs
        """
        job_name_list = []
        job_idx_dict = {}
        idx = 0
        for job_name in jobs.keys():
            job_idx_dict[job_name] = idx
            idx += 1
            job_name_list.append(job_name)

        edges = []
        for job_name, job in jobs.items():
            dep_job_names = job.get("needs", [])
            for dep_name in dep_job_names:
                from_idx = job_idx_dict[dep_name]
                to_idx = job_idx_dict[job_name]
                edges.append([from_idx, to_idx])

        dep_result = KahnAlgo().sort(len(jobs), edges)
        if dep_result is None:
            logging.error("Cycle dependence in jobs!!!")
            return None

        result = []
        for idx in dep_result:
            result.append(job_name_list[idx])

        return result

    def _load_default_settings(self):
        """
        load settings
        """
        self._settings_handle = SettingsHandle()
        settings_path = [
            os.path.expanduser("~/.{}/settings.xml".format(APP_NAME)),
            os.path.expanduser(
                "~/.local/share/{}/settings.xml".format(APP_NAME)),
            "/etc/{}/settings.xml".format(APP_NAME),
        ]
        for filepath in settings_path:
            if os.path.exists(filepath):
                logging.debug("load default settings: {}".format(filepath))
                self._settings_handle.load(filepath=filepath)

    def _init(self, args):
        """
        init arguments
        """
        cfg = self._parse_args(args)
        if cfg is None:
            return False

        if self._set_args(cfg) is False:
            return False

        os.makedirs(self._output_dir, exist_ok=True)
        LogHandle.init_log(
            os.path.join(
                self._working_dir,
                "_{}".format(APP_NAME),
                "{}.{}".format(self._task_name, self._task_id),
                "log",
                "build.log"),
            console_level=logging.DEBUG,
            file_level=logging.DEBUG,
            use_rotate=False)

        self._load_default_settings()
        self._art_search_path.extend(self._settings_handle.art_search_path)

        if self._set_vars() is False:
            return False

        self._output_args()

        os.chdir(self._working_dir)

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
                "work-dir=", "art-dir=", "params=", "output-dir="
            ]
        )
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
                cfg.art_search_dir.append(arg)
            elif opt in ("-p", "--params"):
                cfg.params.append(arg)
            elif opt in ("-o", "--output-dir"):
                cfg.output_dir = arg

        cfg.config_path = self._expand_path(cfg.config_path)
        cfg.working_dir = self._expand_path(cfg.working_dir)
        for i in range(len(cfg.art_search_dir)):
            cfg.art_search_dir[i] = self._expand_path(cfg.art_search_dir[i])

        return cfg

    def _expand_path(self, filepath):
        ret_filepath = filepath
        if len(filepath) > 0:
            ret_filepath = os.path.expanduser(ret_filepath)
            ret_filepath = os.path.expandvars(ret_filepath)
            ret_filepath = os.path.abspath(ret_filepath)
        return ret_filepath

    def _set_args(self, cfg: BuilderConfig):
        """
        init config arguments
        """
        # set config filepath
        if len(cfg.config_path) == 0:
            print("Error! field 'config' missing\n\n{}".format(self._usage_str))
            return False
        self._cfg_file_path = cfg.config_path

        # set task name
        if len(cfg.task_name) == 0:
            cfg_filename = os.path.basename(self._cfg_file_path).split(".")[0]
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
            self._working_dir = os.path.abspath(os.getcwd())
        else:
            self._working_dir = cfg.working_dir

        # set task_cfg abs
        if not os.path.isabs(self._cfg_file_path):
            self._cfg_file_path = os.path.join(
                self._working_dir, self._cfg_file_path)

        # set search artifacts dir
        self._art_search_path = []
        self._art_search_path.extend(cfg.art_search_dir)

        # set params
        self._params = {}
        if len(cfg.params) > 0:
            for param in cfg.params:
                kv = param.split("=")
                if len(kv) != 2:
                    continue
                self._params[kv[0]] = kv[1]

        # set output dir
        if len(cfg.output_dir) == 0:
            self._output_dir = os.path.join(
                self._working_dir,
                "_{}".format(APP_NAME),
                "{}.{}".format(self._task_name, self._task_id),
                "output")
        else:
            self._output_dir = cfg.output_dir

        return True

    def _set_vars(self):
        """
        set varaibles
        """
        val_git_tag = self._get_git_tag()
        val_git_commit_id = self._get_git_commit_id()
        val_git_branch = self._get_git_branch()
        if len(val_git_tag) > 0:
            val_git_ref = val_git_tag
        elif len(val_git_commit_id) > 0:
            val_git_ref = val_git_commit_id
        else:
            val_git_ref = ""

        self._var_dict = {
            "ROOT_DIR": self._working_dir,
            "OUTPUT_DIR": self._output_dir,
            "FILE_DIR": os.path.dirname(self._cfg_file_path),
            "TASK_NAME": self._task_name,
            "TASK_ID": self._task_id,
            "GIT_REF": val_git_ref,
            "GIT_TAG": val_git_tag,
            "GIT_COMMIT_ID": val_git_commit_id,
            "GIT_BRANCH": val_git_branch,
        }

        return True

    def _get_git_tag(self):
        """
        get git tag
        """
        v = ""
        try:
            result = subprocess.run(
                "git describe --tags --exact-match 2> /dev/null",
                shell=True,
                stdout=subprocess.PIPE)
            v = result.stdout.decode("utf-8").strip()
        except Exception as e:
            logging.debug("failed get git tag: {}".format(str(e)))
        return v

    def _get_git_commit_id(self):
        """
        get git commit id
        """
        v = ""
        try:
            result = subprocess.run(
                "git rev-parse --short HEAD",
                shell=True,
                stdout=subprocess.PIPE)
            v = result.stdout.decode("utf-8").strip()
        except Exception as e:
            logging.debug("failed get git commit id: {}".format(str(e)))
        return v

    def _get_git_branch(self):
        """
        get git branch
        """
        v = ""
        try:
            result = subprocess.run(
                "git symbolic-ref -q --short HEAD",
                shell=True,
                stdout=subprocess.PIPE)
            v = result.stdout.decode("utf-8").strip()
        except Exception as e:
            logging.debug("failed get git branch: {}".format(str(e)))
        return v

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
            "output_dir={}\n"
            "".format(
                self._cfg_file_path,
                self._task_name,
                self._task_id,
                self._working_dir,
                self._art_search_path,
                self._params,
                self._output_dir,
            )
        )

        vars = ""
        for k, v in self._var_dict.items():
            vars = vars + "{}_{}={}\n".format(APP_NAME.upper(), k, v)

        logging.debug(
            "\n-------- builder variables --------\n"
            "{}".format(vars)
        )

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
