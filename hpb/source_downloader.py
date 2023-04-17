import logging
import os

from hpb.command_handle import CommandHandle
from hpb.source_info import SourceInfo


class SourceDownloader:
    def __init__(self, command_handle: CommandHandle):
        self.command_handle = command_handle
        self.source_path = ""

    def download(self, src_info: SourceInfo, source_root: str):
        """
        download source
        """
        if len(source_root) == 0:
            logging.error("failed found source root path in settings")
            return False

        if src_info.repo_kind == "git":
            return self.download_src_git(src_info, source_root)
        else:
            logging.error("invalid field 'source.repo_kind': {}".format(
                src_info.repo_kind))
            return False

    def download_src_git(self, src_info: SourceInfo, source_root: str):
        """
        download source through git
        """
        if src_info.name == "":
            logging.error(
                "failed download source, field 'source.name' is empty")
            return False

        if src_info.maintainer == "":
            logging.error(
                "failed download source, field 'source.maintainer' is empty")
            return False

        if src_info.repo_url == "":
            logging.error(
                "failed download source, field 'source.repo_url' is empty")
            return False

        if src_info.git_depth == 1:
            if src_info.tag == "":
                logging.error(
                    "failed download source, "
                    "use git depth=1 with field 'source.tag' is empty")
                return False
            self.source_path = os.path.join(
                source_root,
                src_info.maintainer,
                "{}-{}".format(src_info.name, src_info.tag)
            )
            if os.path.exists(self.source_path):
                logging.info("{} already exists, skip download".format(
                    self.source_path))
                return True
            command = "git clone --branch={} --depth={} {} {}".format(
                src_info.tag,
                src_info.git_depth,
                src_info.repo_url,
                self.source_path
            )
            logging.info("run command: {}".format(command))
            return self.command_handle.exec(command=command)
        else:
            self.source_path = os.path.join(
                source_root,
                src_info.maintainer,
                src_info.name
            )
            if os.path.exists(self.source_path):
                return self._checkout_src_tag(self.source_path, src_info.tag)
            command = "git clone {} {}".format(
                src_info.repo_url,
                self.source_path
            )
            logging.info("run command: {}".format(command))
            ret = self.command_handle.exec(command=command)
            if ret is False:
                return ret
            return self._checkout_src_tag(self.source_path, src_info.tag)

    def _checkout_src_tag(self, src_path, tag):
        """
        checkout git source tag
        """
        origin_dir = os.path.abspath(os.curdir)
        os.chdir(src_path)
        logging.info("change dir to: {}".format(os.path.abspath(os.curdir)))
        command = "git checkout {}".format(tag)
        logging.info("run command: {}".format(command))
        ret = self.command_handle.exec(command=command)
        os.chdir(origin_dir)
        logging.info("restore dir to: {}".format(os.path.abspath(os.curdir)))
        return ret
