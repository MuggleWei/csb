import datetime
import logging
import os
import re
import typing

from hpb.builder_config import BuilderConfig
from hpb.command_handle import CommandHandle
from hpb.constant_var import APP_NAME
from hpb.git_info import GitInfo
from hpb.kahn_algo import KahnAlgo
from hpb.log_handle import LogHandle
from hpb.platform_info import PlatformInfo
from hpb.repo_deps_handle import RepoDepsHandle
from hpb.settings_handle import SettingsHandle
from hpb.source_downloader import SourceDownloader
from hpb.source_info import SourceInfo
from hpb.var_replace_handle import VarReplaceHandle
from hpb.workflow_yml import WorkflowYaml
from hpb.yaml_handle import YamlHandle


class WorkflowHandle:
    """
    workflow handle
    """

    def __init__(self):
        # input arguments
        self.working_dir = ""  # working directory
        self.cfg_file_path = ""  # config file path
        self.task_name = ""  # task name
        self.task_id = ""  # task id
        self.input_param_dict = {}  # user input param dict

        # directories
        self.task_dir = ""  # task directory
        self.build_dir = ""  # build directory
        self.pkg_dir = ""  # package directory
        self.deps_dir = ""  # dependencies directory
        self.test_deps_dir = ""  # test dependencies directory
        self.output_dir = ""  # output directory

        # settings handle
        self.settings_handle = SettingsHandle()

        # workflow object
        self.yml_obj = WorkflowYaml()

        # command handle
        self.command_handle = CommandHandle()

        self.platform_info = PlatformInfo()
        self.git_info = GitInfo()

        # variables
        self.inner_var_dict = {}
        self.yml_vars = []
        self.all_var_dict = {}  # input_param_dict + inner_var_dict + yml_vars

        # source
        self.src = SourceInfo()

        # deps
        self.deps = []
        self.test_deps = []

    def set_input_args(self, cfg: BuilderConfig):
        """
        set input arguments and variables which derived from input arguments
        :param cfg: builder input arguments
        """
        # set working dir
        if len(cfg.working_dir) == 0:
            self.working_dir = os.path.abspath(os.getcwd())
        else:
            self.working_dir = cfg.working_dir

        # set config filepath
        if len(cfg.config_path) == 0:
            print("Error! field 'config' missing\n")
            return False
        self.cfg_file_path = cfg.config_path
        if not os.path.isabs(self.cfg_file_path):
            self.cfg_file_path = os.path.join(
                self.working_dir, self.cfg_file_path)

        # set task name
        if len(cfg.task_name) == 0:
            cfg_filename = os.path.basename(self.cfg_file_path).split(".")[0]
            self.task_name = cfg_filename
        else:
            self.task_name = cfg.task_name

        # set task id
        if len(cfg.task_id) == 0:
            now = datetime.datetime.now()
            micro_sec = "{:06}".format(int(now.strftime("%f")))
            self.task_id = "{}-{}".format(
                now.strftime("%Y%m%d-%H%M%S"), micro_sec)
        else:
            self.task_id = cfg.task_id

        # set params
        if len(cfg.params) > 0:
            for param in cfg.params:
                kv = param.split("=")
                if len(kv) != 2:
                    continue
                self.input_param_dict[kv[0]] = kv[1]

        # set directories
        self.task_dir = os.path.join(
            self.working_dir,
            "_{}".format(APP_NAME),
            "{}.{}".format(self.task_name, self.task_id))
        self.build_dir = os.path.join(self.task_dir, "build")
        self.pkg_dir = os.path.join(self.task_dir, "pkg")
        self.deps_dir = os.path.join(self.task_dir, "deps")
        self.test_deps_dir = os.path.join(self.task_dir, "test_deps")

        if len(cfg.output_dir) == 0:
            self.output_dir = os.path.join(self.task_dir, "output")
        else:
            self.output_dir = cfg.output_dir

        return True

    def load_settings(self, input_settings_path: str):
        """
        load settings
        :param input_settings_path: user input settings path
        """
        user_settings = []
        if len(input_settings_path) > 0:
            user_settings.append(input_settings_path)
        self.settings_handle = SettingsHandle.load_settings(user_settings)

    def load_yaml_file(self):
        """
        load config file
        """
        yaml_handle = YamlHandle()
        obj = yaml_handle.load(filepath=self.cfg_file_path)
        if obj is None:
            logging.error("failed get workflow")
            return False
        return self.yml_obj.load(obj)

    def init_log(self):
        """
        init log
        """
        console_log_level = LogHandle.log_level(
            self.settings_handle.log_console_level
        )
        file_log_level = LogHandle.log_level(
            self.settings_handle.log_file_level
        )
        LogHandle.init_log(
            os.path.join(self.task_dir, "log", "build.log"),
            console_level=console_log_level,
            file_level=file_log_level,
            use_rotate=False)

        command_logger = logging.getLogger("command")
        command_logger.propagate = False
        command_logger.setLevel(logging.INFO)
        command_logger.addHandler(logging.StreamHandler())

    def run(self):
        """
        run workflow
        """
        # create directories
        self.mk_dirs()

        # chdir to working directory
        os.chdir(self.working_dir)

        workflow_log_path = os.path.join(self.task_dir, "workflow.log")
        with open(workflow_log_path, "w") as f:
            self.command_handle.set_fp(f)

            if self.prepare() is False:
                return False

            self.generate_meta_file()

            self.run_workflow()

        return True

    def mk_dirs(self):
        """
        prepare directories
        """
        os.makedirs(self.task_dir, exist_ok=True)
        os.makedirs(self.build_dir, exist_ok=True)
        os.makedirs(self.pkg_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.deps_dir, exist_ok=True)
        os.makedirs(self.test_deps_dir, exist_ok=True)

    def prepare(self):
        """
        run prepare steps
        """
        # load yaml file
        if self.load_yaml_file() is False:
            return False

        if self.prepare_vars_and_src() is False:
            return False

        self.output_vars()

        if self.prepare_deps() is False:
            return False

        return True

    def generate_meta_file(self):
        """
        generate pacakge meta files
        """
        self.generate_hpd_meta_file()
        self.generate_pkg_meta_file()

    def run_workflow(self):
        """
        run workflow
        """
        # set current working dir
        os.chdir(self.working_dir)

        # run jobs
        jobs = self.yml_obj.jobs
        ordered_jobs = self.sort_jobs(jobs)
        logging.debug("workflow job order: {}".format(", ".join(ordered_jobs)))

        ret = True
        for job_name in ordered_jobs:
            logging.info("run job: {}".format(job_name))
            job = jobs[job_name]
            if self.run_workflow_job(job=job) is False:
                ret = False
                break

        # reset working dir
        os.chdir(self.working_dir)

        return ret

    def run_workflow_job(self, job):
        """
        run workflow job
        :param job: single job
        """
        steps = job.get("steps", [])
        for i in range(len(steps)):
            step = steps[i]
            step_name = step.get("name", "")
            logging.debug("run step[{}]: {}".format(i, step_name))
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
            real_command = VarReplaceHandle.replace(command, self.all_var_dict)
            if real_command is None:
                logging.error("failed replace variable in: {}".format(command))
                return False
            if self.command_handle.exec(command=real_command) is False:
                return False
        return True

    def sort_jobs(self, jobs):
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
            errmsg = "Cycle dependence in jobs!!!"
            logging.error(errmsg)
            raise Exception(errmsg)

        result = []
        for idx in dep_result:
            result.append(job_name_list[idx])

        return result

    def generate_hpd_meta_file(self):
        """
        generate hpd meta dependencies file
        """
        d = {
            "maintainer": self.src.maintainer,
            "name": self.src.name,
            "tag": self.src.tag,
            "build_type": self.guess_build_type(self.all_var_dict),
            "platform": dict(self.platform_info.get_ordered_dict()),
            "deps": self.deps,
        }
        filepath = os.path.join(self.task_dir, "{}.yml".format(APP_NAME))
        yaml_handle = YamlHandle()
        yaml_handle.write(filepath=filepath, obj=d)

    def generate_pkg_meta_file(self):
        """
        generate hpd meta pkg file
        """
        d = {
            "meta_file": os.path.join(
                self.task_dir, "{}.yml".format(APP_NAME)),
            "output_dir": self.inner_var_dict["OUTPUT_DIR"],
            "pkg_dir": self.inner_var_dict["PKG_DIR"],
        }
        filepath = os.path.join(self.task_dir, "pkg.yml")
        yaml_handle = YamlHandle()
        yaml_handle.write(filepath=filepath, obj=d)

    def prepare_vars_and_src(self):
        """
        prepare all variables and sources
        """
        # init inner variables
        self.init_inner_var_dict()

        # load platform informations
        self.platform_info.load_local()
        self.inner_var_dict_add_platform(self.platform_info)

        # init all_var_dict, now only have input params, input param derived
        # info and platform infos
        for k, v in self.inner_var_dict.items():
            var_name = "{}_{}".format(APP_NAME.upper(), k)
            self.all_var_dict[var_name] = v

        for k, v in self.input_param_dict.items():
            self.all_var_dict[k] = v

        # first time replace yml variables
        self.yml_vars = self.yml_obj.variables
        VarReplaceHandle.replace_list(self.yml_vars, self.all_var_dict)

        # try download source
        source_path = self.working_dir

        self.src = self.get_yml_source(self.yml_obj.source, self.all_var_dict)
        if self.need_download_source(self.src):
            src_downloader = SourceDownloader(self.command_handle)
            if src_downloader.download(
                    self.src, self.settings_handle.source_path) is False:
                return False
            source_path = src_downloader.source_path

        self.inner_var_dict["SOURCE_PATH"] = source_path

        # set git info
        self.git_info.get_git_info(source_path)
        self.inner_var_dict_add_git(self.git_info)

        # update all_var_dict
        for k, v in self.inner_var_dict.items():
            var_name = "{}_{}".format(APP_NAME.upper(), k)
            if var_name in self.all_var_dict:
                continue
            self.all_var_dict[var_name] = v

        # second times replace yml variables
        if VarReplaceHandle.replace_list(
                self.yml_vars, self.all_var_dict) is False:
            return False

        return True

    def prepare_deps(self):
        """
        prepare dependencies
        """
        self.deps = self.yml_obj.deps

        repo_deps_handle = RepoDepsHandle(
            self.settings_handle,
            self.platform_info,
            self.guess_build_type(self.all_var_dict)
        )

        if repo_deps_handle.search_all_deps(self.deps) is False:
            logging.error("failed search dependencies")
            return False

        if repo_deps_handle.download_all_deps(self.deps_dir) is False:
            logging.error("failed download dependencies")
            return False

        return True

    def need_download_source(self, src_info: SourceInfo):
        """
        check is need to download source
        """
        if len(src_info.repo_kind) > 0 and len(src_info.repo_url) > 0:
            return True
        else:
            return False

    def get_yml_source(self, src_dict: typing.Dict, replace_dict: typing.Dict):
        """
        get yml source
        :param replace_dict: current variable replace dict
        """
        for k in src_dict.keys():
            v = src_dict[k]
            v = VarReplaceHandle.replace(v, replace_dict)
            if v is None:
                errmsg = "failed get yml source.{}: {}".format(k, src_dict[k])
                logging.error(errmsg)
                raise Exception(errmsg)
            src_dict[k] = v
        src_info = SourceInfo()
        src_info.load(src_dict)
        return src_info

    def init_inner_var_dict(self):
        """
        set inner variables
        """
        self.inner_var_dict = {
            "ROOT_DIR": self.working_dir,
            "TASK_DIR": self.task_dir,
            "BUILD_DIR": self.build_dir,
            "PKG_DIR": self.pkg_dir,
            "DEPS_DIR": self.deps_dir,
            "TEST_DEPS_DIR": self.test_deps_dir,
            "OUTPUT_DIR": self.output_dir,
            "FILE_DIR": os.path.dirname(self.cfg_file_path),
            "FILE_NAME": os.path.basename(self.cfg_file_path),
            "FILE_PATH": self.cfg_file_path,
            "TASK_NAME": self.task_name,
            "TASK_ID": self.task_id,
        }

    def inner_var_dict_add_platform(self, platform_info: PlatformInfo):
        """
        add platform inner variable
        """
        self.inner_var_dict["PLATFORM_SYSTEM"] = platform_info.system
        self.inner_var_dict["PLATFORM_RELEASE"] = platform_info.release
        self.inner_var_dict["PLATFORM_VERSION"] = platform_info.version
        self.inner_var_dict["PLATFORM_MACHINE"] = platform_info.machine
        self.inner_var_dict["PLATFORM_DISTR"] = platform_info.distr
        self.inner_var_dict["PLATFORM_LIBC"] = platform_info.libc

    def inner_var_dict_add_git(self, git_info: GitInfo):
        self.inner_var_dict["GIT_REF"] = git_info.ref
        self.inner_var_dict["GIT_TAG"] = git_info.tag
        self.inner_var_dict["GIT_COMMIT_ID"] = git_info.commit_id
        self.inner_var_dict["GIT_BRANCH"] = git_info.branch

    def guess_build_type(self, all_vars):
        """
        guess build type
        """
        build_type = ""
        try_words = [
            "build-type",
            "build_type",
            "BUILD_TYPE",
            "BUILDTYPE",
        ]
        for word in try_words:
            if word not in all_vars:
                continue
            build_type = all_vars[word]
            break
        return build_type

    def output_vars(self):
        """
        output arguments
        """
        logging.debug(
            "\n-------- input args --------\n"
            "task_cfg={}\n"
            "task_name={}\n"
            "task_id={}\n"
            "working_dir={}\n"
            "artifacts_search_dir={}\n"
            "params={}\n"
            "output_dir={}\n"
            "".format(
                self.cfg_file_path,
                self.task_name,
                self.task_id,
                self.working_dir,
                self.settings_handle.pkg_search_repos,
                self.input_param_dict,
                self.output_dir,
            )
        )

        s = ""
        for k, v in self.inner_var_dict.items():
            s = s + "{}_{}={}\n".format(APP_NAME.upper(), k, v)
        logging.debug(
            "\n-------- builder inner variables --------\n"
            "{}".format(s)
        )

        s = ""
        for k, v in self.input_param_dict.items():
            s = s + "{}={}\n".format(k, v)
        logging.debug(
            "\n-------- builder user input variables --------\n"
            "{}".format(s)
        )

        s = ""
        for var in self.yml_vars:
            for k in var.keys():
                v = self.all_var_dict[k]
                s = s + "{}={}\n".format(k, v)
        logging.debug(
            "\n-------- builder user yaml variables --------\n"
            "{}".format(s)
        )
