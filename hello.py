# -*- coding: utf-8 -*-
import sys
import os.path

import scipy.io
import numpy as np
import h5py


class ClassMatFile:
    """Класс осуществляет обработку v7 и hdf5 mat-файлов Matlab."""

    extensions = ['mat', 'fig'] # расширения файла

    @property
    def filename(self): return self._filename
    @filename.setter
    def filename(self, value):

        # Проверка на существование файла.
        if not os.path.isfile(value):
            message = "No such file or directory <{}>!".format(value)
            raise OSError(message)

        # Проверка на соответствие расширения
        extension = value.split('.')[-1].lower()
        if value.lower() == extension:
            message = "The file <{}> have not extension!".format(value)
            raise OSError(message)
        else:
            if extension not in self.extensions:
                message = "The file <{}> isn't mat-file!".format(value)
                raise OSError(message)

        # Пытаемся открыть mat файл
        try:
            self._open_old_mat(value)
        except Exception as e:
            print(e)
            self._open_hdf5_mat(value)
        else:
            self._filename = value

    def _open_old_mat(self, filename):
        """Пытаемся открыть файл старого формата."""
        # mat version < 7.3, save('test.mat','-v7')
        try:
            mat = scipy.io.loadmat(filename)
        except:
            message = "The file <{}> isn't mat-file with version < 7.3!".format(filename)
            raise OSError(message)
        else:
            self._source = mat
            self._version = 'old'


    def _open_hdf5_mat(self, filename):
        """Пытаемся открыть файл формата hdf5."""
        # mat version >= 7.3
        # h5py extension requires HDF5 on your system.
        # This works fine, if you use the '-v7.3' flag in Matlab when saving out your data.
        try:
            File = h5py.File(filename, 'r')
        except:
            message = "The file <{}> isn't mat-file with version >= 7.3!".format(filename)
            raise OSError(message)
        else:
            self._source = File
            self._version = 'hdf5'


    def __init__(self, filename):
        """Инициализация объекта файлом mat произвольного формата."""
        self._source = False
        self._version = False

        try:
            self.filename = filename
        except OSError as e:
            print(e)
            raise


if __name__ == "__main__":

    print("Hello world!")
    A = ClassMatFile('db_interface.fig')

    #data = f.get('data/variable1')
    #data = np.array(data)  # For converting to numpy array