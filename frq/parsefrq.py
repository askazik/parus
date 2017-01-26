# -*- coding: utf-8 -*-
"""
Work with data file.
"""
import os.path as path
import argparse

# import parusDB as db
import parusFile as pf
# import parusPlot as pplt


def createParser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-d', '--directory',
        default='c:\!data\E')
    parser.add_argument(
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
    # d = db.parusDB()
    # d.saveResults(
    #     A.name,
    #     A.time,
    #     A.dt,
    #     A.frqs,
    #     momentalHeights, momentalAmplitudes)
    # d.close()
