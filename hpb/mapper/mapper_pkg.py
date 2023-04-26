import json
import logging
import typing
from hpb.data_type.package_info import PackageInfo
from hpb.utils.utils import Utils


class MapperPkg:
    """
    package mapper
    """

    def __init__(self):
        self.table_name = "package"
        self.qry_sqlstr = \
            "SELECT " \
            "dirpath, maintainer, name, tag, " \
            "sys, sys_release, sys_ver, machine, " \
            "distr_id, distr_ver, build_type, fat_pkg, " \
            "cc, cc_ver, cxx, cxx_ver, " \
            "libc, libc_ver " \
            "from {} ".format(self.table_name)

    def create_table(self, conn):
        """
        create table
        """
        cursor = conn.cursor()
        sqlstr = "CREATE TABLE IF NOT EXISTS {} (" \
            "dirpath TEXT NOT NULL," \
            "maintainer TEXT NOT NULL," \
            "name TEXT NOT NULL," \
            "tag TEXT NOT NULL," \
            "sys TEXT NOT NULL, " \
            "sys_release TEXT NOT NULL, " \
            "sys_ver TEXT NOT NULL, " \
            "machine TEXT NOT NULL, " \
            "distr_id TEXT NOT NULL, " \
            "distr_ver TEXT NOT NULL, " \
            "build_type TEXT NOT NULL," \
            "fat_pkg BOOLEAN NOT NULL," \
            "cc TEXT," \
            "cc_ver TEXT," \
            "cxx TEXT," \
            "cxx_ver TEXT," \
            "libc TEXT," \
            "libc_ver TEXT," \
            "update_time int)".format(self.table_name)
        cursor.execute(sqlstr)

        sqlstr = "CREATE INDEX IF NOT EXISTS idx_repo ON {} (maintainer, name, tag)".format(
            self.table_name)
        cursor.execute(sqlstr)

        sqlstr = "CREATE INDEX IF NOT EXISTS idx_path ON {} (dirpath)".format(
            self.table_name)
        cursor.execute(sqlstr)
        conn.commit()

    def query(self, conn, qry: PackageInfo) -> typing.List[PackageInfo]:
        """
        query package infos
        """
        src_info = qry.meta.source_info
        build_info = qry.meta.build_info
        plt_info = qry.meta.platform

        cond_list = []
        if len(qry.path) != 0:
            cond_list.append("dirpath='{}'".format(qry.path))
        if len(src_info.maintainer) != 0:
            cond_list.append("maintainer='{}'".format(src_info.maintainer))
        if len(src_info.name) != 0:
            cond_list.append("name='{}'".format(src_info.name))
        if len(src_info.tag) != 0:
            cond_list.append("tag='{}'".format(src_info.tag))

        if len(build_info.build_type) != 0:
            cond_list.append("build_type='{}'".format(build_info.build_type))

        if len(plt_info.system) != 0:
            cond_list.append("sys='{}'".format(plt_info.system))
        if len(plt_info.distr_id) != 0:
            cond_list.append("distr_id='{}'".format(plt_info.distr_id))
        if len(plt_info.machine) != 0:
            cond_list.append("machine='{}'".format(plt_info.machine))

        if len(cond_list) > 0:
            cond_str = " AND ".join(cond_list)
            sqlstr = self.qry_sqlstr + " WHERE {}".format(cond_str)
        else:
            sqlstr = self.qry_sqlstr

        infos = []
        cursor = conn.cursor()
        cursor.execute(sqlstr)
        for row in cursor:
            info = self._deserialize(row)
            info_dict = info.meta.get_ordered_dict()
            qry_dict = qry.meta.get_ordered_dict()
            if Utils.compare_db_cond(info_dict, qry_dict) is False:
                logging.info("ignore: {}".format(json.dumps(info.path)))
                continue
            info.repo_type = "local"
            infos.append(info)

        return infos

    def query_tags(self, conn, qry: PackageInfo) -> typing.List[str]:
        """
        query versions
        """
        src_info = qry.meta.source_info
        sqlstr = \
            "SELECT tag from {} " \
            "WHERE maintainer='{}' AND name='{}' " \
            "GROUP BY maintainer, name".format(
                self.table_name, src_info.maintainer, src_info.name
            )

        tags = []
        cursor = conn.cursor()
        cursor.execute(sqlstr)
        for row in cursor:
            tags.append(row[0])
        return tags

    def query_maintainer_repos(
            self, conn, qry: PackageInfo) -> typing.List[str]:
        """
        query maintainer's repositories
        """
        src_info = qry.meta.source_info
        sqlstr = \
            "SELECT name from {} " \
            "WHERE maintainer='{}' " \
            "GROUP BY name".format(
                self.table_name, src_info.maintainer
            )

        repos = []
        cursor = conn.cursor()
        cursor.execute(sqlstr)
        for row in cursor:
            repos.append(row[0])
        return repos

    def query_repos(
            self, conn, qry: PackageInfo) -> typing.List[str]:
        """
        query maintainer's repositories
        """
        src_info = qry.meta.source_info
        sqlstr = \
            "SELECT maintainer from {} " \
            "WHERE name='{}' " \
            "GROUP BY maintainer".format(
                self.table_name, src_info.name
            )

        maintainers = []
        cursor = conn.cursor()
        cursor.execute(sqlstr)
        for row in cursor:
            maintainers.append(row[0])
        return maintainers

    def insert(self, conn, pkg_infos: typing.List[PackageInfo]):
        """
        insert
        """
        sqlstr = \
            "INSERT INTO {} (" \
            "dirpath, maintainer, name, tag, " \
            "sys, sys_release, sys_ver, machine, " \
            "distr_id, distr_ver, build_type, fat_pkg, " \
            "cc, cc_ver, cxx, cxx_ver, " \
            "libc, libc_ver " \
            ") " \
            "VALUES (" \
            "?, ?, ?, ?, " \
            "?, ?, ?, ?, " \
            "?, ?, ?, ?, " \
            "?, ?, ?, ?, " \
            "?, ?" \
            ")" \
            "".format(self.table_name)

        rows = []
        for pkg_info in pkg_infos:
            row = self._serialize(pkg_info)
            rows.append(row)

        cursor = conn.cursor()
        cursor.executemany(sqlstr, rows)

        logging.info("insert affect row count: {}".format(cursor.rowcount))
        conn.commit()

    def remove_by_dirpath(self, conn, dirpath):
        """
        remove row by dirpath
        """
        sqlstr = \
            "DELETE FROM {} WHERE dirpath='{}'" \
            "".format(self.table_name, dirpath)

        cursor = conn.cursor()
        cursor.execute(sqlstr)

        logging.info("exec: {}, affect row count: {}".format(
            sqlstr, cursor.rowcount))
        conn.commit()

    def _deserialize(self, row):
        """
        parse table row
        """
        info = PackageInfo()

        idx = 0
        info.path = row[idx]

        # source
        idx += 1
        info.meta.source_info.maintainer = row[idx]
        idx += 1
        info.meta.source_info.name = row[idx]
        idx += 1
        info.meta.source_info.tag = row[idx]

        # platform
        idx += 1
        info.meta.platform.system = row[idx]
        idx += 1
        info.meta.platform.release = row[idx]
        idx += 1
        info.meta.platform.version = row[idx]
        idx += 1
        info.meta.platform.machine = row[idx]
        idx += 1
        info.meta.platform.distr_id = row[idx]
        idx += 1
        info.meta.platform.distr_ver = row[idx]

        # build
        idx += 1
        info.meta.build_info.build_type = row[idx]
        idx += 1
        info.meta.build_info.fat_pkg = row[idx]

        # build.compiler
        idx += 1
        info.meta.build_info.compiler_info.compiler_c = row[idx]
        idx += 1
        info.meta.build_info.compiler_info.compiler_c_ver = row[idx]
        idx += 1
        info.meta.build_info.compiler_info.compiler_cpp = row[idx]
        idx += 1
        info.meta.build_info.compiler_info.compiler_cpp_ver = row[idx]

        # build.link
        idx += 1
        info.meta.build_info.link_info.libc = row[idx]
        idx += 1
        info.meta.build_info.link_info.libc_ver = row[idx]

        return info

    def _serialize(self, pkg_info: PackageInfo):
        """
        serialize
        """
        source = pkg_info.meta.source_info
        plt = pkg_info.meta.platform
        build = pkg_info.meta.build_info
        compiler = build.compiler_info
        link = build.link_info
        return (
            pkg_info.path, source.maintainer, source.name, source.tag,
            plt.system, plt.release, plt.version, plt.machine,
            plt.distr_id, plt.distr_ver, build.build_type, build.fat_pkg,
            compiler.compiler_c, compiler.compiler_c_ver,
            compiler.compiler_cpp, compiler.compiler_cpp_ver,
            link.libc, link.libc_ver
        )
