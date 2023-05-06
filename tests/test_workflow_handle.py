import os
import shutil
import unittest

from hpb.utils.utils import Utils


class TestWorkflowHandle(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.working_dir = "./hpb/test_workflow_handle"
        self.working_dir = Utils.expand_path(self.working_dir)
        if os.path.exists(self.working_dir):
            shutil.rmtree(self.working_dir)
        os.makedirs(self.working_dir, exist_ok=True)

    def test_set_input_args(self):
        pass


if __name__ == "__main__":
    unittest.main()
