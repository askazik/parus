# -*- coding: utf-8 -*-
"""
Calculate B * rho_g and fill database.
"""
import numpy as np
import sqlite3
import math


# Расчет ослабления по двум отражениям.
# Занесение результатов в БД для второго отражения.
if __name__ == '__main__':

    # Create a connection and cursor to your database
    # if file not exist - create empty database
    conn = sqlite3.connect('parus_old.sqlite')
    cur = conn.cursor()
    # Номера файлов и частот для которых найдены два первых отражения.
    # amplitudes.n_sigma > 0 - условие на корректность данных
    cur.execute(
        "SELECT ampl_file, ampl_frq "
        "FROM amplitudes "
        "WHERE "
        "amplitudes.number == 1 AND amplitudes.n_sigma > 0")
    data = cur.fetchall()
    if not data[0][0]:
        raise ValueError('Database is empty or corrupted.')

    for item in data:  # cycle for file and frequency paar
        cur.execute(
            "SELECT ampl_m, n_sigma, ampl_s, height "
            "FROM amplitudes WHERE "
            "ampl_file == ? AND ampl_frq == ?",
            (item[0], item[1]))
        tmp = cur.fetchall()

        A1 = math.sqrt(tmp[0][2]**2 + tmp[0][0]**2 - tmp[0][1]**2)
        A2 = math.sqrt(tmp[1][2]**2 + tmp[1][0]**2 - tmp[1][1]**2)
        H = tmp[1][3] - tmp[0][3]
        B = 2 * A2 / (H * A1**2)
        L = 20 * math.log10(2 * A2 / A1)

        # Fill amplitude table.
        cur.execute(
            'UPDATE amplitudes '
            'SET L = ?, B = ?, H = ? '
            'WHERE ampl_file = ? AND ampl_frq = ? AND number = 1',
            (L, B, H, item[0], item[1]))
        L1 = 20 * math.log10( A1 * H * B )
        cur.execute(
            'UPDATE amplitudes '
            'SET L = ? '
            'WHERE ampl_file = ? AND ampl_frq = ? AND number = 0',
            (L1, item[0], item[1]))

        # Commit
        conn.commit()

    conn.close()
