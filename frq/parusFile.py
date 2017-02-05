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

        count_modules, = self._header['count_modules']
        self._dt, = count_modules / self._header['pulse_frq']
        t = self._header['time']
        tt = (
            t['year'][0]+1900, t['mon'][0]+1, t['mday'][0],
            t['hour'][0], t['min'][0], t['sec'][0],
            t['wday'][0], t['yday'][0], t['isdst'][0])
        self._time = time.struct_time(tt)
        # Reading of sounding frequencies, Hz
        self._frqs = np.fromfile(
            self._file,
            np.dtype(np.uint32),
            count_modules)
        self._datapos = self._file.tell()
        self._heights = self.getHeights()

    # property BEGIN
    @property
    def name(self):
        head, tail = os.path.split(self._file.name)
        return tail

    @property
    def dt(self):
        return self._dt

    @property
    def time(self):
        return self._time

    @property
    def frqs(self):
        return self._frqs
    # property END

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


class parusIntervals(object):
    """Class for define of heights intervals."""

    def __init__(self, nfrq=5, nref=4, dh=30, h1=90):
        """Init data unit.

        Keyword arguments:
        nfrq -- number of frequencies;
        nref -- number of reflections (height intervals for any frequency);
        dh -- heights intervals length (for all frequencies), km;
        h1 -- scalar/array of heights for the first reflection
        (for all frequencies), km.

        Example:
        I1 = pf.parusIntervals()
        I2 = pf.parusIntervals(dh=20, h1=[90, 95, 100, 105, 110])
        I2 = pf.parusIntervals(dh=20, h1=(90, 95, 100, 105, 110))
        """
        super().__init__()

        # unsupported types combination of input variables
        if (not isinstance(nfrq, int) or
            not isinstance(nref, int) or
            not isinstance(dh, (float, int))):
            raise ValueError(
                'Unsupported size combination of input variables '
                '<nfrq>, <nref>, <dh>!')

        self._intervals = np.zeros((nfrq, nref, 2))
        if isinstance(h1, (float, int)):
            # first reflectoion heights and dh are equal for all frequencies
            self.fillIntervalsForScalar(dh, h1)
        elif isinstance(h1, (list, tuple)) and len(h1) == nfrq:
            # first reflectoion heights and dh are distinct for frequencies
            self.fillIntervalsForArray(dh, h1)
        else:  # unsupported combination of input variables
            raise ValueError(
                'Unsupported dimension of the input <h1> variable!')

    # property BEGIN

    @property
    def intervals(self):
        return self._intervals

    # property END

    def fillIntervalsForArray(self, dh, h1):
        """Fill array of heights intervals for array of h1.

        Keyword argument:
        dh -- heights intervals length (for all frequencies), km;
        h1 -- array of heights for the first reflection, km.
        """
        shape = self._intervals.shape
        for i in range(shape[0]):
            for j in range(shape[1]):
                self._intervals[i, j, 0] = h1[i] * (j + 1)
                self._intervals[i, j, 1] = self._intervals[i, j, 0] + dh

    def fillIntervalsForScalar(self, dh, h1):
        """Fill array of heights intervals for scalar h1.

        Keyword argument:
        dh -- heights intervals length (for all frequencies), km;
        h1 -- height of the first reflection, km.
        """
        shape = self._intervals.shape
        for i in range(shape[0]):
            for j in range(shape[1]):
                self._intervals[i, j, 0] = h1 * (j + 1)
                self._intervals[i, j, 1] = self._intervals[i, j, 0] + dh


class parusUnit(object):
    """Class for parsing of multifrequencies unit of a data file."""

    def __init__(self, unit, heights, intervals_obj):
        """Init data unit.

        Keyword argument:
        unit -- complex array from getUnit(self, idTime), parusFile;
        heights -- heights array;
        intervals -- searching reflections only in given intervals.
        """
        super().__init__()
        self._unit = unit
        self._heights = heights
        self._intervals = intervals_obj.intervals

        # output
        seq = (
            'theresholds', 'means', 'medians', 'stds',
            'heights', 'amplitudes')
        self._parameters = dict.fromkeys(seq)

    # property BEGIN

    @property
    def parameters(self):
        shape = self._intervals.shape
        n_frqs = shape[0]
        n_refs = shape[1]

        theresholds = np.empty(n_frqs)
        theresholds[:] = np.NaN
        means = np.empty(n_frqs)
        means[:] = np.NaN
        medians = np.empty(n_frqs)
        medians[:] = np.NaN
        stds = np.empty(n_frqs)
        stds[:] = np.NaN
        heights = np.empty([n_frqs, n_refs])
        heights[:] = np.NaN
        amplitudes = np.empty([n_frqs, n_refs], dtype=complex)
        amplitudes[:] = np.NaN
        on_border = np.zeros([n_frqs, n_refs], dtype=int)
        for i in range(n_frqs):
            arr = self._unit[i, :]
            abs_arr = np.abs(arr)
            theresholds[i] = self.getThereshold(abs_arr)
            means[i] = np.mean(abs_arr)
            medians[i] = np.median(abs_arr)
            stds[i] = np.std(abs_arr)
            idxs, is_on_border = self.getReflections(
                abs_arr,
                theresholds[i],
                self._intervals[i])
            on_border[i, :] = is_on_border

            idxs_filtered = np.nonzero(idxs != -9999)[0]
            heights[i, idxs_filtered] = self._heights[idxs_filtered]
            amplitudes[i, idxs_filtered] = arr[idxs_filtered]  # complex!!!

        self._parameters['theresholds'] = theresholds
        self._parameters['means'] = means
        self._parameters['medians'] = medians
        self._parameters['stds'] = stds
        self._parameters['on_border'] = on_border
        self._parameters['heights'] = heights
        self._parameters['amplitudes'] = amplitudes

        return self._parameters

    # property END

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
        n = arrSorted.size
        Q1 = np.amin((arrSorted[n//4], arrSorted[n//4-1]))
        Q3 = np.amin((arrSorted[3*n//4], arrSorted[3*n//4-1]))
        # 2. Get interval.
        dQ = Q3 - Q1
        # 3. Get top border of outliers. Search minor outliers.
        thereshold = Q3 + 1.5 * dQ

        return thereshold

    def getReflections(self, arr, thereshold, intervals):
        """Get reflection height for input lines.

        Return indexes of reflections or NaN if no reflection.
        Return key is reflection on min(1)/max(2) interval limits.
        """

        n_refs = intervals.shape[0]
        indexes = np.empty(n_refs, dtype=np.int)
        indexes[:] = -9999  # special no-value key
        is_on_border = np.zeros(n_refs, dtype=np.int)  # best quality
        is_on_border[:] = -9999

        i_ampl = np.nonzero(arr >= thereshold)[0]
        if i_ampl.size:
            for i in range(n_refs):
                i_min = np.nonzero(
                    self._heights[i_ampl] >= intervals[i, 0])[0]
                if i_min.size:
                    i_max = i_min[0] + np.nonzero(
                        self._heights[i_min] <= intervals[i, 1])[0]
                    ind = np.argmax(arr[i_max])
                    indexes[i] = i_max[ind]

                    # get quality of finding extremum
                    if indexes[i] == i_max[0]:
                        is_on_border[i] = 1
                    elif indexes[i] == i_max[-1]:
                        is_on_border[i] = 2
                    elif i_max[-1].size == 1:
                        is_on_border[i] = 3
                    else:
                        is_on_border[i] = 0

        return indexes, is_on_border


class parusFile(header):
    """Class for reading multifrequencies data from the big file.
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

        # Simple intervals define, km
        self._intervals = parusIntervals()

    # property BEGIN
    def intervals(self):
        _intervals = self._intervals.intervals
        return _intervals

    def heights(self):
        return self._heights

    # property END

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
        unit = parusUnit(result, self._heights, self._intervals)

        return unit

    # def getUnitFrequency(self, idTime, idFrq):
    #     """Get one-frequence complex amplitudes.

    #     Keyword arguments:
    #     idTime -- time number (Unit number) from begin of sounding;
    #     idFrq -- frequency number.
    #     """
    #     raw = self._mmap[idTime, idFrq, :]
    #     # two last bytes save channel information
    #     raw_shifted = np.right_shift(raw, 2)
    #     # get complex amplitude
    #     result = np.array(raw_shifted[::2], dtype=complex)
    #     result.imag = raw_shifted[1::2]

    #     return result

    # get averaged data
    def getAveragedLine(self, idFrq):
        """Get averaged line array for a full time period for
        given sounding frequency.

        Keyword arguments:
        idFrq -- frequency number.
        """
        x = self._mmap[:, idFrq, :]
        # two last bytes save channel information
        x_s = np.right_shift(x, 2)
        # get complex amplitude
        x_c = np.array(x_s[:, ::2], dtype=complex)
        x_c.imag = x_s[:, 1::2]
        # get absolute numbers
        x_abs = np.absolute(x_c)
        # mean by all times
        x_avg = np.int16(np.mean(x_abs, axis=0))

        return x_avg

    # get averaged data
    def getAllAveragedLines(self):
        """Get averaged lines array for all frequencies for a full
        time period.
        """
        linesArray = np.zeros((self._rows//2, self._cols))
        for i in range(self._cols):
            linesArray[:, i] = self.getAveragedLine(i)

        return linesArray

    # def getReflectionHeights(self, linesArray):
    #     """Get reflection heights for input lines.
    #     """

    #     heights = list()
    #     for i in range(self._cols):
    #         thereshold = self.getThereshold(linesArray[:, i])
    #         idxs = np.nonzero(linesArray[:, i] >= thereshold)[0]
    #         if idxs.size:
    #             # get only true reflections
    #             idxs = self.reflectionsFilter(idxs)
    #             # split reflections by number
    #             r_groups = self.getGroups(idxs)

    #             j = 0
    #             frq_heights = np.zeros(len(r_groups))
    #             for i_interval in r_groups:  # cylce for reflections
    #                 ampls = linesArray[i_interval, i]
    #                 hs = self._heights[i_interval]
    #                 max_ampl_number = np.argmax(ampls)
    #                 max_ampl_height = hs[max_ampl_number]

    #                 # set height for current interval
    #                 frq_heights[j] = max_ampl_height
    #                 j += 1
    #         else:
    #             frq_heights = np.NaN  # no reflections
    #         heights.append(frq_heights)

    #     return heights

    def reflectionsFilter(self, heights_idxs):
        """Filter only true reflections intervals
        """
        idxs_out = np.array([], dtype=np.int64)  # create empty output array

        i_old = 1  # reflection number
        i_new = i_old
        h_min = self._first_min
        h_max = self._first_max
        dh = h_max - h_min
        for idx in heights_idxs:  # check input array elements
            h = self._heights[idx]
            if h >= h_min and h <= h_max:
                idxs_out = np.append(idxs_out, idx)
            elif h > h_max and i_old == i_new:
                i_new += 1

            # change reflection number
            if i_new > i_old:
                i_old = i_new
                h_min = i_old * self._first_min
                h_max = h_min + dh

        return idxs_out

    def getGroups(self, idxs):
        """Get groupped by alone reflections indexes.
        """
        i = 0
        igroups = np.empty(0, dtype=np.int64)
        for element in idxs[1:]:
            if element > idxs[i]+1:  # border
                igroups = np.append(igroups, i+1)
            i += 1

        return np.split(idxs, igroups)

    def getSearchingIntervals(self, lines):
        """Adjasting all reflections intervals for given approximation.
        Output heights and height intervals is < +/- dn >.

        Keyword arguments:
        lines -- lines array.
        """
        # get reflections heights from averaged lines
        ave_heights = self.getReflectionHeights(lines)

        # search interval = +/- 7 points !!! It's simple!
        dn = 7
        N = 4  # max 4 reflections
        intervals = np.zeros((self._cols, N, 3))
        intervals.fill(np.NaN)
        dh = dn * (self._heights[1] - self._heights[0])

        for i in range(self._cols):  # cycle for frequencies
            h_reflections = ave_heights[i]
            if not np.isnan(h_reflections) and h_reflections.size:
                # на одной из частот могут быть отражения
                for j in range(h_reflections.size):  # cycle for reflections
                    intervals[i, j, 0] = h_reflections[j]
                    intervals[i, j, 1] = intervals[i, j, 0] - dh
                    intervals[i, j, 2] = intervals[i, j, 0] + dh

        return intervals

    # def getThereshold(self, arr):
    #     """Get thereshold for np.array.

    #     Keyword arguments:
    #     idTime -- time number (Unit number) from begin of sounding;
    #     idFrq -- frequency number.
    #     """
    #     # 0. Sort given np.array.
    #     # Use representative array from number = 30 (60 km).
    #     arrSorted = np.sort(arr[30:], axis=0, kind='mergesort')
    #     # 1. Get quartiles.
    #     n = arrSorted.size
    #     Q1 = np.amin((arrSorted[n//4], arrSorted[n//4-1]))
    #     Q3 = np.amin((arrSorted[3*n//4], arrSorted[3*n//4-1]))
    #     # 2. Get interval.
    #     dQ = Q3 - Q1
    #     # 3. Get top border of outliers. Search minor outliers.
    #     thereshold = Q3 + 1.5 * dQ

    #     return thereshold

    def getMomentalReflections(self, intervals):
        """Get h'(t) and A(t) for all data.

        Keyword arguments:
        intervals -- searching intervals for reflections.
        """
        # get numbers of interval borders
        i_intervals = (np.divide(
            intervals,
            self._heights[1] - self._heights[0])).astype(int)

        # allocate fixed output arrays
        n_times = self._mmap.shape[0]
        n_reflections = intervals.shape[1]
        momentalHeights = np.zeros(
            (n_times, n_reflections, self._cols))
        momentalAmplitudes = np.zeros(
            (n_times, n_reflections, self._cols))

        # critical for file version 0 and 2 !!!
        h_base = (self._heights[0] /
                      (self._heights[1]-self._heights[0])).astype(int)
        for i in range(n_times):  # by times number
            # lines = self._mmap[i, :, :]
            unit = self.getUnit(i)
            abs_unit = np.absolute(unit)
            for j in range(n_reflections):  # by reflections
                lims = i_intervals[:, j, -2:] - h_base
                for k in range(self._cols):  # by frequencies
                    cur = abs_unit[k, lims[k, 0]: lims[k, 1]]
                    i_max = cur.argmax() + lims[k, 0]
                    momentalAmplitudes[i, j, k] = abs_unit[k, i_max]
                    momentalHeights[i, j, k] = self._heights[i_max]

        return momentalHeights, momentalAmplitudes

    def getParameters(self, hs, As):
        """Calculate parameters for given momental heights and amplitudes.

        Keyword arguments:
        hs -- momental heights of reflections;
        As -- momental amplitudes of reflections.
        """

        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # Caluculate only for two first reflections!
        # for night !!! rho_g ~ 1
        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        N = As.shape[1]  # number of reflections
        # Get h'(t) and An(t).
        A_m = np.mean(As, 0)
        A_s = np.std(As, 0)

        if N <= 1:
            rho = np.NaN
            h = hs  # if N == 1
        else:
            h = np.subtract(hs[:, 1, :], hs[:, 0, :])
            rho = 2 * A_m[1, :] / A_m[0, :]
        h_m = np.mean(h, 0)
        h_s = np.std(h, 0)

        return rho, h_m, h_s, A_m, A_s

    def calculate(self):
        """
        """
        # allocate fixed output arrays
        n_times = self._mmap.shape[0]
        shape = self._intervals.intervals.shape
        n_frqs = shape[0]
        n_refs = shape[1]
        ampls = np.ma.empty([n_times, n_frqs, n_refs])
        hs = np.ma.empty([n_times, n_frqs, n_refs])
        for i in range(n_times):  # by times number
            iUnit = self.getUnit(i)
            param = iUnit.parameters

            # use masked array for get true data
            # http://koldunov.net/?p=356
            quality = param['on_border']
            Masked_Ampl = np.ma.array(
                param['amplitudes'],
                mask=(quality != 0),
                copy=True)
            Masked_Heights = np.ma.array(
                param['heights'],
                mask=(quality != 0),
                copy=True)

            ampls[i, :, :] = Masked_Ampl
            hs[i, :, :] = Masked_Heights

        A_m = np.ma.mean(ampls, 0)
        A_s = np.ma.std(ampls, 0)
        h_m = np.ma.mean(hs, 0)
        h_s = np.ma.std(hs, 0)

        return A_m, A_s, h_m, h_s
