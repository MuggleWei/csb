import os

from hpb.component.var_replace_handle import VarReplaceHandle


class Utils:
    """
    utils functions
    """

    @classmethod
    def expand_path(cls, filepath):
        """
        expand file path
        """
        ret_filepath = filepath
        if len(filepath) > 0:
            ret_filepath = os.path.expanduser(ret_filepath)
            ret_filepath = os.path.expandvars(ret_filepath)
            ret_filepath = os.path.abspath(ret_filepath)
        return ret_filepath

    @classmethod
    def get_boolean(cls, val, var_replace_dict={}):
        """
        get boolean value
        """
        if type(val) is str:
            val = VarReplaceHandle.replace(val, var_replace_dict)

        if type(val) is bool:
            return val
        elif type(val) is str:
            if val.lower() in ["true", "1", "yes"]:
                return True
            else:
                return False
        elif type(val) is int:
            if val == 0:
                return False
            else:
                return True
        elif type(val) is float:
            if int(val) == 0:
                return False
            else:
                return True
        return False
