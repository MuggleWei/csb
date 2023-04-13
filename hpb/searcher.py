import getopt
import os
import sys
import typing

from .constant_var import APP_NAME
from .package_meta import MetaMatch, PackageMeta
from .settings_handle import RepoConfig, SettingsHandle


class SearcherConfig:
    def __init__(self):
        self.maintainer = ""
        self.repo = ""
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
            "  -r, --repo string       [REQUIRED] repository name\n" \
            "  -v, --ver string        [OPTIONAL] package version\n" \
            "  -t, --build-type string [OPTIONAL] package build type, by default set release\n" \
            "  -s, --settings string   [OPTIONAL] manual set settings.xml\n" \
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
        print("search results: ")
        for result in results:
            if result.repo_type == "local":
                print("--------")
                print("package: {}".format(result.path))
                print("meta file: {}".format(result.meta))

    def search(self, cfg: SearcherConfig, settings_handle) \
            -> typing.List[SearcherResult]:
        """
        search packages invoke in codes
        :param cfg: search config
        :param settings_handle: settings handle
        """
        self.cfg = cfg
        self._settings_handle = settings_handle

        if len(self.cfg.maintainer) == 0:
            return []
        if len(self.cfg.repo) == 0:
            return []

        return self._search_candidate()

    def _search_candidate(self):
        """
        search candidate target path
        """
        results = []
        if len(self._settings_handle.pkg_search_repos) == 0:
            print("WARNING! Artifacts search repo list is empty")

        for search_repo in self._settings_handle.pkg_search_repos:
            if search_repo.kind == "local":
                local_target_paths = self._search_candidate_local(search_repo)
                results.extend(local_target_paths)
            elif search_repo.kind == "remote":
                print("WARNING! "
                      "Artifacts search remote repo currently not support")
            else:
                print("invalid search repo kind: {}".format(search_repo.kind))
        return results

    def _search_candidate_local(self, repo: RepoConfig):
        """
        get search candidate in local repo
        """
        target_paths = []

        search_path = os.path.join(
            repo.path,
            self.cfg.maintainer,
            self.cfg.repo
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
            print("Warning! failed find meta file in {}".format(pkg_dir))
            return None
        pkg_meta = PackageMeta()
        if pkg_meta.load(meta_file) is False:
            print("Warning! failed load meta file: {}".format(meta_file))
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
            print("Warning! failed find package in {}".format(pkg_dir))
            return None
        if len(pkg_candidates) > 1:
            print("Warning! multiple packages in {}".format(pkg_dir))
            return None
        pkg_filepath = os.path.join(pkg_dir, pkg_candidates[0])
        return pkg_filepath

    def _is_pkg_file(self, filename: str):
        """
        check file is package file
        :param filename: filename without dir
        """
        return filename.endswith(".tar.gz")

    def _init(self, args):
        """
        init input arguments
        """
        self.cfg = self._parse_args(args=args)
        if self.cfg is None:
            return False

        if len(self.cfg.maintainer) == 0:
            print("Error! field 'maintainer' missing\n\n{}".format(self._usage_str))
            return False
        if len(self.cfg.repo) == 0:
            print("Error! field 'repo' missing\n\n{}".format(self._usage_str))
            return False

        user_settings = []
        if len(self.cfg.settings_path) > 0:
            user_settings.append(self.cfg.settings_path)
        self._settings_handle = SettingsHandle.load_settings(user_settings)

        return True

    def _parse_args(self, args):
        """
        init arguments
        """
        cfg = SearcherConfig()
        opts, _ = getopt.getopt(
            args, "hm:r:v:t:d:s:",
            [
                "help", "maintainer=", "repo=", "ver=",
                "build-type=", "system=", "distr=", "machine=",
                "settings="
            ]
        )

        for opt, arg in opts:
            if opt in ("-h", "--help"):
                print(self._usage_str)
                sys.exit(0)
            elif opt in ("-m", "--maintainer"):
                cfg.maintainer = arg
            elif opt in ("-r", "--repo"):
                cfg.repo = arg
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
            elif opt in ("-s", "--settings"):
                cfg.settings_path = arg

        return cfg
