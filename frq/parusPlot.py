# -*- coding: utf-8 -*-
"""
Classes for graphical output of resalts.
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

import os
from parusFile import parusFile


def plotAmplitudes(ampls, dt, frqs, name, noise):
    """Plot amplitudes on subplots.

    Keyword arguments:
    ampls -- array of plotted amplitudes,
    dt -- time step (s),
    frqs -- frequencies (kHz),
    name -- file name.
    """

    power0 = np.zeros(frqs.size)
    power1 = np.zeros(frqs.size)
    Pnoise = np.zeros(frqs.size)

    # Subplots sharing both x/y axes
    shape = ampls.shape
    times = range(shape[0]) * dt / 60  # time in minutes

    fig, axs = plt.subplots(
        nrows=shape[1], ncols=1, sharex=True, sharey=True)
    fig_psd, axs_psd = plt.subplots(
        nrows=shape[1], ncols=1, sharex=True, sharey=True)

    for ax, i in zip(axs, range(shape[1])):
        ax.grid(True)
        for j in range(shape[2]):
            ax.plot(times, np.abs(ampls[:, i, j]),
                        label='{} ref.'.format(j))
        ax.plot(times, np.abs(noise[:, i]), label='noise')
    ax.set_xlabel('Time, min')

    for ax, i in zip(axs_psd, range(shape[1])):
        ax.grid(True)
        for j in range(shape[2]):
            _Pxx = ax.psd(ampls[:, i, j], 512, 1/dt, label='{} ref.'.format(j))
            if j == 0:
                power0[i] = 10 * np.log10(np.amax(_Pxx[0]))
            elif j == 1:
                power1[i] = 10 * np.log10(np.amax(_Pxx[0]))

        _Pxx = ax.psd(noise[:, i], 521, 1/dt, label='noise')
        Pnoise[i] = 10 * np.log10(np.amax(_Pxx[0]))

        ax.set_ylabel('{} kHz.'.format(frqs[i]))
        ax.legend()
    ax.set_xlabel('Frequency, Hz')

    # Fine-tune figure; make subplots close to each other and hide x
    # ticks for all but bottom plot.
    fig.canvas.set_window_title('File {}.'.format(name))
    fig.subplots_adjust(hspace=0)
    fig_psd.canvas.set_window_title('File {}.'.format(name))
    fig_psd.subplots_adjust(hspace=0)

    plt.setp([a.get_xticklabels() for a in axs[:-1]], visible=False)
    # plt.tight_layout()
    plt.show()

    print(power0)
    print(power1)
    print(Pnoise)

    return power0, power1, Pnoise

def plotLines(filename, lines, intervals, heights, frqs):
    """Plot array of lines on subplots.

    Keyword arguments:
    filename -- name of files where lines gettig from,
    lines -- array of plotted lines,
    heights -- values of heights,
    frqs -- values of frequencies.
    """

    # Subplots sharing both x/y axes
    _rows=lines.shape[1]
    n_reflections = intervals.shape[1]

    fig, axs = plt.subplots(
        nrows=_rows, ncols=1, sharex=True, sharey=True)
    for ax, i in zip(axs, range(_rows)):
        ax.grid(True)
        ax.plot(heights, lines[:,i], label='{} kHz'.format(frqs[i]))
        ax.legend()
        for j in range(n_reflections): # cycle for reflections
            xmin = intervals[i,j,1]
            xmax = intervals[i,j,2]
            ax.axvspan(xmin, xmax, facecolor='g', alpha=0.1)
            ax.axvline(intervals[i,j,0], color='r')

    ax.set_xlabel('Height, km')

    # Fine-tune figure; make subplots close to each other and hide x
    # ticks for all but bottom plot.
    fig.canvas.set_window_title('File {}.'.format(filename))
    fig.subplots_adjust(hspace=0)
    plt.setp([a.get_xticklabels() for a in axs[:-1]], visible=False)

    plt.show()

    return axs

def plotAveragedLines(filename, heights, frqs, lines, lines2):
    """Plot array of lines on subplots.

    Keyword arguments:
    filename -- name of files where lines gettig from,
    heights -- values of heights,
    frqs -- values of frequencies,
    lines -- averaged lines,
    lines2 -- square averaged lines.
    """

    # Subplots sharing both x/y axes
    n=frqs.size

    fig, axs = plt.subplots(
        nrows=1, ncols=n, sharex=True, sharey=True)
    for ax, i in zip(axs, range(n)):
        ax.grid(True)
        ax.plot(lines[i, :], heights, label='{} kHz'.format(frqs[i]))
        ax.plot(lines2[i, :], heights, label='sqrt')
        ax.legend()

    ax.set_ylabel('Height, km')

    # Fine-tune figure; make subplots close to each other and hide x
    # ticks for all but bottom plot.
    fig.canvas.set_window_title('File {}.'.format(filename))
    fig.subplots_adjust(hspace=0)
    plt.setp([a.get_xticklabels() for a in axs[:-1]], visible=False)

    plt.show()

    return axs

def plotAveragedLog10Lines(filename, heights, frqs, lines2):
    """Plot array of lines on subplots.

    Keyword arguments:
    filename -- name of files where lines gettig from,
    heights -- values of heights,
    frqs -- values of frequencies,
    lines2 -- square averaged lines.
    """

    # Subplots sharing both x/y axes
    n=frqs.size
    _ave2_log = 20*np.log10(lines2)

    fig, axs = plt.subplots(
        nrows=1, ncols=n, sharex=True, sharey=True)
    for ax, i in zip(axs, range(n)):
        ax.grid(True)
        ax.set_xlabel('dB')
        ax.set_title('{} kHz'.format(frqs[i]))
        ax.plot(_ave2_log[i, :], heights)
        if not i:
            ax.set_ylabel('Height, km')

    fig.canvas.set_window_title('File {}, amplitudes in (dB).'.format(filename))
    fig.subplots_adjust(hspace=0)

    plt.show()

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
        self.thereshold, = ax.plot(
            np.zeros(self._heights.shape[0]),
            self._heights,
            'g-',
            label="Outliers thereshold")

        # avg = self.getAveragedLine(self.frqNumber)
        # avg_line = ax.plot(avg, self._heights)

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
        return self.line, self.thereshold, self.timetext

    # draw function.  This is called sequentially
    def animate(self, i):
        data_abs, data_complex = self.getUnit(i)

        value = data_abs[self.frqNumber, :]
        thereshold = self.getThereshold(value)
        self.line.set_xdata(value)
        self.thereshold.set_xdata(np.ones(self._heights.shape[0]) * thereshold)

        t = i * self._dt / 60  # time in minits
        self.timetext.set_text('{0:8.2f}, min.'.format(t))

        return self.line, self.thereshold, self.timetext

    def start(self):
        # call the animator.
        # blit=True means only re-draw the parts that have changed.
        self.anim = animation.FuncAnimation(
            self.fig, self.animate, init_func=self.init,
            frames=self._units, interval=1,
            blit=True, repeat=False)
        plt.show()
