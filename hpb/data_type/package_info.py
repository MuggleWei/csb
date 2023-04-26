import json
import hashlib

from typing import OrderedDict
from hpb.data_type.package_meta import PackageMeta


class PackageInfo:
    def __init__(self):
        self.repo_type = ""  # local or remote
        self.path = ""
        self.ts = 0
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

    def hash_val(self):
        desc = self.meta.get_desc()
        hash_obj = hashlib.sha256(desc.encode("utf-8"))
        return hash_obj.hexdigest()
