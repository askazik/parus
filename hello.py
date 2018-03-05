# -*- coding: utf-8 -*-

import scipy.io
import numpy as np
import h5py
import os.path

print("Hello world!")

# mat version < 7.3
# save('test.mat','-v7')
mat = scipy.io.loadmat('file.mat')

# mat version >= 7.3
# h5py extension requires HDF5 on your system.
# This works fine, if you use the '-v7.3' flag in Matlab when saving out your data.
f = h5py.File('somefile.mat', 'r')
data = f.get('data/variable1')
data = np.array(data)  # For converting to numpy array


class ClassMatFile:
    """Класс осуществляет обработку v7 и hdf5 mat-файлов Matlab."""

    def __init__(self, filename):

        if not os.path.isfile(filename):
            message = "No such file or directory <{}>!".format(filename)
            raise OSError(message)
        self.filename = filename
