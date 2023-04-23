import json
import os
import typing
import xml.dom.minidom

from hpb.data_type.constant_var import APP_NAME
from hpb.utils.singleton import singleton
from hpb.utils.utils import Utils


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

    def key(self) -> str:
        if self.kind == "local":
            return "l#{}".format(self.path)
        elif self.kind == "remote":
            return "r#{}".format(self.url)
        return ""


@singleton
class SettingsHandle:
    """
    settings file handle
    """

    def __init__(self):
        """
        initialize settings handle
        """
        self.clean()

    def clean(self):
        self.log_console_level = ""
        self.log_file_level = ""
        self.db_path = ""
        self.source_path = ""
        self.pkg_search_repos: typing.List[RepoConfig] = []
        self.pkg_upload_repos: typing.List[RepoConfig] = []
        self.build_if_not_exists = False

    def init(self, user_settings=""):
        """
        init settings handle
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
            Exception("Can't find settings.xml")

        self.load(Utils.expand_path(settings_filepath))

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
        self._load_log(nodes)

        nodes = root.getElementsByTagName("db")
        self._load_db(nodes)

        nodes = root.getElementsByTagName("sources")
        self._load_sources(nodes)

        nodes = root.getElementsByTagName("artifacts")
        self._load_artifacts(nodes)

    def _load_log(self, nodes):
        """
        load log config
        """
        if len(nodes) == 0:
            print("WARNING! Can't find 'log' in settings, use default")
            self.log_console_level = "info"
            self.log_file_level = "debug"
            return

        if len(nodes) > 1:
            print("WARNING! Multiple 'log' in settings, use first node")

        node_log = nodes[0]

        if len(self.log_console_level) == 0 and \
                node_log.hasAttribute("console_level"):
            self.log_console_level = node_log.getAttribute("console_level")
        if len(self.log_file_level) == 0 and \
                node_log.hasAttribute("file_level"):
            self.log_file_level = node_log.getAttribute("file_level")

    def _load_db(self, nodes):
        """
        load db config
        """
        if len(nodes) == 0:
            print("WARNING! Can't find 'db' in settings, use default")
            default_db_path = "~/.{0}/{0}.db".format(APP_NAME)
            self.db_path = Utils.expand_path(default_db_path)
            return

        if len(nodes) > 1:
            print("WARNING! Multiple 'db' in settings, use first node")

        node_db = nodes[0]
        val = node_db.firstChild.nodeValue
        self.db_path = Utils.expand_path(val)

    def _load_sources(self, nodes):
        """
        load sources path
        """
        default_source_path = "~/.{}/sources".format(APP_NAME)

        if len(nodes) == 0:
            print("WARNING! Can't find 'sources' in settings, use default")
            self.source_path = Utils.expand_path(default_source_path)
            return

        if len(nodes) > 1:
            print("WARNING! Multiple 'sources' in settings, use first node")

        node_sources = nodes[0]
        node_path_list = node_sources.getElementsByTagName("path")
        if len(node_path_list) == 0:
            print("WARNING! Can't find 'sources/path' in settings, use default")
            self.source_path = Utils.expand_path(default_source_path)
            return

        if len(node_path_list) > 1:
            print(
                "WARNING! Multiple 'sources.path' in settings, use first node")

        node_source = node_path_list[0]
        val = node_source.firstChild.nodeValue
        self.source_path = Utils.expand_path(val)

    def _load_artifacts(self, nodes):
        """
        load artifacts search path
        """
        default_repo = RepoConfig()
        default_repo.kind = "local"
        default_repo.path = "~/.{}/artifacts".format(APP_NAME)

        if len(nodes) == 0:
            print("WARNING! Can't find 'artifacts' in settings, use default")
            self.pkg_search_repos.append(default_repo)
            self.pkg_upload_repos.append(default_repo)
            return

        if len(nodes) > 1:
            print("WARNING! Multiple 'artifacts' in settings, use first node")

        node_artifacts = nodes[0]

        self.pkg_search_repos = self._get_repos(node_artifacts, "search")
        if len(self.pkg_search_repos) == 0:
            self.pkg_search_repos.append(default_repo)

        self.pkg_upload_repos = self._get_repos(node_artifacts, "upload")
        if len(self.pkg_upload_repos) == 0:
            self.pkg_upload_repos.append(default_repo)

    def _get_repos(self, parent, node_name):
        """
        get repo list in parent[node_name]
        """
        node_list = parent.getElementsByTagName(node_name)
        keys = set()
        ret_list = []
        for node in node_list:
            node_repos = node.getElementsByTagName("repo")
            for node_repo in node_repos:
                repo = self._parse_repo(node_repo=node_repo)
                if repo is None:
                    continue

                k = repo.key()
                if k in keys:
                    continue
                keys.add(k)

                ret_list.append(repo)

        return ret_list

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
            print("WARNING! Temporary not support remote repo")
            return None
        else:
            print("Error! invalid repo kind: {}".format(repo.kind))
            return None

        return repo
