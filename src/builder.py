import datetime
import distro
import getopt
import logging
import os
import platform
import re
import selectors
import subprocess
import sys

from constant_var import APP_NAME
from kahn_algo import KahnAlgo
from log_handle import LogHandle
from repo_deps_handle import RepoDepsHandle
from settings_handle import SettingsHandle
from utils import Utils
from yaml_handle import YamlHandle


class BuilderConfig:
    def __init__(self):
        self.working_dir = ""
        self.params = []
        self.config_path = ""
        self.task_id = ""
        self.task_name = ""
        self.output_dir = ""
        self.settings_path = ""


class Builder:
    """
    package builder
    """

    def __init__(self):
        self._usage_str = "Usage: {} build [OPTIONS]\n" \
            "\n" \
            "Options: \n" \
            "  -c, --config string     [REQUIRED] build config file\n" \
            "    , --task-name string  [OPTIONAL] build task name, if empty, use config file without suffix as task-name\n" \
            "    , --task-id string    [OPTIONAL] build task id, if empty, set 'yyyymmddHHMMSSxxxx' as task-id\n" \
            "    , --work-dir string   [OPTIONAL] working directory(by default, use current working directory)\n" \
            "  -p, --param list        [OPTIONAL] build parameters, e.g. --params foo=123 -p bar=456\n" \
            "  -o, --output-dir string [OPTIONAL] output directory\n" \
            "  -s, --settings string   [OPTIONAL] manual set settings.xml\n" \
            "".format(APP_NAME)

        self._cfg_file_path = ""  # config file path
        self._task_name = ""  # task name
        self._task_id = ""  # task id
        self._working_dir = ""  # working directory
        self._task_dir = ""  # task directory
        self._build_dir = ""  # build directory
        self._pkg_dir = ""  # package directory
        self._deps_dir = ""  # dependencies directory
        self._test_deps_dir = ""  # test dependencies directory
        self._output_dir = ""  # output directory
        self._input_param_dict = {}  # user input param dict

        self._platform_name = ""
        self._platform_release = ""
        self._platform_ver = ""
        self._platform_machine = ""
        self._platform_distr_id = ""
        self._platform_distr_ver = ""
        self._platform_distr = ""
        self._platform_libc = ""

        self._git_tag = ""  # git tag
        self._git_commit_id = ""  # git commit id
        self._git_branch = ""  # git branch
        self._git_ref = ""  # git ref

        self._settings_handle = SettingsHandle()  # settings handle

        self._var_replace_dict = {}  # vriable replace dict
        self._inner_var_dict = {}  # HPB inner variable dict
        self._yml_var_dict = {}  # yaml variable dict

        # source information
        self._src_maintainer = ""
        self._src_repo = ""
        self._src_tag = ""
        self._src_repo_kind = ""
        self._src_repo_url = ""
        self._src_git_depth = 0
        self._source_path = ""

        # dependencies information
        self._deps = []
        self._test_deps = []

    def run(self, args):
        """
        run package builder
        """
        # init arguments and prepare build/log directory
        if self._init(args=args) is False:
            return False

        logging.info("{} builder run task {}.{}".format(
            APP_NAME, self._task_name, self._task_id))

        # load yaml file and replace param variables
        yaml_handle = YamlHandle()
        workflow = yaml_handle.load(self._cfg_file_path)
        if workflow is None:
            logging.error("failed get workflow")
            return False

        workflow_log_path = os.path.join(self._task_dir, "workflow.log")
        with open(workflow_log_path, "w") as f:
            self._workflow_fp = f

            # prepare variable replace dict
            if self._prepare_vars(workflow=workflow) is False:
                return False

            # prepare source
            if self._prepare_src(workflow=workflow) is False:
                return False

            # prepare deps
            if self._prepare_deps(workflow=workflow) is False:
                return False

            # output all variables
            self._output_args()

            # generate meta files
            self._generate_meta_file()

            # run workflow
            ret = self._run_workflow(workflow=workflow)

        return ret

    def _init(self, args):
        """
        init arguments
        """
        cfg = self._parse_args(args)
        if cfg is None:
            return False

        if self._set_args(cfg) is False:
            return False

        self._load_settings(cfg.settings_path)

        self._prepare_dirs()

        os.chdir(self._working_dir)

        self._init_log()

        if self._set_inner_vars() is False:
            return False

        return True

    def _prepare_vars(self, workflow):
        """
        prepare variables
        :param workflow: workflow
        """
        for k, v in self._inner_var_dict.items():
            var_name = "{}_{}".format(APP_NAME.upper(), k)
            self._var_replace_dict[var_name] = v
        for k, v in self._input_param_dict.items():
            self._var_replace_dict[k] = v

        yaml_vars = workflow.get("variables", None)
        if yaml_vars is not None:
            if self._load_yml_vars(variables=yaml_vars) is False:
                logging.error("failed load yaml variable info")
                return False

        return True

    def _prepare_src(self, workflow):
        """
        prepare source
        :param workflow: workflow
        """
        if len(self._settings_handle.source_path) == 0:
            self._settings_handle.source_path = os.path.join(
                self._working_dir,
                "_{}".format(APP_NAME),
                "sources"
            )
        if not os.path.exists(self._settings_handle.source_path):
            os.makedirs(self._settings_handle.source_path, exist_ok=True)

        yaml_source = workflow.get("source", None)
        if yaml_source is not None:
            logging.info("handle source")
            if self._load_yml_src_info(yaml_source) is False:
                logging.error("failed load yaml source info")
                return False
            if self._check_yml_src_info() is False:
                logging.error("yaml source info is invalid")
                return False
            if self._download_src() is False:
                logging.error("failed download source")
                return False

        # set HPB_SOURCE_PATH
        if len(self._source_path) == 0:
            self._source_path = self._working_dir
        self._inner_var_dict["SOURCE_PATH"] = self._source_path
        source_replace_k = "{}_SOURCE_PATH".format(APP_NAME.upper())
        self._var_replace_dict[source_replace_k] = self._source_path

        # reset git info
        if self._source_path != self._working_dir:
            origin_dir = os.path.abspath(os.curdir)
            os.chdir(self._source_path)
            self._fillup_git_info()
            self._inner_var_dict["GIT_TAG"] = self._git_tag
            self._inner_var_dict["GIT_REF"] = self._git_ref
            self._inner_var_dict["GIT_TAG"] = self._git_tag
            self._inner_var_dict["GIT_COMMIT_ID"] = self._git_commit_id
            self._inner_var_dict["GIT_BRANCH"] = self._git_branch
            os.chdir(origin_dir)

        return True

    def _prepare_deps(self, workflow):
        """
        prepare dependencies
        """
        yaml_deps = workflow.get("deps", None)
        if yaml_deps is None:
            return True

        repo_deps_handle = RepoDepsHandle()
        repo_deps_handle.settings_handle = self._settings_handle
        repo_deps_handle.platform_name = self._platform_name
        repo_deps_handle.platform_machine = self._platform_machine
        repo_deps_handle.platform_distr = self._platform_distr
        repo_deps_handle.platform_libc = self._platform_libc
        repo_deps_handle.build_type = self._get_build_type()
        for dep in yaml_deps:
            if repo_deps_handle.add(dep) is False:
                return False

        if repo_deps_handle.search_all_deps() is False:
            logging.error("failed search dependencies")
            return False

        self._deps = repo_deps_handle.deps

        if repo_deps_handle.download_all_deps(self._deps_dir) is False:
            logging.error("failed download dependencies")
            return False

    def _run_workflow(self, workflow):
        """
        run workflow
        :param workflow: like github actions workflow, the workflow is
            - workflow include some jobs
            - every jobs include some steps
            - every steps include some action
            - action is command
        """
        # set current working dir
        os.chdir(self._working_dir)

        # run jobs
        jobs = workflow.get("jobs", None)
        if jobs is None:
            logging.debug("workflow without jobs")
            return True

        job_order = self._sort_jobs(jobs)
        if job_order is None:
            logging.error("failed order job")
            return False
        logging.debug("workflow job order: {}".format(", ".join(job_order)))

        ret = True
        for job_name in job_order:
            logging.info("run job: {}".format(job_name))
            job = jobs[job_name]
            if self._run_workflow_job(job=job) is False:
                ret = False
                break

        # reset working dir
        os.chdir(self._working_dir)

        return ret

    def _parse_args(self, args):
        """
        parse input arguments
        """
        cfg = BuilderConfig()
        opts, _ = getopt.getopt(
            args, "hc:p:o:s:",
            [
                "help", "config=", "task-name=", "task-id=",
                "work-dir=", "param=", "output-dir=", "settings="
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
            elif opt in ("-p", "--param"):
                cfg.params.append(arg)
            elif opt in ("-o", "--output-dir"):
                cfg.output_dir = arg
            elif opt in ("-s", "--settings"):
                cfg.settings_path = arg

        cfg.config_path = Utils.expand_path(cfg.config_path)
        cfg.working_dir = Utils.expand_path(cfg.working_dir)
        cfg.output_dir = Utils.expand_path(cfg.output_dir)

        return cfg

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
                self._settings_handle.pkg_search_repos,
                self._input_param_dict,
                self._output_dir,
            )
        )

        s = ""
        for k, v in self._inner_var_dict.items():
            s = s + "{}_{}={}\n".format(APP_NAME.upper(), k, v)
        logging.debug(
            "\n-------- builder inner variables --------\n"
            "{}".format(s)
        )

        s = ""
        for k, v in self._input_param_dict.items():
            s = s + "{}={}\n".format(k, v)
        logging.debug(
            "\n-------- builder user input variables --------\n"
            "{}".format(s)
        )

        s = ""
        for k, v in self._yml_var_dict.items():
            s = s + "{}={}\n".format(k, v)
        logging.debug(
            "\n-------- builder user yaml variables --------\n"
            "{}".format(s)
        )

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

        # set params
        if len(cfg.params) > 0:
            for param in cfg.params:
                kv = param.split("=")
                if len(kv) != 2:
                    continue
                self._input_param_dict[kv[0]] = kv[1]

        # set task dirs
        self._task_dir = os.path.join(
            self._working_dir,
            "_{}".format(APP_NAME),
            "{}.{}".format(self._task_name, self._task_id))
        self._build_dir = os.path.join(self._task_dir, "build")
        self._pkg_dir = os.path.join(self._task_dir, "pkg")
        self._deps_dir = os.path.join(self._task_dir, "deps")
        self._test_deps_dir = os.path.join(self._task_dir, "test_deps")

        # set output dir
        if len(cfg.output_dir) == 0:
            self._output_dir = os.path.join(self._task_dir, "output")
        else:
            self._output_dir = cfg.output_dir

        return True

    def _load_settings(self, input_settings_path: str):
        """
        load settings
        :param input_settings_path: user input settings path
        """
        user_settings = []
        if len(input_settings_path) > 0:
            user_settings.append(input_settings_path)
        self._settings_handle = SettingsHandle.load_settings(user_settings)

    def _prepare_dirs(self):
        """
        prepare directories
        """
        os.makedirs(self._task_dir, exist_ok=True)
        os.makedirs(self._build_dir, exist_ok=True)
        os.makedirs(self._pkg_dir, exist_ok=True)
        os.makedirs(self._output_dir, exist_ok=True)
        os.makedirs(self._deps_dir, exist_ok=True)
        os.makedirs(self._test_deps_dir, exist_ok=True)

    def _init_log(self):
        """
        init log
        """
        console_log_level = LogHandle.log_level(
            self._settings_handle.log_console_level
        )
        file_log_level = LogHandle.log_level(
            self._settings_handle.log_file_level
        )
        LogHandle.init_log(
            os.path.join(self._task_dir, "log", "build.log"),
            console_level=console_log_level,
            file_level=file_log_level,
            use_rotate=False)

        self._command_logger = logging.getLogger("command")
        self._command_logger.propagate = False
        self._command_logger.setLevel(logging.INFO)
        self._command_logger.addHandler(logging.StreamHandler())

    def _set_inner_vars(self):
        """
        set varaibles
        """
        self._fillup_platform_info()

        self._fillup_git_info()

        self._inner_var_dict = {
            "ROOT_DIR": self._working_dir,
            "TASK_DIR": self._task_dir,
            "BUILD_DIR": self._build_dir,
            "PKG_DIR": self._pkg_dir,
            "DEPS_DIR": self._deps_dir,
            "TEST_DEPS_DIR": self._test_deps_dir,
            "OUTPUT_DIR": self._output_dir,
            "SOURCE_PATH": "",  # NOTE: this value set after load source
            "FILE_DIR": os.path.dirname(self._cfg_file_path),
            "FILE_NAME": os.path.basename(self._cfg_file_path),
            "FILE_PATH": self._cfg_file_path,
            "TASK_NAME": self._task_name,
            "TASK_ID": self._task_id,
            "PLATFORM_NAME": self._platform_name,
            "PLATFORM_RELEASE": self._platform_release,
            "PLATFORM_VERSION": self._platform_ver,
            "PLATFORM_MACHINE": self._platform_machine,
            "PLATFORM_DISTR_ID": self._platform_distr_id,
            "PLATFORM_DISTR_VER": self._platform_distr_ver,
            "PLATFORM_DISTR": self._platform_distr,
            "GIT_REF": self._git_ref,
            "GIT_TAG": self._git_tag,
            "GIT_COMMIT_ID": self._git_commit_id,
            "GIT_BRANCH": self._git_branch,
        }

        return True

    def _fillup_platform_info(self):
        """
        fillup platform informations
        """
        logging.debug("system: {}".format(platform.system()))
        logging.debug("system release: {}".format(platform.release()))
        logging.debug("system version: {}".format(platform.version()))
        logging.debug("system architecture: {}".format(platform.architecture()))
        logging.debug("system infos: {}".format(platform.platform()))
        logging.debug("machine: {}".format(platform.machine()))
        logging.debug("node: {}".format(platform.node()))
        logging.debug("processor: {}".format(platform.processor()))
        logging.debug("uname: {}".format(platform.uname()))

        self._platform_name = platform.system().lower()
        self._platform_release = platform.release()
        self._platform_ver = platform.version()
        self._platform_machine = platform.machine()

        if self._platform_name == "linux":
            logging.debug("linux distro id: {}".format(distro.id()))
            logging.debug("linux distro version: {}".format(distro.version()))
            self._platform_distr_id = distro.id()
            self._platform_distr_ver = distro.version()
            if len(self._platform_distr_ver) > 0:
                self._platform_distr = "{}_{}".format(
                    self._platform_distr_id, self._platform_distr_ver)
            else:
                self._platform_distr = self._platform_distr_id

            libc_ver = platform.libc_ver()
            logging.debug("libc: {}".format(libc_ver))
            self._platform_libc = "-".join(libc_ver)
        else:
            self._platform_distr_id = ""
            self._platform_distr_ver = ""
            self._platform_distr = platform.version()
            self._platform_libc = ""

    def _fillup_git_info(self):
        """
        fillup git informations
        """
        self._git_tag = self._get_git_tag()
        self._git_commit_id = self._get_git_commit_id()
        self._git_branch = self._get_git_branch()
        if len(self._git_tag) > 0:
            self._git_ref = self._git_tag
        elif len(self._git_commit_id) > 0:
            self._git_ref = self._git_commit_id
        else:
            self._git_ref = ""

    def _load_yml_vars(self, variables):
        """
        load arguments in yml args
        """
        for variable in variables:
            logging.debug("load variables in yml: {}".format(variable))
            for k, v in variable.items():
                v = self._replace_variable(v)
                if v is None:
                    logging.error("failed load variable: {}".format(variable))
                    return False
                if k in self._var_replace_dict:
                    logging.debug(
                        "{} already in var replace dict, ignore".format(k))
                    continue
                logging.debug("add variable: {}={}".format(k, v))
                self._yml_var_dict[k] = v
                self._var_replace_dict[k] = v
        return True

    def _load_yml_src_info(self, yml_src):
        """
        load source information
        """
        for k, v in yml_src.items():
            logging.debug("load source info in yml: {}={}".format(k, v))
            v = self._replace_variable(v)
            if v is None:
                logging.error("failed load source info: {}".format(k))
                return False
            if k == "maintainer":
                self._src_maintainer = v
            elif k == "repo":
                self._src_repo = v
            elif k == "tag":
                self._src_tag = v
            elif k == "repo_kind":
                self._src_repo_kind = v
            elif k == "repo_url":
                self._src_repo_url = v
            elif k == "git_depth":
                self._src_git_depth = int(v)
            logging.debug("add source info: source.{}={}".format(k, v))
        return True

    def _replace_variable(self, content):
        """
        replace variable in content
        :param content: content string
        """
        content = str(content)
        finds = re.findall(r'\${\w+}', content)
        finds_set = set(finds)
        if len(finds_set) == 0:
            return content
        for var in finds_set:
            var_name = var[2:-1]
            if var_name not in self._var_replace_dict:
                logging.error("failed find variable value: {}".format(var_name))
                return None
            logging.debug("replace {} -> {}".format(
                var, self._var_replace_dict[var_name]))
            content = content.replace(var, self._var_replace_dict[var_name])
        return content

    def _check_yml_src_info(self):
        """
        check yaml source info valid
        """
        if len(self._src_maintainer) == 0:
            logging.debug("field 'source.maintainer' is empty")
        if len(self._src_repo) == 0:
            logging.debug("field 'source.repo' is empty")
        if len(self._src_tag) == 0:
            logging.debug("field 'source.tag' is empty")
        if len(self._src_repo_kind) == 0:
            logging.debug("field 'source.repo_kind' is empty")
        if len(self._src_repo_url) == 0:
            logging.debug("field 'source.repo_url' is empty")
        if self._src_repo_kind == "git" and \
                self._src_git_depth != 0 and self._src_git_depth != 1:
            logging.debug("field 'source.git_depth' invalid")
        return True

    def _download_src(self):
        """
        download source
        """
        if self._src_repo_kind == "":
            logging.info("source.repo_kind is empty, no need download")
        elif self._src_repo_kind == "git":
            return self._download_src_git()
        else:
            logging.error(
                "invalid source.repo_kind: {}".format(self._src_repo_kind))
            return False
        return True

    def _generate_meta_file(self):
        """
        generate dependencies file
        """
        self._generate_hpd_meta_file()
        self._generate_pkg_meta_file()

    def _generate_hpd_meta_file(self):
        """
        generate hpd meta dependencies file
        """
        d = {
            "maintainer": self._src_maintainer,
            "repo": self._src_repo,
            "url": self._src_repo_url,
            "tag": self._get_source_tag(),
            "platform": {
                "system": self._platform_name,
                "version": self._platform_ver,
                "release": self._platform_release,
                "machine": self._platform_machine,
                "distr_id": self._platform_distr_id,
                "distr_ver": self._platform_distr_ver,
                "distr": self._platform_distr,
                "libc": self._platform_libc,
            },
            "deps": self._deps,
            "build_type": self._get_build_type(),
        }
        filepath = os.path.join(self._task_dir, "{}.yml".format(APP_NAME))
        yaml_handle = YamlHandle()
        yaml_handle.write(filepath=filepath, obj=d)

    def _generate_pkg_meta_file(self):
        """
        generate hpd meta pkg file
        """
        d = {
            "meta_file": os.path.join(
                self._task_dir, "{}.yml".format(APP_NAME)),
            "output_dir": self._inner_var_dict["OUTPUT_DIR"],
            "pkg_dir": self._inner_var_dict["PKG_DIR"],
        }
        filepath = os.path.join(self._task_dir, "pkg.yml")
        yaml_handle = YamlHandle()
        yaml_handle.write(filepath=filepath, obj=d)

    def _get_build_type(self):
        """
        get build type
        """
        build_type = ""
        try_words = [
            "build-type",
            "build_type",
            "BUILD_TYPE",
            "BUILDTYPE",
        ]
        for word in try_words:
            if word not in self._var_replace_dict:
                continue
            build_type = self._var_replace_dict[word]
            break
        return build_type

    def _get_source_tag(self):
        """
        get source tag
        """
        src_tag = ""
        if self._src_repo_kind == "":
            if self._git_tag != "":
                src_tag = self._git_tag
            else:
                src_tag = self._git_commit_id
        else:
            src_tag = self._src_tag
        return src_tag

    def _run_workflow_job(self, job):
        """
        run workflow job
        :param job: single job
        """
        steps = job.get("steps", [])
        for i in range(len(steps)):
            step = steps[i]
            step_name = step.get("name", "")
            logging.debug("run step[{}]: {}".format(i, step_name))
            if self._run_workflow_step(step=step) is False:
                return False
        return True

    def _run_workflow_step(self, step):
        """
        run workflow step
        """
        command_str = step.get("run", "")
        if len(command_str) == 0:
            return True
        pattern = re.compile(r'''((?:[^;"']|"[^"]*"|'[^']*')+)''')
        commands = pattern.split(command_str)
        for command in commands:
            command = command.strip()
            if len(command) == 0:
                continue
            if command == ";":
                continue
            logging.info("run command: {}".format(command))
            real_command = self._replace_variable(command)
            if real_command is None:
                logging.error("failed replace variable in: {}".format(command))
                return False
            if self._exec_command(command=real_command) is False:
                return False
        return True

    def _exec_command(self, command):
        """
        exec command
        :param command: exec command
        """
        logging.debug("exec command: {}".format(command))
        self._workflow_fp.write("COMMAND|{}\n".format(command))

        pos = command.find("cd ")
        if pos != -1:
            chpath = command[pos+2:].strip()
            chpath = chpath.strip("\"")
            if not os.path.isabs(chpath):
                chpath = os.path.join(os.getcwd(), chpath)
            os.chdir(chpath)
            return True

        p = subprocess.Popen(
            command, shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        try:
            self._exec_subporcess(p)
            p.communicate()
            if p.returncode is not None and p.returncode != 0:
                logging.error("failed exec: {}, ret code: {}".format(
                    command, p.returncode))
                return False
        except Exception as e:
            logging.warning("wait subprocess finish except: {}".format(e))
            p.terminate()
            return False
        return True

    def _exec_subporcess(self, p):
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
                data = data.strip()
                if key.fileobj is p.stdout:
                    self._workflow_fp.write("INFO|{}\n".format(data))
                    self._command_logger.info("{}".format(data))
                elif key.fileobj is p.stderr:
                    self._workflow_fp.write("ERROR|{}\n".format(data))
                    self._command_logger.error("{}".format(data))
                self._workflow_fp.flush()

    def _download_src_git(self):
        """
        download git source
        """
        if len(self._settings_handle.source_path) == 0:
            logging.error("failed find source path in settings")
            return False

        if self._src_maintainer == "":
            logging.error(
                "failed download source, field 'source.maintainer' is empty")
            return False

        if self._src_repo == "":
            logging.error(
                "failed download source, field 'source.repo' is empty")
            return False

        if self._src_repo_url == "":
            logging.error(
                "failed download source, field 'source.repo_url' is empty")
            return False

        if self._src_git_depth == 1:
            if self._src_tag == "":
                logging.error(
                    "failed download source, "
                    "use git depth=1 with field 'source.tag' is empty")
                return False
            self._source_path = os.path.join(
                self._settings_handle.source_path,
                self._src_maintainer,
                "{}-{}".format(self._src_repo, self._src_tag)
            )
            if os.path.exists(self._source_path):
                logging.info("{} already exists, skip download".format(
                    self._source_path))
                return True
            command = "git clone --branch={} --depth={} {} {}".format(
                self._src_tag,
                self._src_git_depth,
                self._src_repo_url,
                self._source_path
            )
            logging.info("run command: {}".format(command))
            return self._exec_command(command=command)
        else:
            self._source_path = os.path.join(
                self._settings_handle.source_path,
                self._src_maintainer,
                self._src_repo
            )
            if os.path.exists(self._source_path):
                return self._checkout_src_tag(self._source_path, self._src_tag)
            command = "git clone {} {}".format(
                self._src_repo_url,
                self._source_path
            )
            logging.info("run command: {}".format(command))
            ret = self._exec_command(command=command)
            if ret is False:
                return ret
            return self._checkout_src_tag(self._source_path, self._src_tag)

    def _checkout_src_tag(self, src_path, tag):
        """
        checkout git source tag
        """
        origin_dir = os.path.abspath(os.curdir)
        os.chdir(src_path)
        logging.info("change dir to: {}".format(os.path.abspath(os.curdir)))
        command = "git checkout {}".format(tag)
        logging.info("run command: {}".format(command))
        ret = self._exec_command(command=command)
        os.chdir(origin_dir)
        logging.info("restore dir to: {}".format(os.path.abspath(os.curdir)))
        return ret

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
