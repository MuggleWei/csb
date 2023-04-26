import getopt
import logging
import os
import rich
import sys
import typing

from hpb.component.db_handle import DBHandle
from hpb.component.settings_handle import RepoConfig, SettingsHandle
from hpb.data_type.constant_var import APP_NAME
from hpb.data_type.package_info import PackageInfo
from hpb.data_type.package_meta import MetaMatch, PackageMeta
from hpb.mapper.mapper_pkg import MapperPkg
from rich.tree import Tree


class SearcherConfig:
    def __init__(self):
        self.maintainer = ""
        self.name = ""
        self.tag = ""
        self.build_type = ""
        self.system_name = ""
        self.distr = ""
        self.machine = ""


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
            "  -m, --maintainer string [OPTIONAL] repository maintainer\n" \
            "  -n, --name string       [OPTIONAL] repository name\n" \
            "  -v, --ver string        [OPTIONAL] package version\n" \
            "    , --system string     [OPTIONAL] system string, e.g. linux, windows\n" \
            "    , --build-type string [OPTIONAL] package build type, by default set release\n" \
            "    , --distr string      [OPTIONAL] distrubution string, e.g. ubuntu, arch, alpine, ubuntu-22.04, alpine-3.17\n" \
            "    , --machine string    [OPTIONAL] platform machine, e.g. x64_64\n" \
            "\n" \
            "There are 4 mode for search\n" \
            "1. list packages: maintainer + name + ver\n" \
            "e.g.\n" \
            "  {0} search --maintainer google --name googletest --ver v1.13.0\n" \
            "  google/googletest@v1.13.0\n" \
            "  │\n" \
            "  ├──── ~/.hpb/packages/google/googletest/v1.13.0-debug-linux-arch-x86_64\n" \
            "  │     (fat_pkg=false, cc=gcc-12.2.1, cxx=g++-12.2.1, libc=glibc-2.37)\n" \
            "  │\n" \
            "  ├──── ~/.hpb/packages/google/googletest/v1.13.0-release-linux-arch-x86_64\n" \
            "  │     (fat_pkg=false, cc=gcc-12.2.1, cxx=g++-12.2.1, libc=glibc-2.37)\n" \
            "  ......\n" \
            "\n" \
            "2. list versions: maintainer + name\n" \
            "e.g.\n" \
            "  {0} search --maintainer google --name googletest\n" \
            "  google/googletest\n" \
            "  ├──── v1.13.0\n" \
            "  ├──── v1.12.0\n" \
            "  ......\n" \
            "\n" \
            "3. list maintainer's repositories: maintainer\n" \
            "e.g.\n" \
            "  {0} search --maintainer google\n" \
            "  google\n" \
            "  ├──── brotli\n" \
            "  ├──── googletest\n" \
            "  ├──── leveldb\n" \
            "  ......\n" \
            "\n" \
            "4. list repositories: name\n" \
            "e.g.\n" \
            "  googletest\n" \
            "  ├──── google/googletest\n" \
            "  ├──── mugglewei/googletest\n" \
            "  ......\n" \
            "".format(APP_NAME)

    def run(self, args):
        """
        run package searcher
        """
        if self._init(args=args) is False:
            return False

        if len(self.cfg.maintainer) > 0:
            if len(self.cfg.name) > 0:
                if len(self.cfg.tag) > 0:
                    self._list_packages()
                else:
                    self._list_versions()
            else:
                self._list_maintainer_repos()
        elif len(self.cfg.name) > 0:
            self._list_repos()
        else:
            logging.error(
                "Input arguments invalid!\n{}".format(self._usage_str))
            sys.exit(1)

    def search(self, cfg: SearcherConfig) -> typing.List[PackageInfo]:
        """
        search packages invoke in codes
        :param cfg: search config
        :param settings_handle: settings handle
        """
        self.cfg = cfg
        return self._search_candidate()

    def _list_packages(self):
        """
        list packages
        """
        results = self._search_candidate()
        root_name = "{}/{}@{}".format(
            self.cfg.maintainer, self.cfg.name, self.cfg.tag)
        tree = Tree(root_name)

        for pkg_info in results:
            node = "{}\n({})\n".format(pkg_info.path, pkg_info.meta.get_desc())
            tree.add(node)

        if len(results) == 0:
            tree.add("(Not Found)")

        rich.print(tree)

    def _list_versions(self):
        """
        list versions
        """
        tags = []

        # search local
        qry = PackageInfo()
        qry.meta.source_info.maintainer = self.cfg.maintainer
        qry.meta.source_info.name = self.cfg.name
        qry.meta.source_info.tag = self.cfg.tag
        db_path = SettingsHandle().db_path
        with DBHandle(db_path, isolation_level="EXCLUSIVE") as db_handle:
            mapper_pkg = MapperPkg()
            curr_tags = mapper_pkg.query_tags(db_handle.conn, qry)
            tags.extend(curr_tags)

        # search remote
        # TODO:

        # draw
        root_name = "{}/{}".format(self.cfg.maintainer, self.cfg.name)
        tree = Tree(root_name)
        for tag in tags:
            tree.add(tag)
        if len(tags) == 0:
            tree.add("(Not Found)")

        rich.print(tree)

        return tags

    def _list_maintainer_repos(self):
        """
        list maintainer's repositories
        """
        repos = []

        # search local
        qry = PackageInfo()
        qry.meta.source_info.maintainer = self.cfg.maintainer
        db_path = SettingsHandle().db_path
        with DBHandle(db_path, isolation_level="EXCLUSIVE") as db_handle:
            mapper_pkg = MapperPkg()
            curr_repos = mapper_pkg.query_maintainer_repos(db_handle.conn, qry)
            repos.extend(curr_repos)

        # search remote
        # TODO:

        # draw
        root_name = "{}".format(self.cfg.maintainer)
        tree = Tree(root_name)
        for repo in repos:
            tree.add(repo)
        if len(repos) == 0:
            tree.add("(Not Found)")

        rich.print(tree)

        return repos

    def _list_repos(self):
        """
        list repositories
        """
        maintainers = []

        # search local
        qry = PackageInfo()
        qry.meta.source_info.name = self.cfg.name
        db_path = SettingsHandle().db_path
        with DBHandle(db_path, isolation_level="EXCLUSIVE") as db_handle:
            mapper_pkg = MapperPkg()
            curr_maintainers = mapper_pkg.query_repos(db_handle.conn, qry)
            maintainers.extend(curr_maintainers)

        # search remote
        # TODO:

        # draw
        root_name = "{}".format(self.cfg.name)
        tree = Tree(root_name)
        for maintainer in maintainers:
            tree.add("{}/{}".format(maintainer, self.cfg.name))
        if len(maintainers) == 0:
            tree.add("(Not Found)")

        rich.print(tree)

        return maintainers

    def _search_candidate(self) -> typing.List[PackageInfo]:
        """
        search candidate target path
        """
        results: typing.List[PackageInfo] = []

        # search local
        qry = PackageInfo()
        qry.meta.source_info.maintainer = self.cfg.maintainer
        qry.meta.source_info.name = self.cfg.name
        qry.meta.source_info.tag = self.cfg.tag
        db_path = SettingsHandle().db_path
        with DBHandle(db_path, isolation_level="EXCLUSIVE") as db_handle:
            mapper_pkg = MapperPkg()
            curr_results = mapper_pkg.query(db_handle.conn, qry)
            results.extend(curr_results)

        # search remote
        # TODO:

        return results

    def _search_candidate_local(self, repo: RepoConfig) \
            -> typing.List[PackageInfo]:
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
            result = PackageInfo()
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

    # def _draw(self, results: typing.List[PackageInfo]):
    #     """
    #     draw results
    #     """
    #     tree_dict = {}
    #     for result in results:
    #         tag = result.meta.source_info.tag
    #         if tag not in tree_dict:
    #             tree_dict[tag] = []
    #         if result.repo_type == "local":
    #             node = os.path.dirname(result.path)
    #         else:
    #             # TODO: support remote
    #             node = "(unrecognize repo_type)"
    #         tree_dict[tag].append(node)

    #     tag_list = []
    #     for k in tree_dict.keys():
    #         tag_list.append(k)

    #     s = "{}/{}".format(self.cfg.maintainer, self.cfg.name)
    #     tree_dict[s] = tag_list
    #     if len(tag_list) > 0:
    #         ptree(s, tree_dict)
    #     else:
    #         logging.info("Search results is empty")

    def _init(self, args):
        """
        init input arguments
        """
        self.cfg = self._parse_args(args=args)
        if self.cfg is None:
            return False
        return True

    def _parse_args_getopts(self, args):
        """
        get argument opts
        """
        opts, _ = getopt.getopt(
            args, "hm:n:v:",
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
            elif opt in ("--build-type"):
                cfg.build_type = arg
            elif opt in ("--system"):
                cfg.system_name = arg
            elif opt in ("--distr"):
                cfg.distr = arg
            elif opt in ("--machine"):
                cfg.machine = arg

        return cfg
