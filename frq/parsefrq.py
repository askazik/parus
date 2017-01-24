# -*- coding: utf-8 -*-
"""
Work with data file.
"""
import os.path as path
import argparse

import parusDB as db
import parusFile as pf
import parusPlot as pplt

def createParser():
    parser = argparse.ArgumentParser()
    parser.add_argument (
        '-d', '--directory',
        default='c:\!data\E')
    parser.add_argument (
        '-f', '--filename',
        default='20161208050700.frq')

    return parser

# Проверочная программа
if __name__ == '__main__':
    # 0. Get working parameters.
    parser = createParser()
    namespace = parser.parse_args()
    filepath = path.join(namespace.directory, namespace.filename)

    # 1. Parsing data and collect information.
    A = pf.parusFile(filepath)
    # 1.1. Get averaged lines.
    lines = A.getAllAveragedLines()
    # 1.3. Get true reflections and thier searching intervals of heights.
    intervals = A.getSearchingIntervals(lines)
    # View averaged plots and searching intervals of true reflections.
    # axs = pplt.plotLines(
    #     namespace.filename,
    #     lines, intervals,
    #     A._heights, A._frqs)

    # 1.4. Get h'(t) and A(t) for all frequencies for all times and
    # all true reflections.
# --------------------------------------------------------------------
# Не учитывается, что число отражений может меняться за время выборки.
# Возможно и большее и меньшее количество отражений!!!
# Ошибка вероятна!!!
# --------------------------------------------------------------------
    momentalHeights, momentalAmplitudes = A.getMomentalReflections(intervals)

    # Save results in sqlite Database.
    # d = db.parusDB()
    # d.saveResults(
    #     A.name,
    #     A.time,
    #     A.dt,
    #     A.frqs,
    #     momentalHeights, momentalAmplitudes)
    # d.close()
    rho, rho_g, L, B, A1h, N = A.getAbsorption(momentalHeights, momentalAmplitudes)


    # 1.6. Estimation of dh between a radioimpulse sendig and the ADC start.
    # We need a effective height correction.
    # Start of ADC is'nt a ground border! It is a time delay = c / dh.
    # dh = 2 * h_1 - h_2

    # 1.7. Estimation of noise features.

    # 2. Estimation of permanent equipment (B) and effective reflection
    # coefficient (rho_g).

    # 3. Estimation of the apparent reflection coefficient.


    # Animation
    # B = pplt.parusAmnimation(filepath, 2)
    # B.frqNumber = 4
    # B.start()
