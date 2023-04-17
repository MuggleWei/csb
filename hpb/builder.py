import getopt
import logging
import sys

from hpb.builder_config import BuilderConfig
from hpb.constant_var import APP_NAME
from hpb.utils import Utils
from hpb.workflow_handle import WorkflowHandle


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

        # workflow
        self._workflow = WorkflowHandle()

    def run(self, args):
        """
        run package builder
        """
        # init arguments and prepare build/log directory
        if self._init(args=args) is False:
            return False

        # init log
        self._workflow.init_log()

        logging.info("{} builder run task {}.{}".format(
            APP_NAME, self._workflow.task_name, self._workflow.task_id))

        if self._workflow.load_yaml_file() is False:
            return False

        return self._workflow.run()

    def _init(self, args):
        """
        init arguments
        """
        cfg = self._parse_args(args)
        if cfg is None:
            return False

        if len(cfg.config_path) == 0:
            print("Error! config path not be set")
            print(self._usage_str)
            sys.exit(1)

        cfg.config_path = Utils.expand_path(cfg.config_path)
        cfg.working_dir = Utils.expand_path(cfg.working_dir)
        cfg.output_dir = Utils.expand_path(cfg.output_dir)

        if self._workflow.set_input_args(cfg) is False:
            return False

        self._workflow.load_settings(cfg.settings_path)

        return True

    def _parse_args(self, args):
        """
        parse input arguments
        """
        cfg = BuilderConfig()
        try:
            opts, _ = getopt.getopt(
                args, "hc:p:o:s:",
                [
                    "help", "config=", "task-name=", "task-id=",
                    "work-dir=", "param=", "output-dir=", "settings="
                ]
            )
        except Exception as e:
            print("{}, exit...".format(str(e)))
            sys.exit(1)

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

        return cfg
