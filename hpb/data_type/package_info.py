import json
from typing import OrderedDict
from hpb.data_type.package_meta import PackageMeta


class PackageInfo:
    def __init__(self):
        self.repo_type = ""  # local or remote
        self.path = ""
        self.meta = PackageMeta()

    def __str__(self):
        return json.dumps(self.get_ordered_dict(), indent=2)

    def __repr__(self) -> str:
        return self.__str__()

    def get_ordered_dict(self):
        """
        get field ordered dict
        """
        return OrderedDict([
            ("path", self.path),
            ("meta", self.meta.get_ordered_dict()),
        ])
