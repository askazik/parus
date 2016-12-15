# -*- coding: utf-8 -*-
"""
Редактор Spyder

Проверка работы с memory mapping средствами numpy.
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

#% =========================================================================
#% Чтение заголовка файла данных.
#% !!!uint32!!!
#% struct dataHeader { 	    // === Заголовок файла данных ===
#%   unsigned ver; // номер версии
#%   struct tm time_sound; // GMT время получения зондирования
#%   unsigned height_min; // начальная высота, км (всё, что ниже при обработке отбрасывается)
#% 	unsigned height_max; // конечная высота, км (всё, что выше при обработке отбрасывается)
#%   unsigned height_step; // шаг по высоте, м (реальный шаг, вычисленный по частоте АЦП)
#%   unsigned count_height; // число высот (размер исходного буфера АЦП при зондировании, fifo нашего АЦП 4Кб. Т.е. не больше 1024 отсчётов для двух квадратурных каналов)
#%   unsigned count_modules; // количество модулей/частот зондирования
#% 	unsigned pulse_frq; // частота зондирующих импульсов, Гц
#% };
#%
#% struct tm !!!int32!!!
#% Member	Type	Meaning	Range
#% tm_sec	int	seconds after the minute	0-60*
#% tm_min	int	minutes after the hour	0-59
#% tm_hour	int	hours since midnight	0-23
#% tm_mday	int	day of the month	1-31
#% tm_mon	int	months since January	0-11
#% tm_year	int	years since 1900
#% tm_wday	int	days since Sunday	0-6
#% tm_yday	int	days since January 1	0-365
#% tm_isdst	int	Daylight Saving Time flag
#% =========================================================================
    def getHeader(self):
        """Извлечение данных зондирования из заголовка файла."""

        self.__file.seek(0, 0)
        # Распакуем структуру данных из заголовка файла.
        _dtype = np.dtype([('ver', 'I'),
                       ('time', [('sec','i'), ('min','i'), ('hour','i'), ('mday','i'), ('mon','i'), ('year','i'),
                                 ('wday','i'), ('yday','i'), ('isdst','i')]),
                       ('height_min', 'I'),
                       ('height_max', 'I'),
                       ('height_step', 'I'),
                       ('count_height', 'I'),
                       ('count_modules', 'I')])
        self.__header = np.fromfile(self.__file, _dtype, count=1)
        t = self.__header['time']
        tt = (t['year'][0], t['mon'][0], t['mday'][0], t['hour'][0], t['min'][0], 
              t['sec'][0], t['wday'][0], t['yday'][0], t['isdst'][0])
        self.__time = time.struct_time(tt)
        # Считываем частоты зондирования
        count_modules = self.__header['count_modules'][0]
        frqs = np.fromfile(self.__file, np.dtype(np.uint32), count_modules)

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
