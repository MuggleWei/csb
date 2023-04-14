import typing


class WorkflowYaml:
    """
    workflow yaml object
    """

    def __init__(self):
        self.obj = {}
        self.variables = {}
        self.source = {}
        self.deps = {}
        self.test_deps = {}
        self.jobs = {}

    def load(self, obj: typing.Optional[typing.Dict]):
        """
        load yml object
        """
        if obj is None:
            return False

        self.obj = obj

        self.variables = self.obj.get("variables", {})
        self.source = self.obj.get("source", {})
        self.deps = self.obj.get("deps", {})
        self.test_deps = self.obj.get("test_deps", {})
        self.jobs = self.obj.get("jobs", {})

        return True

    def get_variables(self):
        """
        get yml variable dict
        """
        var_dict = {}
        for variable in self.variables:
            for k, v in variable.items():
                var_dict[k] = v
        return var_dict

    def get_source_dict(self):
        """
        get yml source info
        """
        src_dict = {}
        for k, v in self.source.items():
            src_dict[k] = v
        return src_dict
        # source_info = SourceInfo()
        # for k, v in self.source.items():
        #     if k == "name":
        #         source_info.name = v
        #     elif k == "maintainer":
        #         source_info.maintainer = v
        #     elif k == "tag":
        #         source_info.tag = str(v)
        #     elif k == "repo_kind":
        #         source_info.repo_kind = v
        #     elif k == "repo_url":
        #         source_info.repo_url = v
        #     elif k == "git_depth":
        #         if v.isdigit():
        #             source_info.git_depth = int(v)
        # return source_info
