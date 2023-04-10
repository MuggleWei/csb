import os


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
