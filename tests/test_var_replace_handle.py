import unittest

from hpb.component.var_replace_handle import VarReplaceHandle


class TestVarReplaceHandle(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.replace_dict = {
            "build_type": "release",
            "tag": "1.0.1",
            "machine": "x86_64",
        }

    def test_replace_var(self):
        val = "${tag}-${build_type}-${machine}"
        val = VarReplaceHandle.replace(val, self.replace_dict)
        self.assertIsNotNone(val)
        if val is None:
            return
        self.assertEqual(val, "{}-{}-{}".format(
            self.replace_dict["tag"],
            self.replace_dict["build_type"],
            self.replace_dict["machine"],
        ))

    def test_replace_list(self):
        vars = [
            {"maintainer": "mugglewei"},
            {"repo_name": "hpb"},
            {"tag": "1.0.0"},
            {"git_url": "https://github.com/MuggleWei/${repo_name}.git"},
            {"build_type": "debug"},
            {"pkg_name": "${repo_name}-${tag}-${build_type}-${machine}"},
        ]
        ret = VarReplaceHandle.replace_list(vars, self.replace_dict)
        self.assertTrue(ret)
        self.assertEqual(self.replace_dict["maintainer"], "mugglewei")
        self.assertEqual(self.replace_dict["tag"], "1.0.1")
        self.assertEqual(self.replace_dict["machine"], "x86_64")
        self.assertEqual(self.replace_dict["repo_name"], "hpb")
        self.assertEqual(
            self.replace_dict["git_url"],
            "https://github.com/MuggleWei/{}.git".format(
                self.replace_dict["repo_name"]))
        self.assertEqual(self.replace_dict["build_type"], "release")
        self.assertEqual(
            self.replace_dict["pkg_name"],
            "{}-{}-{}-{}".format(
                self.replace_dict["repo_name"],
                self.replace_dict["tag"],
                self.replace_dict["build_type"],
                self.replace_dict["machine"],
            ))

        var_dict = {}
        for var in vars:
            for k, v in var.items():
                var_dict[k] = v
        self.assertEqual(
            var_dict["maintainer"], self.replace_dict["maintainer"])
        self.assertEqual(var_dict["repo_name"], self.replace_dict["repo_name"])
        self.assertEqual(var_dict["tag"], "1.0.0")
        self.assertEqual(var_dict["git_url"], self.replace_dict["git_url"])
        self.assertEqual(var_dict["build_type"], "debug")
        self.assertEqual(var_dict["pkg_name"], self.replace_dict["pkg_name"])


if __name__ == "__main__":
    unittest.main()
