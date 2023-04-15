import datetime
import logging
import os
import typing
from hpb.builder import BuilderConfig
from hpb.command_handle import CommandHandle
from hpb.constant_var import APP_NAME
from hpb.git_info import GitInfo
from hpb.log_handle import LogHandle
from hpb.platform_info import PlatformInfo
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
        self.all_var_dict = {}
        self.inner_var_dict = {}
        self.yml_vars = {}

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
            micro_sec = "{:06}".format(now.strftime("%f"))
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

    def prepare_dirs(self):
        """
        prepare directories
        """
        os.makedirs(self.task_dir, exist_ok=True)
        os.makedirs(self.build_dir, exist_ok=True)
        os.makedirs(self.pkg_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.deps_dir, exist_ok=True)
        os.makedirs(self.test_deps_dir, exist_ok=True)

    def run(self):
        """
        run workflow
        """
        # prepare directories
        self.prepare_dirs()

        # chdir to working directory
        os.chdir(self.working_dir)

        workflow_log_path = os.path.join(self.task_dir, "workflow.log")
        with open(workflow_log_path, "w") as f:
            self.command_handle.set_fp(f)

            if self.prepare() is False:
                return False

        return True

    def prepare(self):
        """
        run prepare steps
        """
        # load yaml file
        if self.load_yaml_file() is False:
            return False

        if self.prepare_variables() is False:
            return False

        # TODO:

        return True

    def prepare_variables(self):
        """
        prepare all variables
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

        # first time replace
        self.yml_vars = self.yml_obj.get_variables()
        VarReplaceHandle.replace_list(self.yml_vars, self.all_var_dict)

        # try download source
        source_path = self.working_dir

        src_info = self.get_yml_source(
            self.yml_obj.get_source_dict(), self.all_var_dict)
        if src_info is None:
            return False
        if self.need_download_source(src_info):
            src_downloader = SourceDownloader(self.command_handle)
            if src_downloader.download(
                    src_info, self.settings_handle.source_path) is False:
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

        # second times replace variables
        if VarReplaceHandle.replace_list(
                self.yml_vars, self.all_var_dict) is False:
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
                logging.error(
                    "failed get yml source.{}: {}".format(k, src_dict[k]))
                return None
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
