# -*- coding: utf-8 -*-
"""
Work with database SQLite3.
"""
from datetime import datetime
import numpy as np
import sqlite3
import io

import parusFile as pf


class parusDB(object):
    "Class for work with sqlite3 database for Parus data."

    def __init__(self, fileName='parus.sqlite'):
        super().__init__()
        self._filename = fileName
        self.customization()
        self._con = sqlite3.connect(
            self._filename,
            detect_types=sqlite3.PARSE_DECLTYPES)
        self._cur = self._con.cursor()

    def adapt_array(self, arr):
        """
        http://stackoverflow.com/a/31312102/190597 (SoulNibbler)
        """
        out = io.BytesIO()
        np.save(out, arr)
        out.seek(0)
        return sqlite3.Binary(out.read())

    def convert_array(self, text):
        out = io.BytesIO(text)
        out.seek(0)
        return np.load(out)

    def customization(self):
        # Converts np.array to TEXT when inserting
        sqlite3.register_adapter(np.ndarray, self.adapt_array)
        # Converts TEXT to np.array when selecting
        sqlite3.register_converter("array", self.convert_array)

    def executeSELECT(self, text):
        # "SELECT name FROM sqlite_master WHERE type='table'"
        self._cur.execute(text)
        print(self._cur.fetchall())

    def saveResults(self, name, tim, dt, frqs, heights, amplitudes):
        tm = datetime(*tim[:6])
        self._cur.execute('insert into files '
                        '(name, time, dt, ref_heights, amplitudes) '
                        'values (?,?,?,?,?)',
                        (name, tm, dt, heights, amplitudes))
        self._con.commit()

    def getResults(self):
        # And retrieve the array directly from sqlite as a NumPy array:
        # cur.execute("select arr from test")
        # data = cur.fetchone()[0]
        pass

    def close(self):
        "Close DB connection."

        self._cur.close()
        self._con.close()
