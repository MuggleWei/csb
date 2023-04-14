import json
from typing import OrderedDict


class SourceInfo:
    """
    source info
    """

    def __init__(self):
        self.maintainer = ""
        self.name = ""
        self.tag = ""
        self.repo_kind = ""
        self.repo_url = ""
        self.git_depth = 1

    def __str__(self) -> str:
        return json.dumps(OrderedDict([
            ("maintainer", self.maintainer),
            ("name", self.name),
            ("tag", self.tag),
            ("repo_kind", self.repo_kind),
            ("repo_url", self.repo_url),
            ("git_depth", self.git_depth),
        ]), indent=2)

    def __repr__(self) -> str:
        return self.__str__()

    def load(self, obj):
        """
        load from object
        """
        self.maintainer = obj.get("maintainer", "")
        self.name = obj.get("name", "")
        self.tag = obj.get("tag", "")
        self.repo_kind = obj.get("repo_kind", "")
        self.repo_url = obj.get("repo_url", "")
        self.git_depth = obj.get("git_depth", "")
