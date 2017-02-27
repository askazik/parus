# -*- coding: utf-8 -*-
"""
Work with data file. Use a spectral algorithm.
"""
import os.path as path
import argparse

import parusFile as pf
import parusPlot as pplt


def createParser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-d', '--directory',
        default='c:\\!data\\E\\new_antenn')
    parser.add_argument(
        '-f', '--filename',
        default='20161208053100.frq')

    return parser


# Проверочная программа
if __name__ == '__main__':
    # 0. Get working parameters.
    parser = createParser()
    namespace = parser.parse_args()
    filepath = path.join(namespace.directory, namespace.filename)

    # 1. View reflections on every frequencies.
    view = pplt.parusAmnimation(filepath)
    view.start()

# End of file.
