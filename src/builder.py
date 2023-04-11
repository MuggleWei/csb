import datetime
import getopt
import logging
import os
import re
import selectors
import subprocess
import sys

from constant_var import APP_NAME
from kahn_algo import KahnAlgo
from log_handle import LogHandle
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

        # run workflow
        workflow_log_path = os.path.join(self._task_dir, "workflow.log")
        with open(workflow_log_path, "w") as f:
            self._workflow_fp = f
            ret = self.run_workflow(workflow=workflow)

        return ret

    def run_workflow(self, workflow):
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

        # prepare variable replace dict
        if self._prepare_vars(workflow=workflow) is False:
            return False

        # prepare source
        if self._prepare_src(workflow=workflow) is False:
            return False

        # output all variables
        self._output_args()

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
            if self.run_workflow_job(job=job) is False:
                ret = False
                break

        # reset working dir
        os.chdir(self._working_dir)

        return ret

    def run_workflow_job(self, job):
        """
        run workflow job
        :param job: single job
        """
        steps = job.get("steps", [])
        for step in steps:
            step_name = step.get("name", "")
            logging.debug("run step: {}".format(step_name))
            if self.run_workflow_step(step=step) is False:
                return False
        return True

    def run_workflow_step(self, step):
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
            if self.exec_command(command=real_command) is False:
                return False
        return True

    def exec_command(self, command):
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
            self.exec_subporcess(p)
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

    def exec_subporcess(self, p):
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

    def _prepare_vars(self, workflow):
        """
        prepare variables
        :param workflow: workflow
        """
        self._var_replace_dict = {}
        for k, v in self._var_dict.items():
            var_name = "{}_{}".format(APP_NAME.upper(), k)
            self._var_replace_dict[var_name] = v
        for k, v in self._params.items():
            self._var_replace_dict[k] = v

        self._yml_var_dict = {}
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

        self._src_owner = ""
        self._src_repo = ""
        self._src_tag = ""
        self._src_repo_kind = ""
        self._src_repo_url = ""
        self._src_git_depth = 0
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
        self._var_dict["SOURCE_PATH"] = self._source_path
        source_replace_k = "{}_SOURCE_PATH".format(APP_NAME.upper())
        self._var_replace_dict[source_replace_k] = self._source_path

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
            if k == "owner":
                self._src_owner = v
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

    def _check_yml_src_info(self):
        """
        check yaml source info valid
        """
        if len(self._src_owner) == 0:
            logging.debug("Error! field 'source.owner' is empty")
            return False
        if len(self._src_repo) == 0:
            logging.debug("Error! field 'source.repo' is empty")
            return False
        if len(self._src_tag) == 0:
            logging.debug("Error! field 'source.tag' is empty")
            return False
        if len(self._src_repo_kind) == 0:
            logging.debug("Error! field 'source.repo_kind' is empty")
            return False
        if len(self._src_repo_url) == 0:
            logging.debug("Error! field 'source.repo_url' is empty")
            return False
        if self._src_repo_kind == "git" and \
                self._src_git_depth != 0 and self._src_git_depth != 1:
            logging.debug("Error! field 'source.git_depth' invalid")
            return False
        return True

    def _download_src(self):
        """
        download source
        """
        if self._src_repo_kind == "git":
            return self._download_src_git()
        else:
            logging.error(
                "invalid source.repo_kind: {}".format(self._src_repo_kind))
            return False

    def _download_src_git(self):
        """
        download git source
        """
        if len(self._settings_handle.source_path) == 0:
            logging.error("failed find source path in settings")
            return False

        if self._src_git_depth == 1:
            self._source_path = os.path.join(
                self._settings_handle.source_path,
                self._src_owner,
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
            return self.exec_command(command=command)
        else:
            self._source_path = os.path.join(
                self._settings_handle.source_path,
                self._src_owner,
                self._src_repo
            )
            if os.path.exists(self._source_path):
                return self._checkout_src_tag(self._source_path, self._src_tag)
            command = "git clone {} {}".format(
                self._src_repo_url,
                self._source_path
            )
            logging.info("run command: {}".format(command))
            ret = self.exec_command(command=command)
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
        ret = self.exec_command(command=command)
        os.chdir(origin_dir)
        logging.info("restore dir to: {}".format(os.path.abspath(os.curdir)))
        return ret

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

        user_settings = []
        if len(cfg.settings_path) > 0:
            user_settings.append(cfg.settings_path)
        self._settings_handle = SettingsHandle.load_settings(user_settings)

        self._art_search_path = []
        self._art_search_path.extend(self._settings_handle.art_search_path)

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

        os.chdir(self._working_dir)

        # set variables
        if self._set_vars() is False:
            return False

        return True

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
        self._params = {}
        if len(cfg.params) > 0:
            for param in cfg.params:
                kv = param.split("=")
                if len(kv) != 2:
                    continue
                self._params[kv[0]] = kv[1]

        # set task dir
        self._task_dir = os.path.join(
            self._working_dir,
            "_{}".format(APP_NAME),
            "{}.{}".format(self._task_name, self._task_id))

        # set output dir
        if len(cfg.output_dir) == 0:
            self._output_dir = os.path.join(self._task_dir, "output")
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
            "TASK_DIR": self._task_dir,
            "OUTPUT_DIR": self._output_dir,
            "SOURCE_PATH": "",  # NOTE: this value set after load source
            "FILE_DIR": os.path.dirname(self._cfg_file_path),
            "FILE_NAME": os.path.basename(self._cfg_file_path),
            "FILE_PATH": self._cfg_file_path,
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

        s = ""
        for k, v in self._var_dict.items():
            s = s + "{}_{}={}\n".format(APP_NAME.upper(), k, v)
        logging.debug(
            "\n-------- builder inner variables --------\n"
            "{}".format(s)
        )

        s = ""
        for k, v in self._params.items():
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
