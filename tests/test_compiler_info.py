import platform
import unittest

from hpb.data_type.compiler_info import CompilerInfo


class TestCompilerInfo(unittest.TestCase):

    def test_compiler_info(self):
        if platform.system().lower() != "linux":
            return

        compiler_info = CompilerInfo()
        ret = compiler_info.load_local_gcc()
        self.assertTrue(ret)
        self.assertEqual(compiler_info.compiler_c, "gcc")
        self.assertGreater(len(compiler_info.compiler_c_ver), 0)
        self.assertEqual(compiler_info.compiler_cpp, "g++")
        self.assertGreater(len(compiler_info.compiler_cpp_ver), 0)

        compiler_info = CompilerInfo()
        ret = compiler_info.load_local_clang()
        if ret is True:
            self.assertEqual(compiler_info.compiler_c, "clang")
            self.assertGreater(len(compiler_info.compiler_c_ver), 0)
            self.assertEqual(compiler_info.compiler_cpp, "clang++")
            self.assertGreater(len(compiler_info.compiler_cpp_ver), 0)

        compiler_info = CompilerInfo()
        ret = compiler_info.load_local_musl_gcc()
        if ret is True:
            self.assertEqual(compiler_info.compiler_c, "musl-gcc")
            self.assertGreater(len(compiler_info.compiler_c_ver), 0)
            self.assertEqual(compiler_info.compiler_cpp, "musl-g++")
            self.assertGreater(len(compiler_info.compiler_cpp_ver), 0)


if __name__ == "__main__":
    unittest.main()
