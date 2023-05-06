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

    @classmethod
    def compare_db_cond(cls, obj1, obj_cond):
        """
        compare db condition
        """
        for k in obj1.keys():
            if k not in obj_cond:
                return False
            v1 = obj1[k]
            v2 = obj_cond[k]
            if isinstance(v2, type(v1)) is False:
                breakpoint()
                return False
            if type(v2) is str and len(v2) == 0:
                continue
            if type(v2) is int and v2 == 0:
                continue
            if type(v2) is bool and v2 is False:
                continue

            if type(v1) is str or \
                    type(v1) is int or \
                    type(v1) is bool:
                if v1 != v2:
                    breakpoint()
                    return False
            elif type(v1) is dict:
                return cls.compare_db_cond(v1, v2)
        return True
