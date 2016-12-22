# -*- coding: utf-8 -*-
"""
Проверка работы с memory mapping средствами numpy.

Отладка в Emacs: (M-x pdb) -> (py -m pdb <filename>)
"""
import numpy as np
import matplotlib.pyplot as plt

import os.path as path
import sys
import time
import os

class header(object):
    "Класс, содержащий данные заголовка файла."
    def __init__(self, file):
        super().__init__()
        self._file = file
        self.getHeader()

#% ===================================================================

    def getHeader(self):
        """Извлечение данных зондирования из заголовка файла."""

        self._file.seek(0, 0)
        # Распакуем структуру данных из заголовка файла.
        _dtype = np.dtype([('ver', 'I'), # номер версии
                       ('time', # GMT время получения зондирования
                            [('sec','i'), # seconds after the minute (0-60*)
                            ('min','i'), # minutes after the hour (0-59)
                            ('hour','i'), # hours since midnight (0-23)
                            ('mday','i'), # day of the month (1-31)
                            ('mon','i'), # months since January (0-11)
                            ('year','i'), # years since 1900
                            ('wday','i'), # days since Sunday (0-6)
                            ('yday','i'), # days since January 1 (0-365)
                            ('isdst','i')]), # Daylight Saving Time flag
                        ('height_min', 'I'), # начальная высота, км (всё, что ниже при обработке отбрасывается)
                        ('height_max', 'I'), # конечная высота, км (всё, что выше при обработке отбрасывается)
                        ('height_step', 'I'), # шаг по высоте, м (реальный шаг, вычисленный по частоте АЦП)
                        ('count_height', 'I'), # число высот (размер исходного буфера АЦП при зондировании, fifo нашего АЦП 4Кб. Т.е. не больше 512 отсчётов для двух квадратурных каналов)
                        ('count_modules', 'I'), # количество модулей/частот зондирования
                        ('pulse_frq','I')]) # частота зондирующих импульсов, Гц
        self._header = np.fromfile(self._file, _dtype, count=1)
        t = self._header['time']
        tt = (t['year'][0], t['mon'][0], t['mday'][0],
                t['hour'][0], t['min'][0], t['sec'][0],
                t['wday'][0], t['yday'][0], t['isdst'][0])
        self._time = time.struct_time(tt)
        # Считываем частоты зондирования, Гц
        count_modules = self._header['count_modules'][0]
        self._frqs = np.fromfile(self._file,
                                      np.dtype(np.uint32),
                                      count_modules)
        self._datapos = self._file.tell()
        self._heights = self.getHeights()

    def getHeights(self):
        """Формирование списка высот зондирования."""

        version = self._header['ver']
        h_step = self._header['height_step'] / 1000 # in km
        if version == 0 or version == 2: # stripped sounding heights
            # first reflection heights
            h_min = self._header['height_min']
            h_max = self._header['height_max']
            h1 = np.arange(h_min, h_max, h_step)

            # second reflection heights
            h_min_2 = h_min * 2
            DH = h1[-1] - h1[0]
            h_max_2 = h_min_2 + DH
            h2 = np.arange(h_min_2, h_max_2, h_step)
            heights = np.concatenate((h1, h2), axis=0)

        elif version == 1: # full list of sounding heights
            n_heights = self._header['count_height'][0]
            h_max = n_heights * h_step
            heights = np.arange(0, h_max, h_step)

        else: # unsupported version
            raise ValueError('Unsupported version {} of the data file {}!'.format(version, self._file))

        return heights

class parusFrq(header):
    "Класс для работы с данными многочастотных измерений амплитуд."

    def __init__(self, filename):
        self._file = self.openFile(filename)
        super().__init__(self._file)

        # Since offset is measured in bytes, it should normally be a
        # multiple of the byte-size of dtype.
        _dtype = np.int16
        _offset = self._datapos
        _rows = 2 * self._heights.size # two quadrature np.int16
        _cols = self._frqs.size
        _units = 32000 // _cols

        self._mmap =  np.memmap(self._file,
                             dtype = _dtype,
                             mode = 'r',
                             offset = _offset,
                             shape = ( _units, _cols, _rows),
                             order = 'C')

    def openFile(self, fname):
        """Open file with existence checking.

        Keyword arguments:
        fname -- full file path.
        """

        s = 'The file <' + fname
        try:
            file = open(fname, 'rb')
        except IOError as e:
            print(s + '> missing or did you misspell his name!')
            sys.exit()

        return file

    def getUnit(self, idTime):
        """Get multifrequence data unit with complex amplitudes.

        Keyword arguments:
        idTime -- time number (Unit number) from begin of sounding.
        """
        raw = self._mmap[idTime,:,:]
        # two last bytes save channel information
        raw_shifted = np.right_shift(raw, 2)
        # get complex amplitude
        result = np.array(raw_shifted[:, ::2], dtype = complex)
        result.imag = raw_shifted[:, 1::2]

        return result

    def getUnitFrequency(self, idTime, idFrq):
        """Get one-frequence complex amplitudes.

        Keyword arguments:
        idTime -- time number (Unit number) from begin of sounding;
        idFrq -- frequency number.
        """
        raw = self._mmap[idTime,idFrq,:]
        # two last bytes save channel information
        raw_shifted = np.right_shift(raw, 2)
        # get complex amplitude
        result = np.array(raw_shifted[::2], dtype = complex)
        result.imag = raw_shifted[1::2]

        return result

    def plotFrequency(self, idTime, idFrq):
        """Plot data for given time and frequency numbers.

        Keyword arguments:
        idTime -- time number (Unit number) from begin of sounding;
        idFrq -- frequency number.
        """

        data = self.getUnitFrequency(idTime, idFrq)
        value = np.absolute(data)
        phase = np.angle(data, deg=True)

        fig = plt.figure()
        ax1 = fig.add_subplot(2, 1, 1)
        #ax1.set_title(u'Abs. amplitude')
        ax2 = fig.add_subplot(2, 1, 2)
        #ax2.set_title(u'Phase')

        for ax in fig.axes:
            ax.set_ylabel('Height, km')
            ax.grid(True)

        ax1.plot(value, self._heights)
        ax1.set_xlabel('Abs. amplitude, un.')

        ax2.plot(phase, self._heights)
        ax2.set_xlabel('Phase, degr.')

        # ax1.title('File {}, frq = {} kHz, No <{}>.'
        #               .format(self._file.name, self._frqs[idFrq], idTime))

        plt.show()

# Проверочная программа
if __name__ == '__main__':
    filepath = path.join('h:\!data\E', '20161208053100.frq')
    #filepath = path.join('d:\!data\E', '20161107090206.frq')
    #filepath = path.join('i:\!data\E', '20161107090206.frq')
    A = parusFrq(filepath)
    A.plotFrequency(2,1)

#Data = np.memmap(filepath, dtype=np.int16, mode='r', shape=(2000,2000))
