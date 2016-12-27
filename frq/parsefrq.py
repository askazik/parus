# -*- coding: utf-8 -*-
"""
Work with data file.
"""
import os.path as path
import argparse

import parusPlot

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
    # setup argument parsing
    parser = createParser()
    namespace = parser.parse_args()
    filepath = path.join(namespace.directory, namespace.filename)

    # A = parusFrq(filepath)
    # A.plotFrequency(2,1)
    B = parusPlot.parusAmnimation(filepath, 2)
    # B.frqNumber = 4
    B.start()
