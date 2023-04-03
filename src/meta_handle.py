import logging
import json
import os


class MetaHandle:
    """
    meta file handler
    """
    def __init__(self):
        self._meta_dir = ""
        self._meta_dict = {}

    def load(self, filepath):
        """
        load meta file
        :param filepath: meta file path
        """
        self._meta_dir = os.path.dirname(filepath)
        try:
            logging.info("load meta file: {}".format(filepath))
            with open(filepath, "r") as f:
                meta_obj = json.load(f)
        except Exception as e:
            logging.error("faild load meta file, {}".format(str(e)))
            return False

        metas = meta_obj.get("metas", [])
        if len(metas) == 0:
            logging.error("failed found 'metas' field in meta object")
            return False

        for meta in metas:
            repo_tag = meta.get("tag", None)
            if repo_tag is None:
                logging.warning("skip invalid meta that without 'tag' field")
                continue

            repo_deps = meta.get("deps", None)
            if repo_deps is None:
                repo_deps = []

            repo_yml = meta.get("yml", None)
            if repo_yml is None:
                logging.warning(
                    "skip invalid meta(tag={}) "
                    "that without 'dockerfile' field".format(repo_tag))
                continue

            if repo_tag in self._meta_dict:
                logging.warning("repeated tag: {}, ignore".format(repo_tag))
                continue

            logging.debug("load meta: tag={}, yml={}, deps={}".format(
                repo_tag, repo_yml, repo_deps))
            self._meta_dict[repo_tag] = meta
        return True

    def get_yml(self, tag):
        """
        get yml file path
        :param tag: repository tag
        """
        if tag in self._meta_dict:
            meta = self._meta_dict[tag]
        elif "default" in self._meta_dict:
            meta = self._meta_dict["default"]
        else:
            logging.error("failed found corresponding tag: {}".format(tag))
            return None

        yml_filepath = meta.get("yml", None)
        if yml_filepath is None:
            logging.error("failed found yml config in meta: {}".format(tag))
            return None

        if not os.path.isabs(yml_filepath):
            yml_filepath = os.path.join(self._meta_dir, yml_filepath)
        yml_filepath = os.path.abspath(yml_filepath)

        return yml_filepath
