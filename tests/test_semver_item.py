import unittest

from hpb.data_type.semver_item import SemverItem


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
            semver = SemverItem()
            ret = semver.load(v)
            self.assertTrue(ret)
            self.assertEqual(semver.major, 1)
            self.assertEqual(semver.minor, 10)
            self.assertEqual(semver.patch, 6)

    def test_compare_equal(self):
        semver_list = [
            ["1.10.1", "v1.10.1"],
        ]
        for v in semver_list:
            v1 = SemverItem()
            ret = v1.load(v[0])
            self.assertTrue(ret)

            v2 = SemverItem()
            ret = v2.load(v[1])
            self.assertTrue(ret)

            result = v1.compare(v2)
            self.assertEqual(result, 0)

    def test_compare(self):
        semver_list = [
            ["1.10.1", "1.10.1-alpha"],
            ["1.10.1-beta", "1.10.1-alpha"],
            ["1.10.1-rc.1", "1.10.1-rc"],
        ]
        for v in semver_list:
            v1 = SemverItem()
            ret = v1.load(v[0])
            self.assertTrue(ret)

            v2 = SemverItem()
            ret = v2.load(v[1])
            self.assertTrue(ret)

            result = v1.compare(v2)
            self.assertEqual(result, 1)

        for v in semver_list:
            v1 = SemverItem()
            ret = v1.load(v[1])
            self.assertTrue(ret)

            v2 = SemverItem()
            ret = v2.load(v[0])
            self.assertTrue(ret)

            result = v1.compare(v2)
            self.assertEqual(result, -1)


if __name__ == "__main__":
    unittest.main()
