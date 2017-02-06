# -*- coding: utf-8 -*-
"""
Fill a Parus database by files data from given directory.
"""
import os.path as path
import argparse
import glob

from datetime import datetime
import sqlite3

import parusFile as pf
#import parusPlot as pplt


def createParser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-d', '--directory',
        default='d:\!data\E')

    return parser


# Проверочная программа
if __name__ == '__main__':
    # 0. Get working parameters.
    parser = createParser()
    namespace = parser.parse_args()
    names = glob.glob(path.join(namespace.directory, '*.frq'))

    # Create a connection and cursor to your database
    # if file not exist - create empty database
    conn = sqlite3.connect('parus.sqlite')
    cur = conn.cursor()
    # Check of table <files> existence.
    cur.execute(
        "SELECT count(*) FROM sqlite_master "
        "WHERE type='table' AND "
        "name='files';")
    data = cur.fetchall()
    if not data[0][0]:
        raise ValueError('Database is empty or corrupted.')
    # In sqlite3 foreign key constraints are disabled by default
    # for performance reasons. PRAGMA statement enables them.
    cur.execute("PRAGMA foreign_keys = ON")
    for name in names:
        # 1. Parsing data and collect information.
        print(name)
        A = pf.parusFile(name)
        A_m, A_s, h_m, h_s, ampls, hs = A.calculate()

        # 2. Save results in sqlite Database.
        # Insert file
        ftime = datetime(*A.time[:6])
        cur.execute(
            'insert into files '
            '(filename, time, dt, dh) values (?,?,?,?)', (
            A.name,
            ftime,
            A.dt,
            A._heights[1] - A._heights[0]))
        # The python module puts the last row id inserted into
        # a variable on the cursor
        file_id = cur.lastrowid
        # Insert frequencies
        cur.execute(
        """INSERT INTO frequencies VALUES(NULL, 'spot')""")
        frq_id = cur.lastrowid
        # Insert amplitude
        cur.execute(
        """INSERT INTO amplitudes VALUES(?, ?)""",
            (bobby_id, spot_id));
        # Commit
        conn.commit()
        print('Well done. Try next file.')

    conn.close()
