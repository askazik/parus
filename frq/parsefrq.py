# -*- coding: utf-8 -*-
"""
Work with data file.
"""
import os.path as path
import argparse

import parusPlot as pplt
import parusFile as pfl

def createParser():
    parser = argparse.ArgumentParser()
    parser.add_argument (
        '-d', '--directory',
        default='d:\!data\E')
    parser.add_argument (
        '-f', '--filename',
        default='20161208053100.frq')
    parser.add_argument (
        '-z', '--height',
        default=100) # effective height in km for first reflection

    return parser

# Проверочная программа
if __name__ == '__main__':
    # 0. Get working parameters.
    parser = createParser()
    namespace = parser.parse_args()
    filepath = path.join(namespace.directory, namespace.filename)
    height = namespace.height

    # 1. Parsing data and collect information.
    A = pfl.parusFile(filepath)
    avgLines = A.getAllAveragedLines()
    pplt.plotLines(namespace.filename, avgLines, A._heights, A._frqs)

    # Animation
    # B = pp.parusAmnimation(filepath, 2)
    # B.frqNumber = 4
    # B.start()
