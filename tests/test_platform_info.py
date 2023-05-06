import json
import typing
import unittest

from hpb.component.yaml_handle import YamlHandle
from hpb.data_type.platform_info import PlatformInfo


class TestPlatformInfo(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self._obj = {
            "system": "linux",
            "release": "6.2.9-arch1-1",
            "version": "#1 SMP PREEMPT_DYNAMIC Thu, 30 Mar 2023 14:51:14 +0000",
            "machine": "x86_64",
            "distr_id": "arch",
            "distr_ver": "",
        }

    def test_load(self):
        platform_info = PlatformInfo()
        platform_info.load(obj=self._obj)
        self.assert_platform_info_eq(platform_info)

    def test_get_dict(self):
        platform_info = PlatformInfo()
        platform_info.load(obj=self._obj)
        ordered_dict = platform_info.get_ordered_dict()
        for k, v in ordered_dict.items():
            obj_v = self._obj.get(k, None)
            self.assertIsNotNone(obj_v)
            if obj_v is None:
                continue
            self.assertEqual(v, obj_v)

    def test_get_str(self):
        platform_info = PlatformInfo()
        platform_info.load(obj=self._obj)
        s = str(platform_info)
        platform_info_obj = json.loads(s)
        for k, v in platform_info_obj.items():
            obj_v = self._obj.get(k, None)
            self.assertIsNotNone(obj_v)
            if obj_v is None:
                continue
            self.assertEqual(v, obj_v)

    def test_load_from_file(self):
        handle = YamlHandle()
        platform_info_obj: typing.Optional[typing.Dict] = handle.load(
            "./share/test_platform_info/platform.yml")
        self.assertIsNotNone(platform_info_obj)
        if platform_info_obj is None:
            # for get rid of editor warning
            return
        obj = platform_info_obj.get("platform", None)

        platform_info = PlatformInfo()
        platform_info.load(obj=obj)
        self.assert_platform_info_eq(platform_info)

    def test_load_local(self):
        platform_info = PlatformInfo()
        platform_info.load_local()
        self.assertGreater(len(platform_info.system), 0)
        self.assertGreater(len(platform_info.machine), 0)

    def test_field_distr(self):
        platform_info = PlatformInfo()
        platform_info.load(obj=self._obj)
        self.assertEqual(platform_info.distr, "arch")

    def test_field_libc(self):
        platform_info = PlatformInfo()
        platform_info.load(obj=self._obj)

    def assert_platform_info_eq(self, platform_info: PlatformInfo):
        self.assertEqual(platform_info.system, self._obj["system"])
        self.assertEqual(platform_info.release, self._obj["release"])
        self.assertEqual(platform_info.version, self._obj["version"])
        self.assertEqual(platform_info.machine, self._obj["machine"])
        self.assertEqual(platform_info.distr_id, self._obj["distr_id"])
        self.assertEqual(platform_info.distr_ver, self._obj["distr_ver"])


if __name__ == "__main__":
    unittest.main()
