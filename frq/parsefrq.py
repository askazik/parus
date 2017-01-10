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
    # 1.1. Get averaged lines.
    lines = A.getAllAveragedLines()
    # 1.3. Get first reflection and searching interval of heights.
    intervals = A.adjastSearchingIntervals(lines)
    # 1.4. View averaged plots.
    axs = pplt.plotLines(
        namespace.filename,
        lines, intervals,
        A._heights, A._frqs)

    # 1.5. Get h'(t) and A(t) for all frequencies
    # We need a effective height correction.
    # Start of ADC is'nt a ground border! It is a time delay = c / dh.
    # dh = 2 * h_1 - h_2

    # 1.6. Estimation of dh between a radioimpulse sendig and the ADC start.

    # 1.7. Estimation of noise features.

    # 2. Estimation of permanent equipment (B) and effective reflection
    # coefficient (rho_g).

    # 3. Estimation of the apparent reflection coefficient.


    # Animation
    # B = pp.parusAmnimation(filepath, 2)
    # B.frqNumber = 4
    # B.start()
