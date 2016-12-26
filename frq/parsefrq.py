# -*- coding: utf-8 -*-
"""
Work with data file.
"""
import os.path as path
import parusPlot


# Проверочная программа
if __name__ == '__main__':
    # filepath = path.join('d:\!data\E', '20161208053100.frq')
    filepath = path.join('d:\!data\E', '20161208053100.frq')
    # A = parusFrq(filepath)
    # A.plotFrequency(2,1)
    B = parusPlot.parusAmnimation(filepath)
    B.frqNumber = 4
    B.start()
