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

        self._content = self._replace_var_params(content)
        if self._content is None:
            logging.error("failed replace param variables")
            return None

        logging.debug("load yaml file: \n{}".format(self._content))

        # parse
        return yaml.safe_load(self._content)

    def _replace_var_params(self, content):
        """
        replace all param variables
        """
        finds = re.findall(r'\${\w+}', content)
        find_set = set(finds)
        logging.debug("find variable in yaml: {}".format(
            ", ".join(find_set)))
        for var in find_set:
            var_name = var[2:-1]
            if var_name not in self._param:
                logging.error("failed find variable param: {}".format(var))
                return None
            content = content.replace(var, self._param[var_name])
        return content
