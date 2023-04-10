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
        self.assertEqual(len(self._handle.art_search_path), 3)
        path1 = os.path.expanduser("~/.{}/artifacts".format(APP_NAME))
        path2 = os.path.expanduser(
            "~/.local/share/{}/artifacts".format(APP_NAME))
        path3 = os.path.expanduser("/etc/share/{}/artifacts".format(APP_NAME))
        self.assertEqual(path1, self._handle.art_search_path[0])
        self.assertEqual(path2, self._handle.art_search_path[1])
        self.assertEqual(path3, self._handle.art_search_path[2])


if __name__ == "__main__":
    unittest.main()
