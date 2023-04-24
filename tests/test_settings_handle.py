import unittest

from hpb.component.settings_handle import SettingsHandle
from hpb.data_type.constant_var import APP_NAME
from hpb.utils.utils import Utils


class TestSettingsHandle(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self._handle = SettingsHandle()
        self._handle.clean()

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

    def test_packages(self):
        self._handle.load("./etc/test_settings_handle/settings_package.xml")

        path1 = Utils.expand_path("~/.{}/packages".format(APP_NAME))
        path2 = Utils.expand_path(
            "~/.local/share/{}/packages".format(APP_NAME))
        self.assertEqual(len(self._handle.pkg_search_repos), 2)
        self.assertEqual(self._handle.pkg_search_repos[0].kind, "local")
        self.assertEqual(path1, self._handle.pkg_search_repos[0].path)
        self.assertEqual(self._handle.pkg_search_repos[1].kind, "local")
        self.assertEqual(path2, self._handle.pkg_search_repos[1].path)

        path1 = "/var/local/hpb/packages"
        path2 = Utils.expand_path("~/.{}/packages".format(APP_NAME))
        self.assertEqual(len(self._handle.pkg_upload_repos), 2)
        self.assertEqual(self._handle.pkg_upload_repos[0].kind, "local")
        self.assertEqual(path1, self._handle.pkg_upload_repos[0].path)
        self.assertEqual(self._handle.pkg_upload_repos[1].kind, "local")
        self.assertEqual(path2, self._handle.pkg_upload_repos[1].path)


if __name__ == "__main__":
    unittest.main()
