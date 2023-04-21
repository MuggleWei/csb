import json
import os
import typing
import xml.dom.minidom

from xml.dom.minidom import Element

from hpb.constant_var import APP_NAME
from hpb.utils import Utils


class RepoConfig:
    """
    repo config
    """

    def __init__(self):
        self.kind = ""
        self.path = ""
        self.url = ""
        self.name = ""
        self.passwd = ""

    def __str__(self) -> str:
        if self.kind == "local":
            return json.dumps({
                "kind": self.kind,
                "path": self.path,
            })
        elif self.kind == "remote":
            return json.dumps({
                "kind": self.kind,
                "url": self.url,
                "name": self.name,
                "passwd": "******",
            })
        else:
            return "{}"

    def __repr__(self) -> str:
        return self.__str__()


class SettingsHandle:
    """
    settings file handle
    """

    @classmethod
    def load_settings(cls, user_settings=""):
        """
        load settings
        """
        default_settings_paths = []
        default_settings_paths.extend([
            Utils.expand_path("~/.{}/settings.xml".format(APP_NAME)),
            Utils.expand_path(
                "~/.local/share/{}/settings.xml".format(APP_NAME)),
            "/usr/local/etc/{}/settings.xml".format(APP_NAME),
            "/etc/{}/settings.xml".format(APP_NAME),
            "/usr/share/{}/settings.xml".format(APP_NAME),
        ])

        settings_filepath = ""
        if len(user_settings) > 0:
            if not os.path.exists(user_settings):
                raise Exception("User input settings.xml({}) not exists".format(
                    user_settings
                ))
            settings_filepath = user_settings
        else:
            for filepath in default_settings_paths:
                if not os.path.exists(filepath):
                    continue
                settings_filepath = filepath

        if len(settings_filepath) == 0:
            raise Exception("Can't find settings.xml")

        settings_handle = SettingsHandle()
        settings_handle.load(Utils.expand_path(settings_filepath))
        return settings_handle

    def __init__(self):
        """
        initialize settings handle
        """
        self.log_console_level = ""
        self.log_file_level = ""
        self.source_path = ""
        self.pkg_search_repos: typing.List[RepoConfig] = []
        self.pkg_upload_repo = None
        self.build_if_not_exists = False

    def load(self, filepath):
        """
        load setting file
        :param filepath: settings file path
        """
        if not os.path.exists(filepath):
            return False
        root = xml.dom.minidom.parse(file=filepath)
        self._parse_dom(root=root)

    def _parse_dom(self, root):
        """
        parse xml dom
        """
        nodes = root.getElementsByTagName("log")
        for node in nodes:
            self._load_log(node)

        nodes = root.getElementsByTagName("sources")
        for node in nodes:
            self._load_sources(node)

        nodes = root.getElementsByTagName("artifacts")
        for node in nodes:
            self._load_artifacts(node)

    def _load_log(self, node_log: Element):
        """
        load log config
        """
        if len(self.log_console_level) == 0 and \
                node_log.hasAttribute("console_level"):
            self.log_console_level = node_log.getAttribute("console_level")
        if len(self.log_file_level) == 0 and \
                node_log.hasAttribute("file_level"):
            self.log_file_level = node_log.getAttribute("file_level")

    def _load_sources(self, node_sources):
        """
        load sources path
        """
        if len(self.source_path) == 0:
            node_source_list = node_sources.getElementsByTagName("path")
            for node_source in node_source_list:
                val = node_source.firstChild.nodeValue
                val = Utils.expand_path(val)
                self.source_path = val
                break

    def _load_artifacts(self, node_artifacts):
        """
        load artifacts search path
        """
        node_search_list = node_artifacts.getElementsByTagName("search")
        for node_search in node_search_list:
            node_repos = node_search.getElementsByTagName("repo")
            for node_repo in node_repos:
                repo = self._parse_repo(node_repo=node_repo)
                if repo is None:
                    continue
                self.pkg_search_repos.append(repo)

        node_upload_list = node_artifacts.getElementsByTagName("upload")
        for node_upload in node_upload_list:
            if self.pkg_upload_repo is not None:
                break
            node_repos = node_upload.getElementsByTagName("repo")
            for node_repo in node_repos:
                repo = self._parse_repo(node_repo=node_repo)
                if repo is None:
                    continue
                self.pkg_upload_repo = repo
                break

    def _parse_repo(self, node_repo):
        """
        parse repo node
        """
        repo = RepoConfig()
        node_kinds = node_repo.getElementsByTagName("kind")
        if len(node_kinds) != 1:
            print("Error! failed find single 'kind' in repo")
            return None
        repo.kind = node_kinds[0].firstChild.nodeValue
        if repo.kind == "local":
            node_paths = node_repo.getElementsByTagName("path")
            if len(node_paths) != 1:
                print("Error! failed find single 'path' in repo")
                return None
            repo.path = node_paths[0].firstChild.nodeValue
            repo.path = Utils.expand_path(repo.path)
        elif repo.kind == "remote":
            node_urls = node_repo.getElementsByTagName("url")
            if len(node_urls) != 1:
                print("Error! failed find single 'url' in repo")
                return None
            repo.url = node_urls[0].firstChild.nodeValue

            node_name = node_repo.getElementsByTagName("name")
            if len(node_name) == 1:
                repo.name = node_name[0].firstChild.nodeValue

            node_passwd = node_repo.getElementsByTagName("passwd")
            if len(node_passwd) == 1:
                repo.passwd = node_passwd[0].firstChild.nodeValue
        else:
            print("Error! invalid repo kind: {}".format(repo.kind))
            return None

        return repo
