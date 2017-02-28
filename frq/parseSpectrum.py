# -*- coding: utf-8 -*-
"""
Work with data file. Use a spectral algorithm.
"""
import os.path as path
import argparse
import glob

import parusFile as pf
import parusPlot as pplt


def createParser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-d', '--directory',
        default='c:\\!data\\E\\new_antenn')

    return parser


# Проверочная программа
if __name__ == '__main__':
    # 0. Get working parameters.
    parser = createParser()
    namespace = parser.parse_args()
    names = glob.glob(path.join(namespace.directory, '*.frq'))

    for name in names:
        # 1. View reflections on every frequencies.
        #view = pplt.parusAmnimation(filepath, 1)
        #view.start()

        # 2. Get amplitudes of reflections.
        A = pf.parusFile(name)
        results = A.SpectralCalculation()

        # 3. Plot amplitudes for two reflections.
        signals = results['signal']
        noise = results['noise']

        pplt.plotAmplitudes(signals[:, :, 0:2], A.dt, A.frqs, name)

# End of file.
