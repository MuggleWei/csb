import json
from typing import OrderedDict


class BuildInfo:
    """
    build info
    """

    def __init__(self):
        self.build_type = ""
        self.fat_pkg = False

    def __str__(self) -> str:
        return json.dumps(self.get_ordered_dict(), indent=2)

    def __repr__(self) -> str:
        return self.__str__()

    def get_ordered_dict(self):
        """
        get field ordered dict
        """
        return OrderedDict([
            ("build_type", self.build_type),
            ("fat_pkg", self.fat_pkg),
        ])

    def load(self, obj):
        """
        load from object
        """
        self.build_type = obj.get("build_type", "release")
        self.fat_pkg = obj.get("fat_pkg", False)
