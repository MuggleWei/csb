import getopt
import os
import sys
from constant_var import APP_NAME
from package_meta import PackageMeta
from settings_handle import RepoConfig, SettingsHandle


class SearcherConfig:
    def __init__(self):
        self.maintainer = ""
        self.repo = ""
        self.ver = ""
        self.build_type = ""
        self.distr = ""
        self.machine = ""
        self.settings_path = ""


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

        target_paths = self._search_candidate()
        print("search results: ")
        for target in target_paths:
            if target[0] == "local":
                print("--------")
                print("package: {}".format(target[1]))
                print("meta file: {}".format(target[2]))

    def _search_candidate(self):
        """
        search candidate target path
        """
        target_paths = []
        if len(self._settings_handle.pkg_search_repos) == 0:
            print("WARNING! Artifacts search repo list is empty")

        for search_repo in self._settings_handle.pkg_search_repos:
            if search_repo.kind == "local":
                local_target_paths = self._search_candidate_local(search_repo)
                target_paths.extend(local_target_paths)
            elif search_repo.kind == "remote":
                print("WARNING! "
                      "Artifacts search remote repo currently not support")
            else:
                print("invalid search repo kind: {}".format(search_repo.kind))
        return target_paths

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

            if len(self.cfg.ver) > 0 and \
                    len(pkg_meta.tag) > 0 and \
                    self.cfg.ver != pkg_meta.tag:
                continue
            if len(self.cfg.build_type) > 0 and \
                    len(pkg_meta.build_type) > 0 and \
                    self.cfg.build_type != pkg_meta.build_type:
                continue
            if len(self.cfg.distr) > 0 and \
                    len(pkg_meta.platform_distro) > 0 and \
                    pkg_meta.platform_distro.find(self.cfg.distr) == -1:
                continue
            if len(self.cfg.machine) > 0 and \
                    len(pkg_meta.platform_machine) > 0 and \
                    self.cfg.machine != pkg_meta.platform_machine:
                continue
            target_paths.append([
                "local",
                pkg_filepath,
                pkg_meta,
            ])
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
                "build-type=", "distr=", "machine=", "settings="
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
                cfg.ver = arg
            elif opt in ("-t", "--build-type"):
                cfg.build_type = arg
            elif opt in ("-d", "--distr"):
                cfg.distr = arg
            elif opt in ("--machine"):
                cfg.machine = arg
            elif opt in ("-s", "--settings"):
                cfg.settings_path = arg

        return cfg
