# -*- coding: utf-8 -*-
"""
Work with data file. Use a spectral algorithm.
"""
import os.path as path
import argparse
import glob

from datetime import datetime
import numpy as np
import sqlite3

import parusFile as pf
import parusPlot as pplt


def createParser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-d', '--directory',
        default='c:\\!data\\E\\old_antenn\\big')
    parser.add_argument(
        '-f', '--file',
        default='parus_psd.sqlite')

    return parser


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

    for name in names:
        # 0. View reflections on every frequencies.
        #view = pplt.parusAmnimation(filepath, 1)
        #view.start()

        # 1. Get amplitudes of reflections.
        A = pf.parusFile(name)
        # ave = A.getAveragedMeans()
        # pplt.plotAveragedLines(name, A.heights, A.frqs, ave)

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
                (A.name, ftime, A.dt, A.heights[1] - A.heights[0]))
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
        results = A.SpectralCalculation()

        # 3. Plot amplitudes for two reflections.
        signals = results['signal']
        noise = results['noise']

        power0, power1, Pnoise = pplt.plotAmplitudes(
            signals[:, :, 0:2],
            A.dt,
            A.frqs,
            name,
            noise)

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
                cur.execute(
                    'INSERT INTO amplitudes '
                    '(ampl_file, ampl_frq, '
                    'power0, power1, Pnoise, '
                    'h0_eff, h0_std, h1_eff, h1_std) '
                    'VALUES(?,?,?,?,?,?,?,?,?)',
                    (file_id, frq_id,
                    power0[i_frq],
                    power1[i_frq],
                    Pnoise[i_frq],
                    results['h_eff'][i_frq, 0],
                    results['h_std'][i_frq, 0],
                    results['h_eff'][i_frq, 1],
                    results['h_std'][i_frq, 1]))

            i_frq += 1  # next frq number

        # Commit
        conn.commit()
        # Update Progress Bar
        i_file += 1

    conn.close()


# End of file.
