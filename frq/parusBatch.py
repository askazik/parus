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
        default='c:\\!data\\e\\new_antenn')
    parser.add_argument(
        '-f', '--file',
        default='parus.sqlite')

    return parser


# Print iterations progress
def printProgressBar(
        iteration, total, prefix='', suffix='', decimals=1,
        length=100, fill='#'):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
    """
    percent = (
        "{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end='\r')
    # Print New Line on Complete
    if iteration == total:
        print()


# Проверочная программа
if __name__ == '__main__':
    # 0. Get working parameters.
    parser = createParser()
    namespace = parser.parse_args()
    names = glob.glob(path.join(namespace.directory, '*.frq'))

    # Create a connection and cursor to your database
    # if file not exist - create empty database
    conn = sqlite3.connect(namespace.file)
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

    i_file = 0
    n_files = len(names)
    # Initial call to print 0% progress
    printProgressBar(
        i_file, n_files,
        prefix='Progress:', suffix='Complete', length=50)
    for name in names:
        # 1. Parsing data and collect information.
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
                '(filename, time, dt, dh) values (?,?,?,?)',
                (A.name, ftime, A.dt, A._heights[1] - A._heights[0]))
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
        results = A.HardCalculation()
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
                shape = results['A_eff'].shape
                for i_ref in range(shape[1]):  # by reflection
                    if np.isnan(results['A_eff'][i_frq, i_ref]):
                        break
                    if results['A_std'][i_frq, i_ref] == 0:
                        break
                    cur.execute(
                        'INSERT INTO amplitudes '
                        '(ampl_file, ampl_frq, number, '
                        'a_eff, a_std, n_std, h_eff, h_std ) '
                        'VALUES(?,?,?,?,?,?,?,?)',
                        (file_id, frq_id, i_ref,
                        results['A_eff'][i_frq, i_ref],
                        results['A_std'][i_frq, i_ref],
                        results['n_std'][i_frq, i_ref],
                        results['h_eff'][i_frq, i_ref],
                        results['h_std'][i_frq, i_ref]))
            i_frq += 1  # next frq number

        # Commit
        conn.commit()
        # Update Progress Bar
        i_file += 1
        printProgressBar(
            i_file, n_files,
            prefix='Progress:', suffix='Complete', length=50)

    conn.close()
