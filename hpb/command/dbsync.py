import getopt
import json
import logging
import os
import sys
import typing
from hpb.component.db_handle import DBHandle

from hpb.component.settings_handle import SettingsHandle
from hpb.data_type.constant_var import APP_NAME
from hpb.data_type.package_info import PackageInfo
from hpb.data_type.package_meta import PackageMeta
from hpb.mapper.mapper_pkg import MapperPkg
from hpb.utils.utils import Utils


class DbSyncConfig:
    def __init__(self):
        pass


class DbSync:
    """
    sync local db and local package directory
    """

    def __init__(self):
        self._usage_str = "Usage: {0} dbsync\n" \
            "\n" \
            "sync local db and local packages which config in settings\n" \
            "".format(APP_NAME)

    def run(self, args):
        """
        run db sync
        """
        if self._init(args=args) is False:
            return False

        # scan directories
        logging.info("# start scan local package directories")
        local_paths = self._scan_lcal_dirs()
        local_pkg_infos = self._scan_local_pkgs(local_paths)
        for info in local_pkg_infos:
            logging.info(
                "scan dir find local package: {}".format(info.path))
        logging.info("# completed scan local package directories")

        # scan db
        logging.info("# start scan local package db")
        db_path = SettingsHandle().db_path
        db_pkg_infos = self._scan_db_pkgs(db_path)
        for info in db_pkg_infos:
            logging.info(
                "scan db find local package: {}".format(info.path))
        logging.info("# completed scan local package db")

        # remove not exists path
        db_pkg_infos = self._remove_not_exists_path(db_pkg_infos)

        # add exists path
        self._add_new_path(db_pkg_infos, local_pkg_infos)

        return True

    def _add_new_path(
            self,
            db_pkg_infos: typing.List[PackageInfo],
            local_pkg_infos: typing.List[PackageInfo]):
        """
        add local path that not in db
        """
        logging.info("# start add new package info to db")
        dirpath_set = set()
        db_pkg_meta_dict = {}
        for pkg_info in db_pkg_infos:
            dirpath_set.add(pkg_info.path)
            s = json.dumps(pkg_info.meta.get_ordered_dict())
            hash_key = hash(s)
            if hash_key in db_pkg_meta_dict:
                logging.warning("hash collision: {} and {}".format(
                    pkg_info.path, db_pkg_meta_dict[hash_key]
                ))
            db_pkg_meta_dict[hash_key] = pkg_info

        new_pkg_infos: typing.List[PackageInfo] = []
        for pkg_info in local_pkg_infos:
            if pkg_info.path in dirpath_set:
                continue

            s = json.dumps(pkg_info.meta.get_ordered_dict())
            hash_key = hash(s)
            if hash_key in db_pkg_meta_dict:
                logging.warning(
                    "path not in db but meta already exists: {}".format(
                        pkg_info.path
                    ))
                continue

            logging.info("find new package in path: {}".format(pkg_info.path))
            new_pkg_infos.append(pkg_info)

        db_path = SettingsHandle().db_path
        with DBHandle(db_path, isolation_level="EXCLUSIVE") as db_handle:
            mapper_pkg = MapperPkg()
            mapper_pkg.insert(db_handle.conn, new_pkg_infos)

        logging.info("# completed add new package info to db")

    def _remove_not_exists_path(self, db_pkg_infos: typing.List[PackageInfo]):
        """
        remove already not exists path
        """
        removed_dirpaths = []
        exists_pkg_infos = []
        for info in db_pkg_infos:
            if not os.path.exists(info.path):
                removed_dirpaths.append(info.path)
            else:
                exists_pkg_infos.append(info)

        logging.info("# start remove not exists package path in db")
        db_path = SettingsHandle().db_path
        with DBHandle(db_path, isolation_level="EXCLUSIVE") as db_handle:
            for dirpath in removed_dirpaths:
                logging.info(
                    "remove not exists path from db: {}".format(dirpath))
                mapper_pkg = MapperPkg()
                mapper_pkg.remove_by_dirpath(db_handle.conn, dirpath)
        logging.info("# completed remove not exists package path in db")

        return exists_pkg_infos

    def _init_db(self):
        """
        init db
        """
        db_path = SettingsHandle().db_path
        with DBHandle(db_path, isolation_level="EXCLUSIVE") as db_handle:
            mapper_pkg = MapperPkg()
            mapper_pkg.create_table(db_handle.conn)

    def _scan_db_pkgs(self, db_path) -> typing.List[PackageInfo]:
        """
        scan local db to get package infos
        """
        db_path = SettingsHandle().db_path
        with DBHandle(db_path, isolation_level="EXCLUSIVE") as db_handle:
            qry = PackageInfo()

            mapper_pkg = MapperPkg()
            return mapper_pkg.query(db_handle.conn, qry)

    def _scan_local_pkgs(self, local_paths) -> typing.List[PackageInfo]:
        """
        scan local paths to get package infos
        """
        local_pkg_infos = []
        for path in local_paths:
            for root, _, files in os.walk(path):
                meta_name = ""
                pkg_name = ""
                multiple_err = False
                for name in files:
                    if name.endswith(".yml"):
                        if meta_name != "":
                            logging.warning(
                                "multiple meta file in {}".format(root))
                            multiple_err = True
                            break
                        meta_name = name
                    elif name.endswith(".tar.gz"):
                        if pkg_name != "":
                            logging.warning(
                                "multiple package file in {}".format(root))
                            multiple_err = True
                            break
                        pkg_name = name

                if len(meta_name) == 0 or len(pkg_name) == 0:
                    continue

                if multiple_err:
                    continue

                pkg_meta = PackageMeta()
                ret = pkg_meta.load_from_file(os.path.join(root, meta_name))
                if ret is False:
                    logging.warning("failed load meta file: {}".format(
                        os.path.join(root, meta_name)
                    ))
                    continue

                pkg_info = PackageInfo()
                pkg_info.path = root
                pkg_info.meta = pkg_meta
                local_pkg_infos.append(pkg_info)

        return local_pkg_infos

    def _scan_lcal_dirs(self) -> typing.List[str]:
        """
        scan package directories get package metas
        """
        path_list = []
        path_set = set()

        repos = []
        repos.extend(SettingsHandle().pkg_search_repos)
        repos.extend(SettingsHandle().pkg_upload_repos)

        for repo in repos:
            if repo.kind == "local":
                local_path = Utils.expand_path(repo.path)
                if local_path in path_set:
                    continue
                path_set.add(local_path)
                path_list.append(local_path)

        return path_list

    def _init(self, args):
        """
        init input arguments
        """
        cfg = self._parse_args(args=args)
        if cfg is None:
            return False

        self._init_db()

        return True

    def _parse_args(self, args) -> DbSyncConfig:
        """
        parse arguments
        """
        cfg = DbSyncConfig()
        opts, _ = getopt.getopt(
            args, "h",
            [
                "help"
            ]
        )

        for opt, _ in opts:
            if opt in ("-h", "--help"):
                print(self._usage_str)
                sys.exit(0)
        return cfg
