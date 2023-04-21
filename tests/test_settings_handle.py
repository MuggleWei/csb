import unittest

from hpb.constant_var import APP_NAME
from hpb.settings_handle import SettingsHandle
from hpb.utils import Utils


class TestSettingsHandle(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self._handle = SettingsHandle()

    def test_log(self):
        self._handle.load("./etc/test_settings_handle/settings_log.xml")

        self.assertEqual(self._handle.log_console_level, "warning")
        self.assertEqual(self._handle.log_file_level, "error")

    def test_db(self):
        self._handle.load("./etc/test_settings_handle/settings_db.xml")
        self.assertEqual(self._handle.db_path, "/var/hpb/hpb.db")

    def test_src(self):
        self._handle.load("./etc/test_settings_handle/settings_src.xml")
        self.assertEqual(
            self._handle.source_path,
            Utils.expand_path("~/helloworld/sources")
        )

    def test_artifacts(self):
        self._handle.load("./etc/test_settings_handle/settings_art.xml")

        path1 = Utils.expand_path("~/.{}/artifacts".format(APP_NAME))
        path2 = Utils.expand_path(
            "~/.local/share/{}/artifacts".format(APP_NAME))
        self.assertEqual(len(self._handle.pkg_search_repos), 2)
        self.assertEqual(self._handle.pkg_search_repos[0].kind, "local")
        self.assertEqual(path1, self._handle.pkg_search_repos[0].path)
        self.assertEqual(self._handle.pkg_search_repos[1].kind, "local")
        self.assertEqual(path2, self._handle.pkg_search_repos[1].path)

        path1 = "/var/local/hpb/artifacts"
        path2 = Utils.expand_path("~/.{}/artifacts".format(APP_NAME))
        self.assertEqual(len(self._handle.pkg_upload_repos), 2)
        self.assertEqual(self._handle.pkg_upload_repos[0].kind, "local")
        self.assertEqual(path1, self._handle.pkg_upload_repos[0].path)
        self.assertEqual(self._handle.pkg_upload_repos[1].kind, "local")
        self.assertEqual(path2, self._handle.pkg_upload_repos[1].path)


if __name__ == "__main__":
    unittest.main()
