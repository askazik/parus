# -*- coding: utf-8 -*-
"""
Fill a Parus database by files data from given directory.
"""
import os.path as path
import argparse
import glob

from datetime import datetime
import numpy as np
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
        "name='files'")
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

        # 2. Save results in sqlite Database.
        # Fill file table.
        ftime = datetime(*A.time[:6])
        cur.execute(
            'SELECT id_file FROM files WHERE filename=?', (A.name,))
        data = cur.fetchall()
        if data:  # exist
            file_id = data[0][0]
        else:  # create record
            cur.execute(
                'insert into files '
                '(filename, time, dt, dh) values (?,?,?,?)', (
                A.name, ftime, A.dt, A._heights[1] - A._heights[0]))
            file_id = cur.lastrowid

        # Fill frequencies table.
        frq_ids = []  # empty list
        i_frq = 0
        for frq in A.frqs:
            cur.execute(
                'SELECT id_frq FROM frequencies '
                'WHERE frequency=?', (np.asscalar(frq),))
            data = cur.fetchall()
            if data:  # exist
                frq_ids.append(data[0][0])
            else:  # create record
                cur.execute(
                    'INSERT INTO frequencies '
                    '(frequency) values (?)',
                    (np.asscalar(frq),))
                frq_ids.append(cur.lastrowid)
            i_frq += 1

        # Fill amplitude table.
        A_m, A_s, h_m, h_s, ampls, hs, thr = A.calculate()
        i_frq = 0
        for frq_id in frq_ids:
            cur.execute(
                'SELECT id_ampl FROM amplitudes '
                'WHERE ampl_file=? AND ampl_frq=?',
                (file_id, frq_id))
            data = cur.fetchall()
            if data:  # exist
                pass
            else:  # create record
                shape = A_m.shape
                for i_ref in range(shape[1]):  # by reflection
                    if not A_m[i_frq, i_ref]:  # is NaN
                        break;
                    cur.execute(
                        'INSERT INTO amplitudes '
                        '(ampl_file, ampl_frq, number, '
                        'ampl_m, ampl_s, heights_m, heights_s, thereshold) '
                        'VALUES(?,?,?,?,?,?,?,?)',
                        (file_id, frq_id, i_ref,
                        A_m[i_frq, i_ref], A_s[i_frq, i_ref],
                        h_m[i_frq, i_ref], h_s[i_frq, i_ref], thr[i_frq]))
            i_frq += 1  # next frq number

        # Commit
        conn.commit()
        print('Well done. Try next file.')

    conn.close()
    print('End of files list.')
