import logging
import os
import subprocess


class GitInfo:
    """
    git information
    """

    def __init__(self):
        """
        init git info
        """
        self.tag = ""
        self.commit_id = ""
        self.branch = ""
        self.ref = ""

    def get_git_info(self, dirpath):
        """
        get git informations of dirpath
        """
        origin_dir = os.path.abspath(os.curdir)
        os.chdir(dirpath)

        self.tag = self._get_git_tag()
        self.commit_id = self._get_git_commit_id()
        self.branch = self._get_git_branch()
        if len(self.tag) > 0:
            self.ref = self.tag
        elif len(self.commit_id) > 0:
            self.ref = "{}_{}".format(self.branch, self.commit_id)
        else:
            self.ref = ""

        os.chdir(origin_dir)

    def _get_git_tag(self):
        """
        get git tag
        """
        v = ""
        try:
            result = subprocess.run(
                "git describe --tags --exact-match 2> /dev/null",
                shell=True,
                stdout=subprocess.PIPE)
            v = result.stdout.decode("utf-8").strip()
        except Exception as e:
            logging.debug("failed get git tag: {}".format(str(e)))
        return v

    def _get_git_commit_id(self):
        """
        get git commit id
        """
        v = ""
        try:
            result = subprocess.run(
                "git rev-parse --short HEAD",
                shell=True,
                stdout=subprocess.PIPE)
            v = result.stdout.decode("utf-8").strip()
        except Exception as e:
            logging.debug("failed get git commit id: {}".format(str(e)))
        return v

    def _get_git_branch(self):
        """
        get git branch
        """
        v = ""
        try:
            result = subprocess.run(
                "git symbolic-ref -q --short HEAD",
                shell=True,
                stdout=subprocess.PIPE)
            v = result.stdout.decode("utf-8").strip()
        except Exception as e:
            logging.debug("failed get git branch: {}".format(str(e)))
        return v
