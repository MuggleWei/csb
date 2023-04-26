import json
import logging
import sqlite3
import time
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
            "hash_val, update_ts " \
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
            "hash_val TEXT NOT NULL, " \
            "update_ts INT NOT NULL, " \
            "PRIMARY KEY(maintainer, name, tag, hash_val) " \
            ")".format(self.table_name)
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

        cond_list = []
        if len(qry.path) != 0:
            cond_list.append("dirpath='{}'".format(qry.path))
        if len(src_info.maintainer) != 0:
            cond_list.append("maintainer='{}'".format(src_info.maintainer))
        if len(src_info.name) != 0:
            cond_list.append("name='{}'".format(src_info.name))
        if len(src_info.tag) != 0:
            cond_list.append("tag='{}'".format(src_info.tag))

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
            "GROUP BY tag".format(
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
            "hash_val, update_ts" \
            ") " \
            "VALUES (" \
            "?, ?, ?, ?, " \
            "?, ?" \
            ")" \
            "".format(self.table_name)

        rows = []
        for pkg_info in pkg_infos:
            row = self._serialize(pkg_info)
            rows.append(row)

        cursor = conn.cursor()
        # insert one by one for see which one insert error
        # cursor.executemany(sqlstr, rows)
        rowcnt = 0
        errcnt = 0
        for row in rows:
            try:
                logging.info("insert row: {}".format(row))
                cursor.execute(sqlstr, row)
            except sqlite3.IntegrityError as e:
                logging.error("sqlite error: {}".format(e.args[0]))
                errcnt += 1
                continue
            rowcnt += cursor.rowcount

        logging.info("insert total affect row count: {}".format(rowcnt))
        logging.info("error insert row count: {}".format(errcnt))
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

        # hash value
        idx += 1

        # update ts
        idx += 1
        info.ts = row[idx]

        return info

    def _serialize(self, pkg_info: PackageInfo):
        """
        serialize
        """
        source = pkg_info.meta.source_info
        return (
            pkg_info.path, source.maintainer, source.name, source.tag,
            pkg_info.hash_val(), int(time.time())
        )
