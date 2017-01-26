# -*- coding: utf-8 -*-
"""
Collect frequencies for data files from given directory.
"""
import os.path as path
import argparse
import glob

import numpy as np
import parusFile as pf
# import parusPlot as pplt


def createParser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-d', '--directory',
        default='c:\!data\E')

    return parser


# Проверочная программа
if __name__ == '__main__':
    # 0. Get working parameters.
    parser = createParser()
    namespace = parser.parse_args()
    names = glob.glob(path.join(namespace.directory, '*.frq'))

    arrFrqs = np.array([], dtype=np.uint32)
    for name in names:
        # Parsing data and collect information.
        # print(name)
        A = pf.parusFile(name)
        arrFrqs = np.append(arrFrqs, A.frqs)

    frqs_unique = np.unique(arrFrqs)
    print(len(names))
    print(frqs_unique)
