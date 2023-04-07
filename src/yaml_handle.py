import logging
import re
import yaml


class YamlHandle:
    """
    YAML file handle
    """

    def __init__(self):
        self._param = {}
        self._content = ""

    def set_param(self, k, v):
        """
        set parameter variable
        """
        self._param[k] = v

    def load(self, filepath):
        """
        load yml file
        """
        try:
            with open(filepath, "r") as f:
                content = f.read()
        except Exception as e:
            logging.error("failed read {}, {}".format(filepath, str(e)))
            return None

        self._content = content
        logging.debug("load yaml file: \n{}".format(self._content))

        return yaml.safe_load(self._content)
