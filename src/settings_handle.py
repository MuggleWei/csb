import os
import xml.dom.minidom

from xml.dom.minidom import Element

from constant_var import APP_NAME
from utils import Utils


class SettingsHandle:
    """
    settings file handle
    """

    @classmethod
    def load_default_settings(cls):
        settings_handle = SettingsHandle()
        settings_path = [
            Utils.expand_path("~/.{}/settings.xml".format(APP_NAME)),
            Utils.expand_path(
                "~/.local/share/{}/settings.xml".format(APP_NAME)),
            "/etc/{}/settings.xml".format(APP_NAME),
        ]
        for filepath in settings_path:
            if os.path.exists(filepath):
                print("load default settings: {}".format(filepath))
                settings_handle.load(filepath=filepath)
        return settings_handle

    def __init__(self):
        """
        initialize settings handle
        """
        self.log_console_level = ""
        self.log_file_level = ""
        self.source_path = ""
        self.art_search_path = []
        self.art_upload_path = ""

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
        for node_path in node_search_list:
            val = node_path.firstChild.nodeValue
            val = Utils.expand_path(val)
            self.art_search_path.append(val)

        if len(self.art_upload_path) == 0:
            node_upload_list = node_artifacts.getElementsByTagName("upload")
            for node_upload in node_upload_list:
                val = node_upload.firstChild.nodeValue
                val = Utils.expand_path(val)
                self.art_upload_path = val
                break
