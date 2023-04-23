import getopt
import logging
import os
import sys
import typing

from hpb.component.settings_handle import RepoConfig, SettingsHandle
from hpb.data_type.constant_var import APP_NAME
from hpb.data_type.package_meta import MetaMatch, PackageMeta
from hpb.utils.ptree import ptree


class SearcherConfig:
    def __init__(self):
        self.maintainer = ""
        self.name = ""
        self.tag = ""
        self.build_type = ""
        self.system_name = ""
        self.distr = ""
        self.machine = ""
        self.settings_path = ""


class SearcherResult:
    def __init__(self):
        self.repo_type = ""  # local or remote
        self.path = ""  # package path
        self.meta = PackageMeta()  # meta object


class Searcher:
    """
    package searcher
    """

    def __init__(self):
        """
        init package searcher
        """
        self._usage_str = "Usage: {0} search [OPTIONS]\n" \
            "\n" \
            "Options: \n" \
            "  -m, --maintainer string [REQUIRED] repository maintainer\n" \
            "  -n, --name string       [REQUIRED] repository name\n" \
            "  -v, --ver string        [OPTIONAL] package version\n" \
            "  -t, --build-type string [OPTIONAL] package build type, by default set release\n" \
            "    , --system string     [OPTIONAL] system string, e.g. linux, windows\n" \
            "  -d, --distr string      [OPTIONAL] distrubution string, e.g. ubuntu, arch, alpine, ubuntu-22.04, alpine-3.17\n" \
            "    , --machine string    [OPTIONAL] platform machine, e.g. x64_64\n" \
            "e.g.\n" \
            "  {0} search --maintainer google --repo googletest\n" \
            "  {0} search -m google -r googletest -v v1.13.0\n" \
            "  {0} search -m google -r googletest -v v1.13.0 -t release\n" \
            "".format(APP_NAME)

    def run(self, args):
        """
        run package searcher
        """
        if self._init(args=args) is False:
            return False

        results: typing.List[SearcherResult] = self._search_candidate()

        self._draw(results)

    def search(self, cfg: SearcherConfig) -> typing.List[SearcherResult]:
        """
        search packages invoke in codes
        :param cfg: search config
        :param settings_handle: settings handle
        """
        self.cfg = cfg

        if len(self.cfg.maintainer) == 0:
            return []
        if len(self.cfg.name) == 0:
            return []

        return self._search_candidate()

    def _search_candidate(self):
        """
        search candidate target path
        """
        results = []
        settings_handle = SettingsHandle()
        if len(settings_handle.pkg_search_repos) == 0:
            logging.warning("Artifacts search repo list is empty")

        result_dict = set()
        for search_repo in settings_handle.pkg_search_repos:
            if search_repo.kind == "local":
                local_target_results = self._search_candidate_local(search_repo)
                for result in local_target_results:
                    if result.path in result_dict:
                        continue
                    results.append(result)
                    result_dict.add(result.path)
            elif search_repo.kind == "remote":
                logging.warning(
                    "Artifacts search remote repo currently not support")
            else:
                logging.warning(
                    "invalid search repo kind: {}".format(search_repo.kind))
        return results

    def _search_candidate_local(self, repo: RepoConfig) \
            -> typing.List[SearcherResult]:
        """
        get search candidate in local repo
        """
        target_paths = []

        search_path = os.path.join(
            repo.path,
            self.cfg.maintainer,
            self.cfg.name
        )
        if not os.path.exists(search_path):
            return []

        dirs = os.listdir(search_path)
        for d in dirs:
            pkg_dir = os.path.join(search_path, d)
            if not os.path.isdir(pkg_dir):
                continue

            pkg_meta = self._get_local_meta(pkg_dir)
            if pkg_meta is None:
                continue

            pkg_filepath = self._get_local_pkg_filepath(pkg_dir)
            if pkg_filepath is None:
                continue

            if pkg_meta.is_tag_match(self.cfg.tag) == MetaMatch.mismatch:
                continue
            if pkg_meta.is_build_type_match(self.cfg.build_type) == \
                    MetaMatch.mismatch:
                continue
            if pkg_meta.is_system_match(self.cfg.system_name) == \
                    MetaMatch.mismatch:
                continue
            if pkg_meta.is_machine_match(self.cfg.machine) == \
                    MetaMatch.mismatch:
                continue
            if pkg_meta.is_distr_match(self.cfg.distr) == MetaMatch.mismatch:
                continue
            result = SearcherResult()
            result.repo_type = "local"
            result.path = pkg_filepath
            result.meta = pkg_meta
            target_paths.append(result)
        return target_paths

    def _get_local_meta(self, pkg_dir: str):
        """
        get meta file in package dir
        """
        meta_file = os.path.join(pkg_dir, "{}.yml".format(APP_NAME))
        if not os.path.exists(meta_file):
            logging.warning("failed find meta file in {}".format(pkg_dir))
            return None
        pkg_meta = PackageMeta()
        if pkg_meta.load_from_file(meta_file) is False:
            logging.warning("failed load meta file: {}".format(meta_file))
            return None
        return pkg_meta

    def _get_local_pkg_filepath(self, pkg_dir: str):
        """
        get pacakge file path
        """
        pkg_candidates = []
        files = os.listdir(pkg_dir)
        for f in files:
            if self._is_pkg_file(f):
                pkg_candidates.append(f)
        if len(pkg_candidates) == 0:
            logging.warning("failed find package in {}".format(pkg_dir))
            return None
        if len(pkg_candidates) > 1:
            logging.warning("multiple packages in {}".format(pkg_dir))
            return None
        pkg_filepath = os.path.join(pkg_dir, pkg_candidates[0])
        return pkg_filepath

    def _is_pkg_file(self, filename: str):
        """
        check file is package file
        :param filename: filename without dir
        """
        return filename.endswith(".tar.gz")

    def _draw(self, results: typing.List[SearcherResult]):
        """
        draw results
        """
        tree_dict = {}
        for result in results:
            tag = result.meta.source_info.tag
            if tag not in tree_dict:
                tree_dict[tag] = []
            if result.repo_type == "local":
                node = os.path.dirname(result.path)
            else:
                # TODO: support remote
                node = "(unrecognize repo_type)"
            tree_dict[tag].append(node)

        tag_list = []
        for k in tree_dict.keys():
            tag_list.append(k)

        s = "{}/{}".format(self.cfg.maintainer, self.cfg.name)
        tree_dict[s] = tag_list
        if len(tag_list) > 0:
            ptree(s, tree_dict)
        else:
            logging.info("Search results is empty")

    def _init(self, args):
        """
        init input arguments
        """
        self.cfg = self._parse_args(args=args)
        if self.cfg is None:
            return False

        if len(self.cfg.maintainer) == 0:
            logging.error(
                "field 'maintainer' missing\n\n{}".format(self._usage_str))
            return False
        if len(self.cfg.name) == 0:
            logging.error("field 'name' missing\n\n{}".format(self._usage_str))
            return False

        return True

    def _parse_args_getopts(self, args):
        """
        get argument opts
        """
        opts, _ = getopt.getopt(
            args, "hm:n:v:t:d:",
            [
                "help", "maintainer=", "name=", "ver=",
                "build-type=", "system=", "distr=", "machine=",
            ]
        )
        return opts

    def _parse_args(self, args):
        """
        init arguments
        """
        cfg = SearcherConfig()
        opts = self._parse_args_getopts(args)

        for opt, arg in opts:
            if opt in ("-h", "--help"):
                print(self._usage_str)
                sys.exit(0)
            elif opt in ("-m", "--maintainer"):
                cfg.maintainer = arg
            elif opt in ("-n", "--name"):
                cfg.name = arg
            elif opt in ("-v", "--ver"):
                cfg.tag = arg
            elif opt in ("-t", "--build-type"):
                cfg.build_type = arg
            elif opt in ("--system"):
                cfg.system_name = arg
            elif opt in ("-d", "--distr"):
                cfg.distr = arg
            elif opt in ("--machine"):
                cfg.machine = arg

        return cfg
