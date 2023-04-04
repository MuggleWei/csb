import os
import xml.dom.minidom

from xml.dom.minidom import Element


class SettingsHandle:
    """
    settings file handle
    """

    def __init__(self):
        """
        initialize settings handle
        """
        self.art_search_path = []

    def load(self, filepath):
        """
        load setting file
        :param filepath: settings file path
        """
        if not os.path.exists(filepath):
            return False
        root = xml.dom.minidom.parse(file=filepath)
        self._parse_dom(root=root)

    def _parse_dom(self, root: Element):
        """
        parse xml dom
        """
        nodes = root.getElementsByTagName("artifacts")
        for node in nodes:
            self._load_artifacts(node)

    def _load_artifacts(self, node_artifacts):
        """
        load artifacts search path
        """
        node_path_list = node_artifacts.getElementsByTagName("path")
        for node_path in node_path_list:
            val = node_path.firstChild.nodeValue
            val = os.path.expandvars(val)
            val = os.path.expanduser(val)
            self.art_search_path.append(val)
