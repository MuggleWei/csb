import getopt
import os
import sys
from constant_var import APP_NAME
from settings_handle import RepoConfig, SettingsHandle


class SearcherConfig:
    def __init__(self):
        self.owner = ""
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
            "    , --owner string      [REQUIRED] repository owner\n" \
            "    , --repo string       [REQUIRED] repository name\n" \
            "  -v, --ver string        [OPTIONAL] package version\n" \
            "  -t, --build-type string [OPTIONAL] package build type, by default set release\n" \
            "  -p, --pkg string        [OPTIONAL] package file\n" \
            "  -s, --settings string   [OPTIONAL] manual set settings.xml\n" \
            "e.g.\n" \
            "  {0} search --owner google --repo googletest\n" \
            "  {0} search --owner google --repo googletest -v v1.13.0\n" \
            "  {0} search --owner google --repo googletest -v v1.13.0 -t release\n" \
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
            print("cfg: {}".format(target[2]))

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
            self.cfg.owner,
            self.cfg.repo
        )
        if not os.path.exists(search_path):
            return []
        ver_dirs = os.listdir(search_path)
        for ver_dir in ver_dirs:
            if len(self.cfg.ver) > 0 and self.cfg.ver != ver_dir:
                continue
            ver_path = os.path.join(search_path, ver_dir)
            build_type_dirs = os.listdir(ver_path)
            for build_type_dir in build_type_dirs:
                if len(self.cfg.build_type) > 0 and \
                        self.cfg.build_type != build_type_dir:
                    continue
                build_type_path = os.path.join(ver_path, build_type_dir)
                target_paths.append(build_type_path)
        return target_paths

    def _handle_target_paths(self, target_paths):
        """
        handle target paths
        """
        targets = []
        for target_path in target_paths:
            try:
                cfg_file = ""
                pkg_file = ""
                files = os.listdir(target_path)
                for filename in files:
                    if self._is_cfg_file(filename=filename):
                        if len(cfg_file) > 0:
                            raise Exception(
                                "multiple {} config file in {}".format(
                                    APP_NAME, target_path))
                        cfg_file = filename
                    if self._is_pkg_file(filename=filename):
                        if len(pkg_file) > 0:
                            raise Exception(
                                "multiple {} package file in {}".format(
                                    APP_NAME, target_path))
                        pkg_file = filename
                targets.append([target_path, pkg_file, cfg_file])
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

        if len(self.cfg.owner) == 0:
            print("Error! field 'owner' missing\n\n{}".format(self._usage_str))
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
            args, "hv:t:p:s:",
            [
                "help", "owner=", "repo=", "ver=",
                "build-type=", "pkg=", "settings="
            ]
        )

        for opt, arg in opts:
            if opt in ("-h", "--help"):
                print(self._usage_str)
                sys.exit(0)
            elif opt in ("--owner"):
                cfg.owner = arg
            elif opt in ("--repo"):
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
