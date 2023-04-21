import unittest

from hpb.component.settings_handle import SettingsHandle


class TestRepoDepsHandle(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self._handle = SettingsHandle()


if __name__ == "__main__":
    unittest.main()
