import unittest

from hpb.semver_handle import SemverHandle


class TestSemverHandle(unittest.TestCase):
    def test_split(self):
        semver_list = [
            "1.10.6",
            "v1.10.6",
            "1.10.6-alpha.1",
            "v1.10.6-beta.5",
            "1.10.6-rc.1",
        ]

        for v in semver_list:
            semver = SemverHandle.parse(v)
            self.assertIsNotNone(semver)
            self.assertEqual(len(semver), 4)
            self.assertEqual(semver[0], 1)
            self.assertEqual(semver[1], 10)
            self.assertEqual(semver[2], 6)

    def test_compare_equal(self):
        semver_list = [
            ["1.10.1", "v1.10.1"],
        ]
        for v in semver_list:
            v1 = SemverHandle.parse(v[0])
            v2 = SemverHandle.parse(v[1])
            result = SemverHandle.compare(v1, v2)
            self.assertEqual(result, 0)

    def test_compare(self):
        semver_list = [
            ["1.10.1", "1.10.1-alpha"],
            ["1.10.1-beta", "1.10.1-alpha"],
            ["1.10.1-rc.1", "1.10.1-rc"],
        ]
        for v in semver_list:
            v1 = SemverHandle.parse(v[0])
            v2 = SemverHandle.parse(v[1])
            result = SemverHandle.compare(v1, v2)
            self.assertEqual(result, 1)
        for v in semver_list:
            v1 = SemverHandle.parse(v[1])
            v2 = SemverHandle.parse(v[0])
            result = SemverHandle.compare(v1, v2)
            self.assertEqual(result, -1)


if __name__ == "__main__":
    unittest.main()
