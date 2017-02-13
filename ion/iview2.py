#!/usr/bin/python
# -*- coding: cp866 -*-
# DEBUG: python -i -m pdb iview2.py
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
    """�������� ����� ��������� ��ப�."""
    parser = argparse.ArgumentParser()
    lastfile = getLastFile()
    parser.add_argument ('name', nargs='?', default=lastfile)

    return parser

# =============================================================================
def getLastFile():
    """�����頥� ��� ��᫥����� ����ᠭ���� 䠩�� �����ࠬ�."""
    # ����砥� ᯨ᮪ 䠩��� � ��६����� files
    f = os.listdir('.');
    # ������㥬 ᯨ᮪ �� �宦����� 䠩��� �����ࠬ�
    files = filter(lambda x: x.startswith('20') and x.endswith('.ion'), f);
    # �����㥬 ᯨ᮪ �� �६��� ���������
    files.sort(lambda x,y:cmp(os.path.getmtime(x),os.path.getmtime(y)))

    lastfile = files[-1]

    return lastfile

# =============================================================================
def getDateFromName(fname):
    """�����頥� ���� � �६� ��砫� �롮ન �� 䠩�� � ����
    ��ப� �ଠ� "YYYY-mm-dd HH:MM:SS".

    ��㬥���:
    fname - ��� 䠩�� �����ࠬ��.
    """
    fname = os.path.basename(fname.upper())

    #import pdb; pdb.set_trace()
    # �뤥��� ���
    tm_year = int(fname[0:4])
    # �뤥��� �����
    tm_month = int(fname[4:6])
    # �뤥��� ����
    tm_mday = int(fname[6:8])
    # �뤥��� ��
    tm_hour = int(fname[8:10])
    # �뤥��� ������
    tm_min = int(fname[10:12])
    # �뤥��� ����⪨ ᥪ㭤
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
    """�����頥� ��ࠬ���� � ����� �� 䠩�� �����ࠬ�� � ����
    ᫮���� � ���砬� 'params' � 'data'.

    ��㬥���:
    fname - ��� 䠩�� �����ࠬ��.
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
    """�����頥� ��������� 䠩�� �����ࠬ�� � ����
    ᫮���� � ���砬� ��ࠬ��஢.

    ��㬥���:
    fid - ���ਯ�� ����⮣� 䠩�� �����ࠬ��.
    """

# =========================================================================
#  === ��������� 䠩�� �����ࠬ� ===
# =========================================================================
# unsigned ver; // ����� ���ᨨ
# struct tm time_sound; // GMT �६� ����祭�� �����ࠬ��
# unsigned height_min; // ��砫쭠� ����, �
# unsigned height_step; // 蠣 �� ����, �
# unsigned count_height; // �᫮ ����
# unsigned switch_frequency; // ���� ��४��祭�� ��⥭� ���������
# unsigned freq_min; // ��砫쭠� ����, ��� (��ࢮ�� �����)
# unsigned freq_max; // ����筠� ����, ��� (��᫥����� �����)
# unsigned count_freq; // �᫮ ���� �� ��� ������
# unsigned count_modules; // ������⢮ ���㫥� �����஢����
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
    """�����頥� ��������� ���⭮� ��ப� �����ࠬ�� � ����
    ᫮���� � ���砬� ��ࠬ��஢.

    ��㬥���:
    fid - ���ਯ�� ����⮣� 䠩�� �����ࠬ��.
    """

# =========================================================================
#  === ��������� ���⭮� ��ப� �����ࠬ� ===
# =========================================================================
# ������ ��ப� ��稭����� � ��������� ᫥���饩 ��������
# struct FrequencyData {
#     unsigned short frequency; //!< ����� �����஢����, [���].
#     unsigned short gain_control; // !< ���祭�� �᫠������ �室���� ��⥭��� ��.
#     unsigned short pulse_time; //!< �६� �����஢���� �� ����� ����, [��].
#     unsigned char pulse_length; //!< ���⥫쭮��� ��������饣� ������, [��c].
#     unsigned char band; //!< ����� ᨣ����, [���].
#     unsigned char type; //!< ��� �����樨 (0 - ������� ������, 1 - ���).
#     unsigned char threshold_o; //!< ��ண �������� ��몭������� �����, ���� ���ண� �⪫��� �� ���� �����뢠���� � 䠩�, [��/��. ���].
#     unsigned char threshold_x; //!< ��ண �������� ����몭������� �����, ���� ���ண� �⪫��� �� ���� �����뢠���� � 䠩�, [��/��. ���].
#     unsigned char count_o; //!< ��᫮ ᨣ����� ���������� O.
#     unsigned char count_x; //!< ��᫮ ᨣ����� ���������� X.
# };
    format1 = "=3H 7B" # struct description
    params = fid.read(calcsize(format1))
    if params != '':
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
    """�����頥� ��������� ���� � ��ப� �����ࠬ�� � ����
    ᫮���� � ���砬� ��ࠬ��஢.

    ��㬥���:
    fid - ���ਯ�� ����⮣� 䠩�� �����ࠬ��.
    """

# =========================================================================
#  === ��������� ���� ===
# =========================================================================
# struct SignalResponse {
#     unsigned long height_begin; //!< ��砫쭠� ����, [�]
#     unsigned short count_samples; //!< ��᫮ ����⮢
# };

    format1 = "=L H" # struct description
    params = fid.read(calcsize(format1))
    properties = unpack(format1, params)
    keys = ('height_begin','count_samples')
    header = dict(zip(keys,properties))

    return header

# =============================================================================
def readLine(fid, headerIonogram, headerLine):
    """�����頥� �ᯠ�������� ��ப� �����ࠬ�� ��� �������� �����.

    ��㬥���:
    fid - ���ਯ�� ����⮣� 䠩�� �����ࠬ��,
    headerIonogram - ��������� �����ࠬ��,
    headerLine - ��������� ⥪�饩 ���⭮� �����.
    """

    # ��ࠬ���� ⥪�饩 �����
    frequency = headerLine['frequency']
    count_o = headerLine['count_o']
    thereshold_o = headerLine['thereshold_o']
    # ��ࠬ���� �����ࠬ��
    count_height = headerIonogram['count_height']
    dh = headerIonogram['height_step']
    h0 = headerIonogram['height_min']
    # ���樠�����㥬 ����� ����� ��� �ᯫ�᪮�
    line = numpy.zeros(count_height, numpy.uint8)
    # ��ॡ�� �� �ᯫ�᪠�
    for i in range(count_o):
        headerOutlier = readOutlierHeader(fid)
        # ��砫�� ����� ⥪�饣� �ᯫ�᪠
        ind = (headerOutlier['height_begin'] - h0)/dh
        for j in range(headerOutlier['count_samples']):
            x = ord(fid.read(1))
            line[ind+j] = x

    dictLine = {'frequency':frequency,
                'thereshold':thereshold_o,
                'line':line
                }
    return dictLine

# =============================================================================
# �᭮���� �ணࠬ��
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
