# -*- coding: utf-8 -*-
"""
Work with data file.
"""
import os.path as path
import argparse

import parusFile as pf
import parusPlot as pplt

def createParser():
    parser = argparse.ArgumentParser()
    parser.add_argument (
        '-d', '--directory',
        default='d:\!data\E')
    parser.add_argument (
        '-f', '--filename',
        default='20161208053100.frq')

    return parser

# Проверочная программа
if __name__ == '__main__':
    # 0. Get working parameters.
    parser = createParser()
    namespace = parser.parse_args()
    filepath = path.join(namespace.directory, namespace.filename)

    # 1. Parsing data and collect information.
    A = pf.parusFile(filepath)
    # 1.1. Plot averaged lines.
    lines = A.getAllAveragedLines()
    axs = pplt.plotLines(namespace.filename, lines, A._heights, A._frqs)
    # 1.2. Plot first reflection and searching interval of heights.
    intervals = A.adjastSearchingIntervals(lines)
    pplt.plotReflections(axs, intervals)
    # 1.3. Get h'(t) and A(t) for all frequencies

    # 1.4. Estimation of dh between a radioimpulse sendig and the ADC start.

    # 1.5. Estimation of noise features.

    # 2. Estimation of permanent equipment (B) and effective reflection
    # coefficient (rho_g).

    # 3. Estimation of the apparent reflection coefficient.


    # Animation
    # B = pp.parusAmnimation(filepath, 2)
    # B.frqNumber = 4
    # B.start()
