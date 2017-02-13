# -*- coding: utf-8 -*-
import sys
import argparse
import os
import numpy
import matplotlib.pyplot as plt

from pylab import *
from struct import *

import pdb

# =============================================================================
def createParser ():
    """Создание парсера командной строки."""
    parser = argparse.ArgumentParser()
    lastfile = getLastFile()
    parser.add_argument ('name', nargs='?', default=lastfile)

    return parser

# =============================================================================
def getLastFile():
    """Возвращает имя последнего записанного файла ионограмм."""
    # Фильтруем список на вхождение файлов ионограмм
    files = filter(
        lambda x: x.startswith('20') and x.endswith('.ion'),
        os.listdir('.'))
    full_list = [os.path.join('.', i) for i in files]
    time_sorted_list = sorted(full_list, key = os.path.getmtime)

    lastfile = time_sorted_list[-1]

    return lastfile

# =============================================================================
def getDateFromName(fname):
    """Возвращает дату и время начала выборки из файла в виде
    строки формата "YYYY-mm-dd HH:MM:SS".

    Аргументы:
    fname - имя файла ионограммы.
    """
    fname = os.path.basename(fname.upper())

    #import pdb; pdb.set_trace()
    # Выделим год
    tm_year = int(fname[0:4])
    # Выделим месяц
    tm_month = int(fname[4:6])
    # Выделим день
    tm_mday = int(fname[6:8])
    # Выделим час
    tm_hour = int(fname[8:10])
    # Выделим минуту
    tm_min = int(fname[10:12])
    # Выделим десятки секунд
    tm_sec = int(fname[12:14])

    tmp_datetime = datetime.datetime(tm_year,
                                     tm_month,
                                     tm_mday,
                                     tm_hour,
                                     tm_min,
                                     tm_sec)
    curtime = tmp_datetime.strftime("%Y-%m-%d %H:%M:%S")
    return curtime

# =============================================================================
def readDataFile(fname):
    """Возвращает параметры и данные из файла ионограммы в виде
    словаря с ключами 'params' и 'data'.

    Аргументы:
    fname - имя файла ионограммы.
    """

    # Open a data file.
    with open(fname, 'rb') as fid:
        properties = readFileHeader(fid)
        count_height = properties['count_height']
        count_freq = properties['count_freq']
        data = numpy.zeros((count_height,count_freq), dtype=numpy.uint8)
        frqs = numpy.zeros(count_freq, dtype=numpy.int)
        i = 0
        while True:
            headerLine = readFrequencyHeader(fid)
            if not headerLine:
                break
            line = readLine(fid, properties, headerLine)
            tmp = line['line']
            data[:,i] = tmp
            frqs[i] = line['frequency']
            i = i + 1

        # data = fid.read()
        # a = numpy.frombuffer(data, numpy.dtype(numpy.int16))
        # aa = numpy.right_shift(a,2)
        # c = numpy.array(aa[::2])+1j*numpy.array(aa[1::2])
        # d = numpy.absolute(c)
        # data = numpy.transpose(numpy.reshape(
        #     d,(properties['ks'],properties['count'])))

    return {'params':properties, 'data':data, 'frqs':frqs }

# =============================================================================
def readFileHeader(fid):
    """Возвращает заголовок файла ионограммы в виде
    словаря с ключами параметров.

    Аргументы:
    fid - дескриптор открытого файла ионограммы.
    """

# =========================================================================
#  === Заголовок файла ионограмм ===
# =========================================================================
# unsigned ver; // номер версии
# struct tm time_sound; // GMT время получения ионограммы
# unsigned height_min; // начальная высота, м
# unsigned height_step; // шаг по высоте, м
# unsigned count_height; // число высот
# unsigned switch_frequency; // частота переключения антенн ионозонда
# unsigned freq_min; // начальная частота, кГц (первого модуля)
# unsigned freq_max; // конечная частота, кГц (последнего модуля)
# unsigned count_freq; // число частот во всех модулях
# unsigned count_modules; // количество модулей зондирования
#
# struct tm
# tm_sec	int	seconds after the minute	0-61*
# tm_min	int	minutes after the hour	0-59
# tm_hour	int	hours since midnight	0-23
# tm_mday	int	day of the month	1-31
# tm_mon	int	months since January	0-11
# tm_year	int	years since 1900
# tm_wday	int	days since Sunday	0-6
# tm_yday	int	days since January 1	0-365
# tm_isdst	int	Daylight Saving Time flag
# =========================================================================
    format1 = "=I 9i 8I" # struct description
    params = fid.read(calcsize(format1))
    properties = unpack(format1, params)
    keys = ('ver',
            'tm_sec','tm_min','tm_hour',
            'tm_mday','tm_mon','tm_year',
            'tm_wday','tm_yday','tm_isdst',
            'height_min','height_step','count_height',
            'switch_frequency',
            'freq_min','freq_max','count_freq',
            'count_modules')
    properties = dict(zip(keys,properties))

    return properties

# =============================================================================
def readFrequencyHeader(fid):
    """Возвращает заголовок частотной строки ионограммы в виде
    словаря с ключами параметров.

    Аргументы:
    fid - дескриптор открытого файла ионограммы.
    """

# =========================================================================
#  === Заголовок частотной строки ионограмм ===
# =========================================================================
# Каждая строка начинается с заголовка следующей структуры
# struct FrequencyData {
#     unsigned short frequency; //!< Частота зондирования, [кГц].
#     unsigned short gain_control; // !< Значение ослабления входного аттенюатора дБ.
#     unsigned short pulse_time; //!< Время зондирования на одной частоте, [мс].
#     unsigned char pulse_length; //!< Длительность зондирующего импульса, [мкc].
#     unsigned char band; //!< Полоса сигнала, [кГц].
#     unsigned char type; //!< Вид модуляции (0 - гладкий импульс, 1 - ФКМ).
#     unsigned char threshold_o; //!< Порог амплитуды обыкновенной волны, ниже которого отклики не будут записываться в файл, [Дб/ед. АЦП].
#     unsigned char threshold_x; //!< Порог амплитуды необыкновенной волны, ниже которого отклики не будут записываться в файл, [Дб/ед. АЦП].
#     unsigned char count_o; //!< Число сигналов компоненты O.
#     unsigned char count_x; //!< Число сигналов компоненты X.
# };
    format1 = "=3H 7B" # struct description
    params = fid.read(calcsize(format1))
    #if params != '':
    if len(params):
        properties = unpack(format1, params)
        keys = ('frequency','gain_control','pulse_time',
                'pulse_length','band','type',
                'thereshold_o','thereshold_x',
                'count_o','count_x')
        header = dict(zip(keys,properties))
    else:
        header = None

    return header

# =============================================================================
def readOutlierHeader(fid):
    """Возвращает заголовок выброса в строке ионограммы в виде
    словаря с ключами параметров.

    Аргументы:
    fid - дескриптор открытого файла ионограммы.
    """

# =========================================================================
#  === Заголовок выброса ===
# =========================================================================
# struct SignalResponse {
#     unsigned long height_begin; //!< начальная высота, [м]
#     unsigned short count_samples; //!< Число дискретов
# };

    format1 = "=L H" # struct description
    params = fid.read(calcsize(format1))
    properties = unpack(format1, params)
    keys = ('height_begin','count_samples')
    header = dict(zip(keys,properties))

    return header

# =============================================================================
def readLine(fid, headerIonogram, headerLine):
    """Возвращает распакованную строку ионограммы для заданной частоты.

    Аргументы:
    fid - дескриптор открытого файла ионограммы,
    headerIonogram - заголовок ионограммы,
    headerLine - заголовок текущей частотной линии.
    """

    # параметры текущей линии
    frequency = headerLine['frequency']
    count_o = headerLine['count_o']
    thereshold_o = headerLine['thereshold_o']
    # параметры ионограммы
    count_height = headerIonogram['count_height']
    dh = headerIonogram['height_step']
    h0 = headerIonogram['height_min']
    # инициализируем чистую линию без всплесков
    line = numpy.zeros(count_height, numpy.uint8)
    # перебор по всплескам
    for i in range(count_o):
        headerOutlier = readOutlierHeader(fid)
        # начальный номер текущего всплеска
        ind = (headerOutlier['height_begin'] - h0)//dh
        for j in range(headerOutlier['count_samples']):
            x = ord(fid.read(1))
            line[ind+j] = x

    dictLine = {'frequency':frequency,
                'thereshold':thereshold_o,
                'line':line
                }
    return dictLine

# =============================================================================
# Основная программа
if __name__ == '__main__':
    parser = createParser()
    namespace = parser.parse_args()

    fname = namespace.name
    strtime = getDateFromName(fname)

    out = readDataFile(fname)
    params = out['params']

    arr = out['data']
    im = plt.imshow(arr,
                    aspect='auto',
                    origin='lower',
                    extent=[params['freq_min']/1000,
                            params['freq_max']/1000,
                            params['height_min']/1000,
                            (params['count_height']-1)*params['height_step']/1000])

    plt.xlabel('f, MHz')
    plt.ylabel('h, km')
    plt.title(strtime)
    plt.grid(True)
    plt.show()
