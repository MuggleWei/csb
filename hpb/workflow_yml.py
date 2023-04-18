import platform
import typing


class WorkflowYaml:
    """
    workflow yaml object
    """

    def __init__(self):
        self._obj = {}
        self._variables = []
        self._source = {}
        self._deps = []
        self._test_deps = []
        self._jobs = {}

    def load(self, obj: typing.Optional[typing.Dict]):
        """
        load yml object
        """
        if obj is None:
            return False

        self._obj = obj

        self._variables = self._obj.get("variables", [])
        self._source = self._obj.get("source", {})
        self._deps = self._obj.get("deps", [])
        self._test_deps = self._obj.get("test_deps", [])
        self._jobs = self._obj.get("jobs", {})

        return True

    @property
    def variables(self):
        """
        get yml variable dict
        """
        variables = []
        for var in self._variables:
            for k, v in var.items():
                if type(v) is dict:
                    val = self._get_platform_var(v)
                    variables.append({k: val})
                else:
                    variables.append(var)
        return variables

    def _get_platform_var(self, vdict):
        """
        get platform specific variable
        """
        curr_system = platform.system().lower()
        val = ""
        for k, v in vdict.items():
            if k == "default":
                val = v
            elif k == curr_system:
                val = v
                break
        return val

    @property
    def source(self):
        """
        get yml source info
        """
        return self._source

    @property
    def deps(self):
        """
        get yml deps
        """
        return self._deps

    @property
    def test_deps(self):
        """
        get yml deps
        """
        return self._test_deps

    @property
    def jobs(self):
        """
        get jobs
        """
        return self._jobs
