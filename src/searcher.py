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
        self.pkg = ""
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
            "  -p, --pkg string        [OPTIONAL] package file\n" \
            "  -s, --settings string   [OPTIONAL] manual set settings.xml\n" \
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
        targets = self._handle_target_paths(target_paths=target_paths)
        print("search results: ")
        for target in targets:
            if len(target[1]) == 0:
                continue
            print("--------")
            print("dir: {}".format(target[0]))
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
            meta_file = os.path.join(pkg_dir, "{}.yml".format(APP_NAME))
            pkg_meta = PackageMeta()
            if pkg_meta.load(meta_file) is False:
                continue
            if len(self.cfg.ver) > 0 and \
                    len(pkg_meta.tag) > 0 and \
                    self.cfg.ver != pkg_meta.tag:
                continue
            if len(self.cfg.build_type) > 0 and \
                    len(pkg_meta.build_type) > 0 and \
                    self.cfg.build_type != pkg_meta.build_type:
                continue
            target_paths.append(os.path.join(search_path, pkg_dir))
        return target_paths

    def _handle_target_paths(self, target_paths):
        """
        handle target paths
        """
        targets = []
        for target_path in target_paths:
            try:
                meta_file = ""
                pkg_file = ""
                files = os.listdir(target_path)
                for filename in files:
                    if self._is_cfg_file(filename=filename):
                        if len(meta_file) > 0:
                            raise Exception(
                                "multiple {} config file in {}".format(
                                    APP_NAME, target_path))
                        meta_file = filename
                    if self._is_pkg_file(filename=filename):
                        if len(pkg_file) > 0:
                            raise Exception(
                                "multiple {} package file in {}".format(
                                    APP_NAME, target_path))
                        pkg_file = filename
                targets.append([target_path, pkg_file, meta_file])
            except Exception as e:
                print("{}".format(str(e)))
        return targets

    def _is_cfg_file(self, filename: str):
        """
        check file is hpb config file
        :param filename: filename without dir
        """
        return filename.endswith(".yml") or filename.endswith(".yaml")

    def _is_pkg_file(self, filename: str):
        """
        check file is package file
        :param filename: filename without dir
        """
        return filename.endswith(".tar.gz") or filename.endswith(".zip")

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
            args, "hm:r:v:t:p:s:",
            [
                "help", "maintainer=", "repo=", "ver=",
                "build-type=", "pkg=", "settings="
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
            elif opt in ("-p", "--pkg"):
                cfg.pkg = arg
            elif opt in ("-s", "--settings"):
                cfg.settings_path = arg

        return cfg
