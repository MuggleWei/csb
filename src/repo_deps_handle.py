import logging
import typing
from downloader import Downloader, DownloaderConfig
from searcher import Searcher, SearcherConfig, SearcherResult
from settings_handle import SettingsHandle


class RepoDepsHandle:
    """
    handle repository dependencies
    """

    def __init__(self):
        self.settings_handle: SettingsHandle | None = None
        self.platform_name = ""
        self.platform_machine = ""
        self.platform_distr = ""
        self.platform_libc = ""
        self.build_type = ""

        self.raw_deps = []
        self.deps = []
        self.search_result_dict = {}

    def add(self, dep):
        """
        handle dep and dep's deps
        """
        self.raw_deps.append(dep)

    def search_all_deps(self):
        """
        search all dependencies
        """
        self.search_result_dict.clear()
        for dep in self.raw_deps:
            if not self._is_valid_dep(dep):
                logging.error("dep is invalid: {}".format(dep))
                return False

            k = self._gen_key(dep["maintainer"], dep["repo"], dep["tag"])
            if k in self.search_result_dict:
                continue

            result = self._search_dep(dep)
            if result is None:
                logging.error("failed find dep: {}".format(dep))
                return False

            self.deps.append({
                "maintainer": result.meta.maintainer,
                "repo": result.meta.repo,
                "tag": result.meta.tag,
                "deps": result.meta.deps,
            })

            self.search_result_dict[k] = result
            if not result.meta.is_fat_pkg:
                self._search_dep_deps(search_result=result)

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
            repo_id = "{}${}".format(maintainer, repo)
            if repo_id in repo_dict:
                if tag > repo_dict[repo_id]:
                    repo_dict[repo_id] = tag
            else:
                repo_dict[repo_id] = tag

        for repo_id, tag in repo_dict.items():
            maintainer, repo = repo_id.split("$")
            key = self._gen_key(maintainer, repo, tag)
            result: SearcherResult = self.search_result_dict[key]
            if self._download_dep(result, download_dir) is False:
                logging.error("failed download {}".format(result.path))
                return False

        return True

    def _search_dep_deps(self, search_result: SearcherResult):
        """
        search dep's deps
        """
        deps = search_result.meta.deps
        for dep in deps:
            if not self._is_valid_dep(dep):
                logging.error("dep is invalid: {}".format(dep))
                return False

            k = self._gen_key(dep["maintainer"], dep["repo"], dep["tag"])
            if k in self.search_result_dict:
                continue

            result = self._search_dep(dep)
            if result is None:
                logging.error("failed find dep: {}".format(dep))
                return False

            self.search_result_dict[k] = result
            if not result.meta.is_fat_pkg:
                self._search_dep_deps(search_result=result)
        return True

    def _download_dep(
            self,
            search_result: SearcherResult,
            download_dir):
        """
        download deps
        :param search_result: search result
        :param download_dir: download directory
        :param recursive: need download dep's deps
        """
        logging.debug("download {}".format(
            search_result.path
        ))
        download_cfg = DownloaderConfig()
        download_cfg.repo_type = search_result.repo_type
        download_cfg.path = search_result.path
        download_cfg.dest = download_dir
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

    def _search_dep(self, dep) -> SearcherResult | None:
        """
        search dependency
        """
        search_cfg = SearcherConfig()
        search_cfg.maintainer = dep["maintainer"]
        search_cfg.repo = dep["repo"]
        search_cfg.tag = dep["tag"]
        search_cfg.system_name = self.platform_name
        search_cfg.machine = self.platform_machine

        searcher = Searcher()
        search_results = searcher.search(search_cfg, self.settings_handle)
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

    def _rank_search_result(self, search_result: typing.List[SearcherResult]):
        """
        rank search result
        """
        result_score_dict = {}
        for result in search_result:
            score = 0
            meta = result.meta
            if len(meta.platform_name) > 0 and \
                    meta.platform_name != self.platform_name:
                continue
            if len(meta.platform_machine) > 0 and \
                    meta.platform_machine != self.platform_machine:
                continue
            if meta.platform_name == self.platform_name:
                score += 10
            if meta.platform_machine == self.platform_machine:
                score += 10
            if meta.platform_distro == self.platform_distr:
                score += 2
            if meta.is_fat_pkg is True:
                score += 2
            if meta.platform_libc == self.platform_libc:
                score += 2
            if meta.build_type.lower() == self.build_type.lower():
                score += 2
            elif meta.build_type.lower() == "release":
                score += 1
            result_score_dict[result] = score
        return result_score_dict

    def _is_valid_dep(self, dep):
        """
        is valid dep info
        """
        if "maintainer" not in dep:
            return False
        if "repo" not in dep:
            return False
        if "tag" not in dep:
            return False
        return True
