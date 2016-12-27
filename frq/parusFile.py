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
        linesArray = np.zeros(self._rows, self._cols)
        for i in range(self._cols):
            linesArray[:, i] = self.getAveragedLine(i)

        return linesArray
