import os
import unittest
from constant_var import APP_NAME

from settings_handle import SettingsHandle


class TestSettingsHandle(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self._handle = SettingsHandle()
        self._handle.load(filepath="./etc/test_settings1.xml")
        self._handle.load(filepath="./etc/test_settings2.xml")

    def test_artifacts_search_path(self):
        self.assertEqual(len(self._handle.pkg_search_repos), 4)
        path1 = os.path.expanduser("~/.{}/artifacts".format(APP_NAME))
        path2 = os.path.expanduser(
            "~/.local/share/{}/artifacts".format(APP_NAME))
        url3 = "https://repo.mugglewei.org/hpb"
        name3 = "hello"
        passwd3 = "123456"
        path4 = os.path.expanduser("/etc/share/{}/artifacts".format(APP_NAME))

        self.assertEqual(self._handle.pkg_search_repos[0].kind, "local")
        self.assertEqual(path1, self._handle.pkg_search_repos[0].path)

        self.assertEqual(self._handle.pkg_search_repos[1].kind, "local")
        self.assertEqual(path2, self._handle.pkg_search_repos[1].path)

        self.assertEqual(self._handle.pkg_search_repos[2].kind, "remote")
        self.assertEqual(url3, self._handle.pkg_search_repos[2].url)
        self.assertEqual(name3, self._handle.pkg_search_repos[2].name)
        self.assertEqual(passwd3, self._handle.pkg_search_repos[2].passwd)

        self.assertEqual(self._handle.pkg_search_repos[3].kind, "local")
        self.assertEqual(path4, self._handle.pkg_search_repos[3].path)


if __name__ == "__main__":
    unittest.main()
