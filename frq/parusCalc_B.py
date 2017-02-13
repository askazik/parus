# -*- coding: utf-8 -*-
"""
Calculate B * rho_g and fill database.
"""
import numpy as np
import sqlite3


# Расчет произведения постоянной аппаратуры на кажущийся коэффициент
# отражения земли (=1) и занесение результатов в БД для данной частоты.
if __name__ == '__main__':

    # Create a connection and cursor to your database
    # if file not exist - create empty database
    conn = sqlite3.connect('parus.sqlite')
    cur = conn.cursor()
    # Номера файлов и частот для которых найдены два первых отражения.
    cur.execute(
        "SELECT DISTINCT ampl_file, ampl_frq "
        "FROM amplitudes WHERE amplitudes.number == 1")
    data = cur.fetchall()
    if not data[0][0]:
        raise ValueError('Database is empty or corrupted.')

    for item in data:  # cycle for file and frequency paar
        cur.execute(
            "SELECT ampl_m, n_sigma "
            "FROM amplitudes WHERE "
            "ampl_file == ? AND ampl_frq == ?",
            (item[0], item[1]))
        tmp = cur.fetchall()

        # without noise
        B2 = 2 * (tmp[1][0]-tmp[1][1]) / (tmp[0][0]-tmp[1][1])**2
        # with noise
        B1 = 2 * tmp[1][0] / tmp[0][0]**2

        # Fill amplitude table.
        cur.execute(
            'UPDATE amplitudes '
            'SET B_with_noise = ?, B_without_noise = ? '
            'WHERE ampl_file = ? AND ampl_frq = ? AND number = 0',
            (B1, B2, item[0], item[1]))

        # Commit
        conn.commit()

    conn.close()
