#
# Copyright (c) 2019, UltraDesu <ultradesu@hexor.ru>
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#     * Neither the name of the <organization> nor the
#     names of its contributors may be used to endorse or promote products
#     derived from this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY UltraDesu <ultradesu@hexor.ru> ''AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL UltraDesu <ultradesu@hexor.ru> BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
"""
.. module:: models
   :synopsis: Contains database action primitives.
.. moduleauthor:: AB <github.com/house-of-vanity>
"""

import sqlite3
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)


# class DataBase create or use existent SQLite database file. It provides 
# high-level methods for database.
class DataBase:
    """This class create or use existent SQLite database file. It provides 
    high-level methods for database."""
    def __init__(self, scheme, basefile='data.sqlite'):
        """
          Constructor creates new SQLite database if 
          it doesn't exist. Uses SQL code from file for DB init.
          :param scheme: sql filename
          :type scheme: string
          :return: None
        """
        self.scheme = ''
        self.basefile = basefile
        try:
            conn = self.connect(basefile=basefile)
        except:
            log.debug('Could not connect to DataBase.')
            return None
        with open(scheme, 'r') as scheme_sql:
            sql = scheme_sql.read()
            self.scheme = sql
            if conn is not None:
                try:
                    cursor = conn.cursor()
                    cursor.executescript(sql)
                except Exception as e:
                    log.debug(f'Could not create scheme - {e}')
            else:
                log.debug("Error! cannot create the database connection.")
        log.info('DB created.')
        self.close(conn)

    def connect(self, basefile):
        """
          Create connect object for basefile
          :param basefile: SQLite database filename
          :type basefile: string
          :return: sqlite3 connect object
        """
        log.debug("Open connection to %s" % basefile)
        return sqlite3.connect(basefile, check_same_thread=False)

    def execute(self, sql):
        """
          Execute SQL code. First of all connect to self.basefile. Close 
          connection after execution.
          :param sql: SQL code
          :type sql: string
          :return: list of response. Empty list when no rows are available.
        """
        conn = self.connect(basefile=self.basefile)
        log.debug("Executing: %s" % sql)
        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()
        result = cursor.fetchall()
        self.close(conn)
        return result

    def add_patch(self, patch):
        sql = f"INSERT OR IGNORE INTO patches('version')  VALUES ('{patch}')"
        self.execute(sql)
        return True

    def add_hero(self, hero):
        hero = hero.replace("'", "''")
        sql = f"INSERT OR IGNORE INTO heroes('name')  VALUES ('{hero}')"
        self.execute(sql)
        return True

    def add_item(self, item):
        item = item.replace("'", "''")
        sql = f"INSERT OR IGNORE INTO items('name')  VALUES ('{item}')"
        self.execute(sql)
        return True

    def add_general_changes(self,
            patch,
            info):
        info = info.replace("'", "''")
        patch_id = self.get_patch_id(patch)
        sql = f"""INSERT OR IGNORE INTO 
        general_changes('patch', 'info')  
        VALUES (
            '{patch_id}', 
            '{info}')"""
        self.execute(sql)
        return True

    def add_item_changes(self,
            patch,
            item,
            info):
        item = item.replace("'", "''")
        info = info.replace("'", "''")
        item_id = self.get_item_id(item)
        patch_id = self.get_patch_id(patch)
        sql = f"""INSERT OR IGNORE INTO 
        item_changes('patch', 'item', 'info')  
        VALUES (
            '{patch_id}', 
            '{item_id}', 
            '{info}')"""
        self.execute(sql)
        return True

    def add_hero_changes(self,
            change_type,
            patch,
            hero,
            info,
            meta=None):
        hero = hero.replace("'", "''")
        info = info.replace("'", "''")
        if meta:
            meta = meta.replace("'", "''")
        hero_id = self.get_hero_id(hero)
        patch_id = self.get_patch_id(patch)
        sql = f"""INSERT OR IGNORE INTO 
        hero_changes('type', 'patch', 'hero', 'info', 'meta')  
        VALUES (
            '{change_type}', 
            '{patch_id}', 
            '{hero_id}', 
            '{info}', 
            '{meta}')"""
        self.execute(sql)
        return True

    def get_patch_id(self, patch):
        sql = f"SELECT rowid FROM patches WHERE version = '{patch}'"
        ret = self.execute(sql)
        return ret[0][0]

    def get_item_id(self, item):
        sql = f"SELECT rowid FROM items WHERE name = '{item}'"
        ret = self.execute(sql)
        return ret[0][0]

    def get_hero_id(self, hero):
        sql = f"SELECT rowid FROM heroes WHERE name = '{hero}'"
        ret = self.execute(sql)
        return ret[0][0]

    def get_items_list(self):
        sql = f"SELECT name FROM items"
        ret = self.execute(sql)
        items = list()
        for item in ret:
          items.append(item[0])
        return items

    def get_heroes_list(self):
        sql = f"SELECT name FROM heroes"
        ret = self.execute(sql)
        heroes = list()
        for hero in ret:
          heroes.append(hero[0])
        return heroes

    def get_patch_list(self):
        sql = f"SELECT version FROM patches"
        ret = self.execute(sql)
        patches = list()
        for patch in ret:
          patches.append(patch[0])
        return patches

    def get_general_history(self, patch):
        patch = patch.replace("'", "''")
        patch = self.get_patch_id(patch)
        sql = f"""SELECT gc.info FROM general_changes gc
        LEFT JOIN patches p on p.ROWID = gc.patch
        WHERE gc.patch = '{patch}'"""
        return self.execute(sql)

    def get_hero_history(self, hero):
        hero = hero.replace("'", "''")
        hero = self.get_hero_id(hero)
        sql = f"""SELECT p.version, a.type, a.info, a.meta FROM 
        patches p
        LEFT JOIN (
                SELECT p.version, hc.type, hc.info, hc.meta FROM `heroes` h
                LEFT JOIN hero_changes hc ON hc.hero = h.ROWID
                LEFT JOIN patches p ON hc.patch = p.ROWID
                WHERE hc.hero = {hero}
        ) a ON p.version = a.version
        ORDER BY p.rowid DESC;"""
        return self.execute(sql)

    def get_item_history(self, item):
        item = item.replace("'", "''")
        item = self.get_item_id(item)
        sql = f"""SELECT p.version, a.info FROM 
        patches p
        LEFT JOIN (
                SELECT p.version, ic.info FROM item_changes ic 
                LEFT JOIN patches p ON p.rowid = ic.patch
                WHERE ic.item = {item}
        ) a ON p.version = a.version
        ORDER BY p.rowid DESC"""
        return self.execute(sql)

    def close(self, conn):
        """
          Close connection object instance.
          :param conn: sqlite3 connection object
          :type conn: object
          :return: None
        """
        log.debug("Close connection to %s" % self.basefile)
        conn.close()

