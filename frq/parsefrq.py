# -*- coding: utf-8 -*-
"""
Проверка работы с memory mapping средствами numpy.

Отладка в Emacs: (M-x pdb) -> (py -m pdb <filename>)
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

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
        self._dt, = 1 / self._header['pulse_frq']
        t = self._header['time']
        tt = (t['year'][0], t['mon'][0], t['mday'][0],
                t['hour'][0], t['min'][0], t['sec'][0],
                t['wday'][0], t['yday'][0], t['isdst'][0])
        self._time = time.struct_time(tt)
        # Считываем частоты зондирования, Гц
        count_modules, = self._header['count_modules']
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
            DH = h_max - h_min
            num = 1 + DH // h_step
            h1 = np.linspace(h_min, h_max, num)

            # second reflection heights
            h_min_2 = h_min * 2
            h_max_2 = h_min_2 + DH
            h2 = np.linspace(h_min_2, h_max_2, num)
            heights = np.concatenate((h1, h2), axis=0)

        elif version == 1: # full list of sounding heights
            n_heights, = self._header['count_height']
            h_max = n_heights * h_step
            heights = np.arange(0, h_max, h_step)

        else: # unsupported version
            raise ValueError('Unsupported version {} of the data file {}!'.format(version, self._file))

        return heights

class parusFrq(header):
    "Класс для работы с данными многочастотных измерений амплитуд."

    def __init__(self, filename):

        # Raise os.error if the file does not exist or is inaccessible.
        _filesize = os.path.getsize(filename)
        self._file = open(filename, 'rb')

        super().__init__(self._file)

        # Since offset is measured in bytes, it should normally be a
        # multiple of the byte-size of dtype.
        _dtype = np.int16
        _offset = self._datapos
        self._rows = 2 * self._heights.size # two quadrature np.int16
        self._cols = self._frqs.size

        unitSize =  np.dtype(_dtype).itemsize * self._rows * self._cols
        dataSize = _filesize - _offset
        self._units = dataSize // unitSize

        self._mmap =  np.memmap(self._file,
                             dtype = _dtype,
                             mode = 'r',
                             offset = _offset,
                             shape = ( self._units, self._cols, self._rows),
                             order = 'C')

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
        fig.canvas.set_window_title('File {}, frq = {} kHz, No <{}>.'
                         .format(self._file.name, self._frqs[idFrq], idTime))
        ax1 = fig.add_subplot(1, 2, 1)
        ax1.set_ylabel('Height, km')
        ax2 = fig.add_subplot(1, 2, 2)
        ax2.tick_params(axis='y', labelleft='off', labelright='on')

        for ax in fig.axes:
            ax.grid(True)

        ax1.plot(value, self._heights)
        ax1.set_xlabel('Abs. amplitude, un.')

        ax2.plot(phase, self._heights, 'green')
        ax2.set_xlabel('Phase, degr.')

        # set heights limits
        ymin = self._heights.min()
        ymax = self._heights.max()
        ax1.set_ylim([ymin,ymax])
        ax2.set_ylim([ymin,ymax])
        # set padding between subplots
        plt.subplots_adjust(wspace = .001)
        plt.show()


class parusAmnimation(parusFrq):
    """Animation class for multyfrequencies data.

    """

    def __init__(self, filename, frqNum = 0):
        super().__init__(filename)
        self.fig = plt.figure()
        self.frqNumber = frqNum

        # set axes
        ymin = self._heights.min()
        ymax = self._heights.max()
        plt.ylim(ymin, ymax)
        plt.xlim(0, 16000)
        plt.ylabel('Height, km')
        plt.xlabel('Abs. amplitude, un.')
        ax = plt.gca()

        ax.grid()
        self.timetext = ax.text(0.5, 0.5,'',
                                 horizontalalignment='center',
                                 verticalalignment='center',
                                 transform = ax.transAxes)
        self.line, = ax.plot(np.zeros(self._heights.shape[0]),
                                  self._heights)

    def getFrqNum(self):
        return self.__frqNum
    def setFrqNum(self, value):
        # set canvas title
        path, fname = os.path.split(self._file.name)
        self.fig.canvas.set_window_title('File {}, frq = {} kHz.'
                         .format(fname, self._frqs[value]))
        self.__frqNum = value
    def delFrqNum(self):
        del self.__frqNum
    frqNumber = property(getFrqNum, setFrqNum, delFrqNum,
                             "Number of the current frequency for one-frequencies working.")

    # init function.
    def init(self):
        self.animate(0)

        return self.line, self.timetext

    # draw function.  This is called sequentially
    def animate(self, i):
        data = self.getUnitFrequency(i, self.frqNumber)
        value = np.absolute(data)
        self.line.set_xdata(value)

        t = i * self._dt * self._cols / 60  # time in minits
        self.timetext.set_text('{0:8.2f}, min.'.format(t))

        return self.line, self.timetext


    def start(self):
        # call the animator.
        # blit=True means only re-draw the parts that have changed.
        self.anim = animation.FuncAnimation(self.fig,
                                                self.animate,
                                                init_func = self.init,
                                                frames = self._units,
                                                interval = 1,
                                                blit = True,
                                                repeat=False)

# Проверочная программа
if __name__ == '__main__':
    #filepath = path.join('d:\!data\E', '20161208053100.frq')
    filepath = path.join('d:\!data\E', '20161208053100.frq')
    #A = parusFrq(filepath)
    #A.plotFrequency(2,1)
    B = parusAmnimation(filepath)
    B.frqNumber = 4
    B.start()

    plt.show()
