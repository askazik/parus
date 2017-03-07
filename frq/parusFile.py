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

    @property
    def version(self):
        return self._header['ver']
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

    def __init__(self, nfrq=5, nref=4, dh=30, h1=85):
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
    @property
    def intervals(self):
        return self._intervals.intervals

    @property
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

        return np.abs(result), result

    def getAveragedMeans(self):
        """Calculate averaged means for all frequencies.
        """
        n_times = self._mmap.shape[0]
        ave = self.getUnit(0)[0]  # initialize
        for i in range(1, n_times):  # by times number
            ave = (ave + self.getUnit(i)[0])/2

        return ave

    def getSigma(self, ave_means):
        """Calculate sigma for all heights and frequencies.
        """
        n_times = self._mmap.shape[0]
        tmp = np.zeros(ave_means.shape)
        for i in range(n_times):  # by times number
            arr = self.getUnit(i)[0]
            tmp += (arr - ave_means)**2
        sigma = np.sqrt(tmp/(n_times - 1))

        return sigma

    def getThereshold(self, arr):
        """Get thereshold for array.
        """
        # # 0. Sort given np.array.
        # arrSorted = np.sort(arr, axis=0, kind='mergesort')
        # # 1. Get quartiles.
        # n = arrSorted.size
        # Q1 = np.amin((arrSorted[n//4], arrSorted[n//4-1]))
        # Q3 = np.amin((arrSorted[3*n//4], arrSorted[3*n//4-1]))
        # # 2. Get interval.
        # dQ = Q3 - Q1
        # # 3. Get top border of outliers. Search minor outliers.
        # thereshold = Q3 + 1.5 * dQ
        thereshold = np.mean(arr) + 1.96 * np.std(arr)  # 5% below

        return thereshold

    def getTheresholds(self, full_arr):
        """Get theresholds for fullarray.
        """
        theresholds = np.empty(self._cols)
        for i in range(self._cols):
            theresholds[i] = self.getThereshold(full_arr[i, :])

        return theresholds

    def getReflectionIndex(self, i_frq, arr, thereshold):
        """Get reflection height for input line.

        Return indexes of reflections or NaN if no reflection.
        """
        intervals = self.intervals[i_frq]
        n_refs = intervals.shape[0]
        indexes = np.empty(n_refs, dtype=np.int)
        indexes[:] = -9999  # special no-value key

        i_ampl = np.nonzero(arr >= thereshold)[0]
        if i_ampl.size:
            for i in range(n_refs):
                i_min = i_ampl[np.nonzero(
                    self._heights[i_ampl] >= intervals[i, 0])[0]]
                if i_min.size:
                    i_max = i_min[np.nonzero(
                        self._heights[i_min] <= intervals[i, 1])[0]]
                    if i_max.size:
                        ind = np.argmax(arr[i_max])
                        indexes[i] = i_max[ind]
                    else:
                        break
                else:
                    break

        return indexes

    def getSimpleReflections(self, full_arr, thr, sigma):
        """Get reflections parameters for full array.
        """
        n_refs = self.intervals.shape[1]

        cur_shape = [self._cols, n_refs]
        Am = np.empty(cur_shape)
        Am[:] = np.NaN
        As = np.empty(cur_shape)
        As[:] = np.NaN
        height = np.empty(cur_shape)
        height[:] = np.NaN
        for i in range(self._cols):
            arr = full_arr[i, :]
            idxs = self.getReflectionIndex(i, arr, thr[i])
            for j in range(n_refs):
                if idxs[j] != -9999:
                    height[i, j] = self._heights[idxs[j]]
                    Am[i, j] = full_arr[i, idxs[j]]
                    As[i, j] = sigma[i, idxs[j]]
                else:  # stop for first NaN
                    break

        return Am, As, height

    def HardCalculation(self):
        """True calculation file parameters.
        """
        # Output formatting
        keys = ['A_eff', 'A_std', 'n_std', 'h_eff', 'h_std', 'L_mean', 'counts']
        results = dict.fromkeys(keys)

        n_times = self._mmap.shape[0]
        n_refs = self.intervals.shape[1]

        # Get real reflections indexes
        heights = np.empty([n_times, self._cols, n_refs])
        heights[:] = np.NaN
        # signal + noise
        s_plus_n = np.empty([n_times, self._cols, n_refs], np.complex)
        s_plus_n[:] = np.NaN
        # noise
        noise = np.empty([n_times, self._cols, n_refs], np.complex)
        noise[:] = np.NaN
        # noise
        noise_std = np.zeros([n_times, self._cols])
        for i in range(n_times):  # by times number
            arr_abs, arr_c = self.getUnit(i)
            thr = self.getTheresholds(arr_abs)

            for j in range(self._cols):  # by frequencies
                # get indexes for reflections
                idxs = self.applyIntervalsAndTheresholds(
                    self.intervals[j], thr[j], arr_abs[j, :])
                i_in = np.extract(idxs > 0, idxs)
                i_to = np.nonzero(idxs > 0)[0]

                s_plus_n[i, j, i_to] = arr_c[j, i_in]
                noise[i, j, :] = arr_c[j, -1]  # last point of heights

                heights[i, j, i_to] = self._heights[i_in]

                noise_std[i, j] = np.std(arr_c[j, -1])

        s_n_2 = np.nanmean(np.abs(s_plus_n)**2, 0)
        n_2 = np.mean(np.abs(noise)**2, 0)

        results['A_eff'] = np.sqrt( s_n_2 - n_2 )
        results['A_std'] = np.nanstd(np.abs(s_plus_n), 0)

        results['n_std'] = np.nanstd(np.abs(noise), 0)
        results['h_eff'] = np.nanmean(heights, 0)
        results['h_std'] = np.nanstd(heights, 0)

        # Calculate of instant absorbtion
        rho = np.empty([n_times, self._cols])
        rho[:] = np.NaN
        counts = np.zeros(self._cols)
        for i in range(self._cols):  # by frequencies
            i_times = np.nonzero(~np.isnan(np.real(s_plus_n[:,i,1])))[0]
            n_std = noise_std[i_times, i]
            counts[i] = i_times.size  # number of points
            A1 = np.sqrt(
                np.abs(s_plus_n[i_times, i, 0])**2 - n_std**2)
            A2 = np.sqrt(
                np.abs(s_plus_n[i_times, i, 1])**2 - n_std**2)
            rho[i_times, i] = 2 * A2 / A1
        rho_mean = np.nanmean(rho, 0)
        L = 20 * np.log10(rho_mean)

        results['L_mean'] = L
        results['counts'] = counts

        return results

    def applyIntervalsAndTheresholds(self, intervals, thereshold, arr):
        """Get reflection height for input line.

        Return indexes of reflections or NaN if no reflection.
        """
        n_refs = intervals.shape[0]
        indexes = np.empty(n_refs, dtype=np.int)
        indexes[:] = -9999  # special no-value key

        i_ampl = np.nonzero(arr >= thereshold)[0]
        if i_ampl.size:
            for i in range(n_refs):
                i_min = i_ampl[np.nonzero(
                    self._heights[i_ampl] >= intervals[i, 0])[0]]
                if i_min.size:
                    i_max = i_min[np.nonzero(
                        self._heights[i_min] <= intervals[i, 1])[0]]
                    if i_max.size:
                        ind = np.argmax(arr[i_max])
                        indexes[i] = i_max[ind]
                    else:
                        break
                else:
                    break

        return indexes

    def SpectralCalculation(self):
        """Spectral estimation.
        """
        # Output formatting
        keys = ['signal', 'noise', 'h_eff', 'h_std']
        results = dict.fromkeys(keys)

        n_times = self._mmap.shape[0]
        n_refs = self.intervals.shape[1]

        # Get real reflections indexes
        heights = np.empty([n_times, self._cols, n_refs])
        heights[:] = np.NaN
        # signal + noise
        s_plus_n = np.empty([n_times, self._cols, n_refs], np.complex)
        s_plus_n[:] = np.NaN
        # noise
        noise = np.empty([n_times, self._cols], np.complex)
        noise[:] = np.NaN
        # noise
        noise_std = np.zeros([n_times, self._cols])
        # indexes
        indexes = np.empty([n_times, self._cols, n_refs], dtype=np.int)
        indexes[:] = -9999

        # 1. get only signal, noise = NaN
        for i in range(n_times):  # by times number
            arr_abs, arr_c = self.getUnit(i)

            noise[i, :] = arr_c[:, -1]  # last point of heights
            thr = self.getTheresholds(arr_abs)

            for j in range(self._cols):  # by frequencies
                # get indexes for reflections
                idxs = self.applyIntervalsAndTheresholds(
                    self.intervals[j], thr[j], arr_abs[j, :])
                i_in = np.extract(idxs > 0, idxs)
                i_to = np.nonzero(idxs > 0)[0]

                # s_plus_n[i, j, i_to] = arr_c[j, i_in]
                # heights[i, j, i_to] = self._heights[i_in]
                indexes[i, j, :] = idxs

        # 2. get indexes of NaN signal
        for i in range(self._cols):  # by frequencies
            for j in range(n_refs):  # by reflections
                indNotNaN, = np.nonzero(indexes[:, i, j] > 0)
                indNaN, = np.nonzero(indexes[:, i, j] < 0)
                if indNotNaN.size >= 1:
                    indMean = np.rint(np.mean(indexes[indNotNaN, i, j]))
                    indexes[indNaN, i, j] = indMean.astype(int)

        # 3. set "bad signal" rather NaN
        for i in range(n_times):  # by times number
            arr_abs, arr_c = self.getUnit(i)

            for j in range(self._cols):  # by frequencies
                idxs = indexes[i, j, :]
                s_plus_n[i, j, :] = arr_c[j, idxs]

        results['signal'] = s_plus_n
        results['noise'] = noise
        #results['h_eff'] = np.nanmean(heights, 0)
        #results['h_std'] = np.nanstd(heights, 0)

        return results
