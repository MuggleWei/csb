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
from yaml_handle import YamlHandle


class BuilderConfig:
    def __init__(self):
        self.working_dir = ""
        self.art_search_dir = []
        self.params = []
        self.config_path = ""
        self.task_id = ""
        self.task_name = ""
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
            "  -p, --param list        [OPTIONAL] build parameters, e.g. --params foo=123 -p bar=456\n" \
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

        # NOTE: Don't replace variable in YamlHandle, replace in builder
        # for k, v in self._var_dict.items():
        #     var_name = "{}_{}".format(APP_NAME.upper(), k)
        #     yaml_handle.set_param(var_name, v)
        # for k, v in self._params.items():
        #     yaml_handle.set_param(k, v)

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
                return False

        # get jobs
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
            logging.debug("run job: {}".format(job_name))
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
            logging.debug("run command: {}".format(command))
            command = self._replace_variable(command)
            if command is None:
                logging.error("failed replace variable in {}".format(command))
                return False
            if self.exec_command(command=command) is False:
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
                elif key.fileobj is p.stderr:
                    self._workflow_fp.write("ERROR|{}\n".format(data))

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
                logging.debug("add variable: {}={}".format(k, v))
                self._yml_var_dict[k] = v
                self._var_replace_dict[k] = v
        return True

    def _replace_variable(self, content):
        """
        replace variable in content
        :param content: content string
        """
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
            os.path.join(self._task_dir, "log", "build.log"),
            console_level=logging.DEBUG,
            file_level=logging.DEBUG,
            use_rotate=False)

        self._load_default_settings()
        self._art_search_path.extend(self._settings_handle.art_search_path)

        os.chdir(self._working_dir)

        if self._set_vars() is False:
            return False

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
                "work-dir=", "art-dir=", "param=", "output-dir="
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
            elif opt in ("-p", "--param"):
                cfg.params.append(arg)
            elif opt in ("-o", "--output-dir"):
                cfg.output_dir = arg

        cfg.config_path = self._expand_path(cfg.config_path)
        cfg.working_dir = self._expand_path(cfg.working_dir)
        for i in range(len(cfg.art_search_dir)):
            cfg.art_search_dir[i] = self._expand_path(cfg.art_search_dir[i])
        cfg.output_dir = self._expand_path(cfg.output_dir)

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
