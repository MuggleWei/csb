import json
import typing
import unittest

from hpb.component.yaml_handle import YamlHandle
from hpb.data_type.source_info import SourceInfo


class TestSourceInfo(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self._obj = {
            "maintainer": "mugglewei",
            "name": "hpb",
            "tag": "1.0.0",
            "repo_kind": "git",
            "repo_url": "https://github.com/MuggleWei/hpb.git",
            "git_depth": 1,
        }

    def test_load(self):
        src_info = SourceInfo()
        src_info.load(obj=self._obj)
        self.assert_source_info_eq(src_info)

    def test_get_dict(self):
        src_info = SourceInfo()
        src_info.load(obj=self._obj)
        orderd_dict = src_info.get_ordered_dict()
        for k, v in orderd_dict.items():
            obj_v = self._obj.get(k, None)
            self.assertIsNotNone(obj_v)
            if obj_v is None:
                continue
            self.assertEqual(v, obj_v)

    def test_get_str(self):
        src_info = SourceInfo()
        src_info.load(obj=self._obj)
        s = str(src_info)
        src_obj = json.loads(s)
        for k, v in src_obj.items():
            obj_v = self._obj.get(k, None)
            self.assertIsNotNone(obj_v)
            if obj_v is None:
                continue
            self.assertEqual(v, obj_v)

    def test_load_from_file(self):
        handle = YamlHandle()
        src_obj: typing.Optional[typing.Dict] = handle.load(
            "./share/test_source_info/hpb.yml")
        self.assertIsNotNone(src_obj)
        if src_obj is None:
            # for get rid of editor warning
            return
        obj = src_obj.get("source", None)

        src_info = SourceInfo()
        src_info.load(obj=obj)
        self.assert_source_info_eq(src_info)

    def assert_source_info_eq(self, src_info: SourceInfo):
        self.assertEqual(src_info.maintainer, self._obj["maintainer"])
        self.assertEqual(src_info.name, self._obj["name"])
        self.assertEqual(src_info.tag, self._obj["tag"])
        self.assertEqual(src_info.repo_kind, self._obj["repo_kind"])
        self.assertEqual(src_info.repo_url, self._obj["repo_url"])
        self.assertEqual(src_info.git_depth, self._obj["git_depth"])


if __name__ == "__main__":
    unittest.main()
