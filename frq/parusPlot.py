# -*- coding: utf-8 -*-
"""
Проверка работы с memory mapping средствами numpy.

Отладка в Emacs: (M-x pdb) -> (py -m pdb <filename>)
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

import os
from parusFile import parusFile


class parusAmnimation(parusFile):
    """Animation class for multyfrequencies data.
    """

    def __init__(self, filename, frqNum=0):
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
        self.timetext = ax.text(
            0.5, 0.5, '',
            horizontalalignment='center',
            verticalalignment='center',
            transform=ax.transAxes)
        self.line, = ax.plot(
            np.zeros(self._heights.shape[0]), self._heights)

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
        fig.canvas.set_window_title(
            'File {}, frq = {} kHz, No <{}>.'
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
        ax1.set_ylim([ymin, ymax])
        ax2.set_ylim([ymin, ymax])
        # set padding between subplots
        plt.subplots_adjust(wspace=.001)
        plt.show()

    # frqNumber property BEGIN
    def getFrqNum(self):
        return self.__frqNum

    def setFrqNum(self, value):
        # set canvas title
        path, fname = os.path.split(self._file.name)
        self.fig.canvas.set_window_title(
            'File {}, frq = {} kHz.'
            .format(fname, self._frqs[value]))
        self.__frqNum = value

    def delFrqNum(self):
        del self.__frqNum

    frqNumber = property(
        getFrqNum, setFrqNum, delFrqNum,
        "Number of the current frequency for one-frequencies working.")
    # frqNumber property END

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
        self.anim = animation.FuncAnimation(
            self.fig, self.animate, init_func=self.init,
            frames=self._units, interval=1,
            blit=True, repeat=False)
        plt.show()
