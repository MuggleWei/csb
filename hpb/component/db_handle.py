import sqlite3


class DBHandle:
    """
    local package db handle
    """

    def __init__(self, database, isolation_level=""):
        self.pkg_table_name = "package"

        self.isolation_level = isolation_level
        self.conn = sqlite3.connect(database, isolation_level=isolation_level)

        self.select_pkg_sqlstr = \
            "SELECT " \
            "dirpath, maintainer, name, tag, " \
            "sys, sys_release, sys_ver, machine_arch, " \
            "distr_id, distr_ver, build_type, fat_pkg, " \
            "cc, cc_ver, cxx, cxx_ver, " \
            "libc, libc_ver " \
            "from {} ".format(self.pkg_table_name)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.conn.close()
