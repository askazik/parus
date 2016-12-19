# -*- coding: utf-8 -*-
"""
Проверка работы с memory mapping средствами numpy.

Отладка в Emacs: (M-x pdb) -> (py -m pdb <filename>)
"""
import sys
import numpy as np
import os.path as path
import time

class headerFrq:
    "Класс, содержащий данные заголовка файла."
    def __init__(self, file):
        self.__file = file
        self.getHeader()

#% ===================================================================

    def getHeader(self):
        """Извлечение данных зондирования из заголовка файла."""

        self.__file.seek(0, 0)
        # Распакуем структуру данных из заголовка файла.
        _dtype = np.dtype([('ver', 'I'), # номер версии
                       ('time', # GMT время получения зондирования
                            [('sec','i'), # seconds after the minute  0-60*
                            ('min','i'), # minutes after the hour	0-59
                            ('hour','i'), # hours since midnight	0-23
                            ('mday','i'), # day of the month	1-31
                            ('mon','i'), # months since January	0-11
                            ('year','i'), # years since 1900
                            ('wday','i'), # days since Sunday	0-6
                            ('yday','i'), # days since January 1	0-365
                            ('isdst','i')]), # Daylight Saving Time flag
                        ('height_min', 'I'), # начальная высота, км (всё, что ниже при обработке отбрасывается)
                        ('height_max', 'I'), # конечная высота, км (всё, что выше при обработке отбрасывается)
                        ('height_step', 'I'), # шаг по высоте, м (реальный шаг, вычисленный по частоте АЦП)
                        ('count_height', 'I'), # число высот (размер исходного буфера АЦП при зондировании, fifo нашего АЦП 4Кб. Т.е. не больше 1024 отсчётов для двух квадратурных каналов)
                        ('count_modules', 'I'), # количество модулей/частот зондирования
                        ('pulse_frq','I')]) # частота зондирующих импульсов, Гц
        self.__header = np.fromfile(self.__file, _dtype, count=1)
        t = self.__header['time']
        tt = (t['year'][0], t['mon'][0], t['mday'][0],
                t['hour'][0], t['min'][0], t['sec'][0],
                t['wday'][0], t['yday'][0], t['isdst'][0])
        self.__time = time.struct_time(tt)
        # Считываем частоты зондирования, Гц
        count_modules = self.__header['count_modules'][0]
        self.__frqs = np.fromfile(self.__file,
                                      np.dtype(np.uint32),
                                      count_modules)
        self.__datapos = self.__file.tell()

class parusFrq(np.memmap):
    "Класс для работы с данными многочастотных измерений амплитуд."
    __dtype = dtype=np.int16
    __shape = (0,0)

    def __init__(self, filename):
        self.__file = self.existFile(filename)
        self.__header = headerFrq(self.__file)
        super().__init__(self.__file,
                        dtype = self.__dtype,
                        mode = 'r',
                        shape = self.__shape)

    def existFile(self, fname):
        """Проверка существования файла. Input: fname - полный путь к файлу."""

        s = 'The file <' + fname
        try:
            file = open(fname, 'rb')
        except IOError as e:
            print(s + '> missing or did you misspell his name!')
            sys.exit()

        return file


# Проверочная программа
if __name__ == '__main__':
    filepath = path.join('D:\!data\E', '20161208053100.frq')
    A = parusFrq(filepath)

#Data = np.memmap(filepath, dtype=np.int16, mode='r', shape=(2000,2000))
