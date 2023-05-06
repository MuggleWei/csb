import json
import logging
import typing

from hpb.command.downloader import Downloader, DownloaderConfig
from hpb.command.searcher import Searcher, SearcherConfig, PackageInfo
from hpb.data_type.build_info import BuildInfo
from hpb.data_type.semver_item import SemverItem
from hpb.data_type.platform_info import PlatformInfo


class DepItem:
    def __init__(self):
        self.name = ""
        self.maintainer = ""
        self.tag = ""
        self.deps = []

    def __str__(self):
        return json.dumps(self.get_ordered_dict(), indent=2)

    def __repr__(self) -> str:
        return self.__str__()

    def get_ordered_dict(self):
        """
        get field ordered dict
        """
        return typing.OrderedDict([
            ("maintainer", self.maintainer),
            ("name", self.name),
            ("tag", self.tag),
        ])

    def load(self, dep):
        if not self.is_valid_dep(dep):
            logging.error("invalid dep item: {}".format(dep))
            return False
        self.name = dep["name"]
        self.maintainer = dep["maintainer"]
        self.tag = dep["tag"]
        self.deps = dep.get("deps", [])

        return True

    def is_valid_dep(self, dep):
        """
        is valid dep info
        """
        if "name" not in dep:
            return False
        if "maintainer" not in dep:
            return False
        if "tag" not in dep:
            return False
        return True

    def gen_key(self):
        """
        gen dep repo key
        """
        return "{}${}${}".format(
            self.name, self.maintainer, self.tag)

    def split_key(self, k):
        """
        split dep repo key
        """
        return k.split("$")


class RepoDepsHandle:
    """
    handle repository dependencies
    """

    def __init__(
            self,
            platform_info: PlatformInfo,
            build_info: BuildInfo):
        self.platform = platform_info
        self.build_info = build_info

        self.deps: typing.List[DepItem] = []
        self.search_result_dict = {}

    def search_all_deps(self, deps):
        """
        search all dependencies
        """
        for dep in deps:
            dep_item = DepItem()
            if dep_item.load(dep) is False:
                return False
            self.deps.append(dep_item)

        self.search_result_dict.clear()
        for dep in self.deps:
            if self.search_dep_item(dep) is False:
                return False
        return True

    def download_all_deps(self, download_dir):
        """
        download all deps
        :param download_dir: download directory
        """
        repo_dict = {}

        # comb same repo
        for k in self.search_result_dict.keys():
            maintainer, repo, tag = self._split_key(k)
            semver = SemverItem()
            if semver.load(tag) is True:
                repo_id = "{}${}${}".format(maintainer, repo, semver.major)
                if repo_id in repo_dict:
                    if semver.compare(repo_dict[repo_id]) > 0:
                        repo_dict[repo_id] = tag
                else:
                    repo_dict[repo_id] = tag
            else:
                repo_id = "{}${}$".format(maintainer, repo)
                if repo_id in repo_dict:
                    if tag > repo_dict[repo_id]:
                        repo_dict[repo_id] = tag
                else:
                    repo_dict[repo_id] = tag

        for repo_id, tag in repo_dict.items():
            maintainer, repo, _ = repo_id.split("$")
            key = self._gen_key(maintainer, repo, tag)
            result: PackageInfo = self.search_result_dict[key]
            if self._download_dep(result, download_dir) is False:
                logging.error("failed download: \n{}".format(result.path))
                return False

        return True

    def search_dep_item(self, dep: DepItem):
        """
        search dep's deps
        """
        k = dep.gen_key()
        if k in self.search_result_dict:
            return True

        result = self._search(dep)
        if result is None:
            logging.error("failed find dep: \n{}".format(dep))
            return False

        self.search_result_dict[k] = result
        if result.meta.build_info.fat_pkg:
            return True

        for sub_dep in result.meta.deps:
            dep_item = DepItem()
            if dep_item.load(sub_dep) is False:
                return False
            if self.search_dep_item(dep_item) is False:
                return False

        return True

    def _download_dep(
            self,
            search_result: PackageInfo,
            download_dir):
        """
        download deps
        :param search_result: search result
        :param download_dir: download directory
        :param recursive: need download dep's deps
        """
        logging.info("download dep: {}".format(
            search_result.path
        ))
        download_cfg = DownloaderConfig()
        download_cfg.repo_type = search_result.repo_type
        download_cfg.path = search_result.path
        download_cfg.dest = download_dir
        download_cfg.extract = True
        downloader = Downloader()
        return downloader.download(download_cfg)

    def _gen_key(self, maintainer, repo, tag):
        """
        gen dep repo key
        """
        return "{}${}${}".format(maintainer, repo, tag)

    def _split_key(self, k):
        """
        split dep repo key
        """
        return k.split("$")

    def _search(self, dep: DepItem) -> typing.Optional[PackageInfo]:
        """
        search dependency
        """
        search_cfg = SearcherConfig()
        search_cfg.name = dep.name
        search_cfg.maintainer = dep.maintainer
        search_cfg.tag = dep.tag
        search_cfg.system_name = self.platform.system
        search_cfg.machine = self.platform.machine

        searcher = Searcher()
        search_results = searcher.search(search_cfg)
        if len(search_results) == 0:
            return None
        elif len(search_results) == 1:
            return search_results[0]
        else:
            result_score_dict = self._rank_search_result(search_results)
            if len(result_score_dict) == 0:
                return None
            else:
                score_list = [
                    (k, v) for k, v in sorted(
                        result_score_dict.items(),
                        key=lambda item: item[1],
                        reverse=True)
                ]
                return score_list[0][0]

    def _rank_search_result(self, search_result: typing.List[PackageInfo]):
        """
        rank search result
        """
        result_score_dict = {}
        for result in search_result:
            score = 0
            meta = result.meta
            if len(meta.platform.system) > 0 and \
                    meta.platform.system != self.platform.system:
                continue
            if len(meta.platform.machine) > 0 and \
                    meta.platform.machine != self.platform.machine:
                continue
            if meta.platform.system == self.platform.system:
                score += 10
            if meta.platform.machine == self.platform.machine:
                score += 10
            if meta.platform.distr == self.platform.distr:
                score += 2
            if meta.build_info.fat_pkg is True:
                score += 2

            meta_build_type = meta.build_info.build_type.lower()
            build_type = self.build_info.build_type.lower()
            if meta_build_type == build_type:
                score += 2
            elif meta.build_info.build_type.lower() == "release":
                score += 1
            result_score_dict[result] = score
        return result_score_dict
