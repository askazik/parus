# -*- coding: utf-8 -*-
"""
Classes for work with a Parus ionosound data files.
"""
import numpy as np

import time
import os


class header(object):
    "Class for work with a header of a data file."
    def __init__(self, file):
        super().__init__()
        self._file = file
        self.getHeader()

# ====================================================================

    def getHeader(self):
        """Get information from header."""

        self._file.seek(0, 0)
        # Unpack data structure from a file header.
        _dtype = np.dtype(
            [('ver', 'I'),          # version number
             ('time',               # GMT of sounding beginning.
                [('sec', 'i'),      # seconds after the minute (0-60*)
                 ('min', 'i'),      # minutes after the hour (0-59)
                 ('hour', 'i'),     # hours since midnight (0-23)
                 ('mday', 'i'),     # day of the month (1-31)
                 ('mon', 'i'),      # months since January (0-11)
                 ('year', 'i'),     # years since 1900
                 ('wday', 'i'),     # days since Sunday (0-6)
                 ('yday', 'i'),     # days since January 1 (0-365)
                 ('isdst', 'i')]),  # Daylight Saving Time flag
             ('height_min', 'I'),   # beginning height, km
             ('height_max', 'I'),   # ending height, km
             ('height_step', 'I'),  # heights step, m (real ADC step)
             ('count_height', 'I'),  # number of heights (max 512)
             ('count_modules', 'I'),  # number of modules/frequencies
             ('pulse_frq', 'I')])   # switching frequency, Hz
        self._header = np.fromfile(self._file, _dtype, count=1)
        self._dt, = 1 / self._header['pulse_frq']
        t = self._header['time']
        tt = (
            t['year'][0], t['mon'][0], t['mday'][0],
            t['hour'][0], t['min'][0], t['sec'][0],
            t['wday'][0], t['yday'][0], t['isdst'][0])
        self._time = time.struct_time(tt)
        # Reading of sounding frequencies, Hz
        count_modules, = self._header['count_modules']
        self._frqs = np.fromfile(
            self._file,
            np.dtype(np.uint32),
            count_modules)
        self._datapos = self._file.tell()
        self._heights = self.getHeights()

    def getHeights(self):
        """Forming the array of heights for real amplitudes.
        """

        version = self._header['ver']
        h_step = self._header['height_step'] / 1000  # in km
        if version == 0 or version == 2:  # stripped sounding heights
            # first reflection heights
            h_min = self._header['height_min']
            h_max = self._header['height_max']
            DH = h_max - h_min
            num = 1 + DH // h_step
            h1 = np.linspace(h_min, h_max, num)

            # second reflection heights
            h_min_2 = h_min * 2
            h_max_2 = h_min_2 + DH
            h2 = np.linspace(h_min_2, h_max_2, num)
            heights = np.concatenate((h1, h2), axis=0)

        elif version == 1:  # full list of sounding heights
            n_heights, = self._header['count_height']
            h_max = n_heights * h_step
            heights = np.arange(0, h_max, h_step)

        else:  # unsupported version
            raise ValueError(
                'Unsupported version {} of the data file {}!'.format(
                    version, self._file))

        return heights


class parusFile(header):
    """Class for reading multifrequencies data from file.
    """

    def __init__(self, filename):

        # Raise os.error if the file does not exist or is inaccessible.
        _filesize = os.path.getsize(filename)
        self._file = open(filename, 'rb')

        super().__init__(self._file)

        # Since offset is measured in bytes, it should normally be a
        # multiple of the byte-size of dtype.
        _dtype = np.int16
        _offset = self._datapos
        self._rows = 2 * self._heights.size  # two quadrature np.int16
        self._cols = self._frqs.size

        unitSize = np.dtype(_dtype).itemsize * self._rows * self._cols
        dataSize = _filesize - _offset
        self._units = dataSize // unitSize

        self._mmap = np.memmap(
            self._file,
            dtype=_dtype,
            mode='r',
            offset=_offset,
            shape=(self._units, self._cols, self._rows),
            order='C')

    def getUnit(self, idTime):
        """Get multifrequence data unit with complex amplitudes.

        Keyword arguments:
        idTime -- time number (Unit number) from begin of sounding.
        """
        raw = self._mmap[idTime, :, :]
        # two last bytes save channel information
        raw_shifted = np.right_shift(raw, 2)
        # get complex amplitude
        result = np.array(raw_shifted[:, ::2], dtype=complex)
        result.imag = raw_shifted[:, 1::2]

        return result

    def getUnitFrequency(self, idTime, idFrq):
        """Get one-frequence complex amplitudes.

        Keyword arguments:
        idTime -- time number (Unit number) from begin of sounding;
        idFrq -- frequency number.
        """
        raw = self._mmap[idTime, idFrq, :]
        # two last bytes save channel information
        raw_shifted = np.right_shift(raw, 2)
        # get complex amplitude
        result = np.array(raw_shifted[::2], dtype=complex)
        result.imag = raw_shifted[1::2]

        return result

    def getAveragedLine(self, idFrq):
        """Get averaged line array for a full time period for
        given sounding frequency.

        Keyword arguments:
        idFrq -- frequency number.
        """
        x = self._mmap[:, idFrq, :]
        avg_raw = np.int16(np.mean(x, axis=0))
        # two last bytes save channel information
        avg_shifted = np.right_shift(avg_raw, 2)
        # get complex amplitude
        avg_complex = np.array(avg_shifted[::2], dtype=complex)
        avg_complex.imag = avg_shifted[1::2]
        # get absolute numbers
        avg_abs = np.absolute(avg_complex)

        return avg_abs

    def getAllAveragedLines(self):
        """Get averaged lines array for all frequencies for a full
        time period.
        """
        linesArray = np.zeros((self._rows//2, self._cols))
        for i in range(self._cols):
            linesArray[:, i] = self.getAveragedLine(i)

        return linesArray

    def adjastReflection(self, lines):
        """Adjasting first reflection interval for given approximation.
        Output heights and haights intervals for level 3 dB.

        Keyword arguments:
        line -- averaged line,
        """
        for i in range(self._cols):
            lines[:, i] = self.getAveragedLine(i)

        return height, dh

    def getFirstHeights(self, lines):
        """Get heights for first reflections for all frequencies.

        Keyword arguments:
        lines -- lines array.
        """
        # definition of heights interval for first reflection
        _min = 80
        _max = 120

        idxs = np.where((
            (self._heights >= _min) & (self._heights <= _max)))[0]
        # fill heights
        clines = lines[idxs, :] # use constraints
        a_maxs = np.amax(clines, axis=0)
        idxs = np.where(lines == a_maxs)[0]

        return a_maxs, clines, self._heights[idxs]

    def getEffectiveHeights(self, lines):
        """Get effective heights for all frequencies. Use two first reflections.

        Keyword arguments:
        lines -- lines array.
        """
        # get first dirty reflections
        amaxs, constraint_lines, first_heights = self.getFirstHeights(lines)
        # get a possible maximum number of reflections
        n_reflections = (self._heights[-1] // first_heights.max()).astype(int)

        return h

    def adjastSearchingIntervals(self, lines):
        """Adjasting all reflections intervals for given approximation.
        Output heights and height intervals for level 10 dB.

        Keyword arguments:
        lines -- averaged lines array.
        """
        # get a possible maximum number of reflections
        amaxs, constraint_lines, first_heights = self.getFirstHeights(lines)
        n_reflections = (self._heights[-1] // first_heights.max()).astype(int)

        # a_lims = amaxs / 10**(10/20)
        a_lims = amaxs / np.sqrt(10)
        intervals = np.zeros((self._cols, n_reflections, 3))
        for i in range(self._cols): # cycle for frequencies
            # use constraint lines !!!
            i_into = np.where(constraint_lines[:,i] >= a_lims[i])[0]
            a_min = constraint_lines[i_into[0], i]
            a_max = constraint_lines[i_into[-1], i]
            i_min = np.where(lines[:,i] == a_min)
            i_max = np.where(lines[:,i] == a_max)
            d_minus = first_heights[i] - self._heights[i_min[0]]
            d_plus = self._heights[i_max[0]] - first_heights[i]
            for j in range(n_reflections): # cycle for reflections
                intervals[i,j,0] = first_heights[i]*(j+1)
                intervals[i,j,1] = intervals[i,j,0] - d_minus
                intervals[i,j,2] = intervals[i,j,0] + d_plus

        return intervals

    def getThereshold(self, arr):
        """Get thereshold for np.array.

        Keyword arguments:
        idTime -- time number (Unit number) from begin of sounding;
        idFrq -- frequency number.
        """
        # 0. Sort given np.array.
        # Use representative array from number = 30 (60 km).
        arrSorted = np.sort(arr[30:], axis=0, kind='mergesort')
        # 1. Get quartiles.
        n = arr.size
        Q1 = np.amin((arrSorted[n//4], arrSorted[n//4-1]))
        Q3 = np.amin((arrSorted[3*n//4], arrSorted[3*n//4-1]))
        # 2. Get interval.
        dQ = Q3 - Q1
        # 3. Get top border of outliers. Search minor outliers.
        thereshold = Q3 + 1.5 * dQ

        return thereshold
