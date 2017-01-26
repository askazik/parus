# -*- coding: utf-8 -*-
"""
Fill a Parus database by files data from given directory.
"""
import os.path as path
import argparse
import glob

import parusDB as db
import parusFile as pf
# import parusPlot as pplt


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

    d = db.parusDB()
    for name in names:
        # 1. Parsing data and collect information.
        A = pf.parusFile(name)
        # 1.1. Get averaged lines.
        lines = A.getAllAveragedLines()
        # 1.3. Get true reflections and thier searching intervals of heights.
        intervals = A.getSearchingIntervals(lines)
        # 1.4. Get h'(t) and A(t) for all frequencies for all times and
        # all true reflections.
# --------------------------------------------------------------------
# Не учитывается, что число отражений может меняться за время выборки.
# Возможно и большее и меньшее количество отражений!!!
# Ошибка вероятна!!!
# --------------------------------------------------------------------
        momentalHeights, momentalAmplitudes = A.getMomentalReflections(
            intervals)
        rho, h_m, h_s, A_m, A_s = A.getParameters(
            momentalHeights,
            momentalAmplitudes)

        # 1.5. Save results in sqlite Database.
        # d.saveResults(
        #     A.name,
        #     A.time,
        #     A.dt,
        #     A.frqs,
        #     momentalHeights, momentalAmplitudes)
    d.close()
