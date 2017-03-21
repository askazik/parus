# -*- coding: utf-8 -*-

# импортирование модулей python
from datetime import datetime
import os.path as path
import glob
import os

import tkinter as tk
import tkinter.font as tkfont
import tkinter.ttk as ttk
import tkinter.filedialog as tkfd

# используем наработки по теме
import sys
sys.path.append('../frq/')
import parusFile as pf
import parusPlot as pplt

# класс родительских окон
class main(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        self.master = master
        self.master.title('Аггрегатор процедур обработки измерений')
        self.master.geometry('500x650+850+0')

        self.menuCreate()
        self.initPopupMenu()

        self.initGrid(self.master)
        self.askDirectory()

        self.master.mainloop()

    def menuCreate(self):
        m = tk.Menu(root) #создается объект Меню на главном окне
        root.config(menu=m) #окно конфигурируется с указанием меню для него

        fm = tk.Menu(m) #создается пункт меню с размещением на основном меню (m)
        m.add_cascade(label="Файл", menu=fm) #пункт располагается на основном меню (m)
        fm.add_command(
            label="Папка...",
            command=self.askDirectory) #формируется список команд пункта меню
        fm.add_separator()
        fm.add_command(
            label="Открыть файл выбора...",
            command=self.openSelected)
        fm.add_command(
            label="Сохранить файл выбора...",
            command=self.saveSelected)
        fm.add_separator()
        fm.add_command(
            label="Выход",
            command=self.close_win)

        vm = tk.Menu(m)  # формирование видимого оконного интерфейса
        m.add_cascade(label='Вид', menu=vm)

        self.show_ion = tk.BooleanVar()
        self.show_ion.set(False)
        self.show_ionR = tk.BooleanVar()
        self.show_ionR.set(False)
        self.show_ionM = tk.BooleanVar()
        self.show_ionM.set(False)

        vm.add_checkbutton(
            label='Файлы ионограмм',
            onvalue=True, offvalue=False, variable=self.show_ion)
        vm.add_checkbutton(
            label='Файлы ионограмм (Ростов) Парус-А',
            onvalue=True, offvalue=False, variable=self.show_ionR)
        vm.add_checkbutton(
            label='Файлы ионограмм (Москва) Парус-А',
            onvalue=True, offvalue=False, variable=self.show_ionM)

        hm = tk.Menu(m) #второй пункт меню
        m.add_cascade(label="Помощь", menu=hm)
        hm.add_command(label="Помощь")
        hm.add_separator()
        hm.add_command(
            label='О программе',
            command=self.about)

    def initGrid(self, parent):
        f = ttk.Frame(parent)
        f.pack(side=tk.TOP, fill=tk.BOTH, expand=tk.Y)

        # create the tree and scrollbars
        self.dataCols = ('fname', 'ftime', 'fsize', 'fselected')
        self.tree = ttk.Treeview(columns=self.dataCols)

        ysb = ttk.Scrollbar(orient=tk.VERTICAL, command= self.tree.yview)
        xsb = ttk.Scrollbar(orient=tk.HORIZONTAL, command= self.tree.xview)
        self.tree['yscroll'] = ysb.set
        self.tree['xscroll'] = xsb.set

        # setup column headings
        self.tree.heading('#0', text='№')
        self.tree.heading('fname', text='File Name')
        self.tree.heading('ftime', text='File Time')
        self.tree.heading('fsize', text='Size (Kb)')
        self.tree.heading('fselected', text='Selected')

        self.tree.column('#0', stretch=0, width=60, anchor=tk.E)
        self.tree.column('fname', stretch=0, width=130, anchor=tk.W)
        self.tree.column('ftime', stretch=0, width=110)
        self.tree.column('fsize', stretch=0, width=80, anchor=tk.E)
        self.tree.column('fselected', stretch=0, width=60, anchor=tk.E)

        # add tree and scrollbars to frame
        self.tree.grid(in_=f, row=0, column=0, sticky=tk.NSEW)
        ysb.grid(in_=f, row=0, column=1, sticky=tk.NS)
        xsb.grid(in_=f, row=1, column=0, sticky=tk.EW)

        # set frame resizing priorities
        f.rowconfigure(0, weight=1)
        f.columnconfigure(0, weight=1)

        # create fonts and tags
        self.normal   = tkfont.Font(family='Consolas', size=10)
        self.boldfont = tkfont.Font(family='Consolas', size=10, weight='bold')
        self.whacky   = tkfont.Font(family='Jokerman', size=10)

        self.tree.tag_configure('normal',   font=self.normal)
        self.tree.tag_configure('timedout', background='pink',
            font=self.boldfont)
        self.tree.tag_configure('whacky',   background='lightgreen',
            font=self.whacky)

        # Button-3 is right click on windows
        self.tree.bind("<Button-3>", self.onTreePopup)
        # Button-1 double click
        self.tree.bind("<Double-1>", self.onDoubleClick)


    def _build_data_for_directory(self, ext):
        cur_dir = self.directory
        names = glob.glob(path.join(cur_dir, ext))
        n_files = len(names)
        out_dict = {}

        i = 1
        for name in names:
            # Parsing data and collect information.
            A = pf.parusFile(name)
            ftime = datetime(*A.time[:6])
            fsize = os.stat(name).st_size // 1024  # Kb

            out_dict[i] = [A.name, ftime, fsize, 0]
            i += 1

        return out_dict

    def _populate_tree(self, in_dict):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for n in range(len(in_dict)):
            num = n+1
            item = in_dict[num]

            self.tree.insert('', tk.END, text='%3d'%num, values=item)

    def close_win(self):
        self.master.destroy()

    def about(self):
        win = tk.Toplevel(self.master)
        lab = tk.Label(win,text="Это просто программа-тест \n меню в Tkinter")
        lab.pack()

    def askDirectory(self):
        path = tkfd.askdirectory(
            title='Выбор рабочей папки...',
            mustexist=True
            )
        path = os.path.normpath(path)
        if not path:
            return
        else:
            self.directory = path
            cur_dict = self._build_data_for_directory('*.frq')
            self._populate_tree(cur_dict)

    def initPopupMenu(self):
        self.popup_menu = tk.Menu(self.master, tearoff=0)
        self.popup_menu.add_command(
            label="Усреднение по выборке",
            command=self.onAverage)
        self.popup_menu.add_command(
            label="Амплитуды и спектры отражений",
            command=self.onAmplitude)
        self.popup_menu.add_command(
            label="Просмотр в реальном времени",
            command=self.onRealView)
        self.popup_menu.add_command(
            label="Отметка выбора",
            command=self.onSelect)
        self.pack()

    def selectGridItem(self, e):
        # select row under mouse
        iid = self.tree.identify_row(e.y)
        if iid:
            # mouse pointer over item
            self.tree.selection_set(iid)
            item = self.tree.item(iid)
            self.cur_fname = item.get('values')[0]

    def onTreePopup(self, e):
        self.selectGridItem(e)
        self.popup_menu.post(e.x_root, e.y_root)

    def onDoubleClick(self, e):
        self.selectGridItem(e)
        self.onAverage()

    def plotAveraged(self, fname):
        name = path.join(self.directory, fname)
        A = pf.parusFile(name)
        ave, ave2, _h, _a = A.getAveragedMeans()
        pplt.plotAveragedLog10Lines(name, A.heights, A.frqs, ave2)

    def onAverage(self):
        self.plotAveraged(self.cur_fname)

    def onRealView(self):
        pass

    def onSelect(self):
        iid = ttk.Treeview.focus(self.tree)
        item = self.tree.item(iid)
        selected = self.tree.item(iid).get('values')[-1]
        if selected == 0:
            selected = 1
        elif selected == 1:
            selected = 0

        self.tree.set(iid, column=3, value=selected)

    def cursor(self):
        # change cursor mode
        if not self.master.cget('cursor') == '':
            self.master.config(cursor='')
        else:
            self.master.config(cursor='watch')

    def getNowFileName(self):
        _dt = datetime.now()
        _s = _dt.strftime('%Y-%m-%d_%H-%M-%S') + '.sel'
        return _s

    def saveSelected(self):

        # get file name for save
        ifile = self.getNowFileName()
        idir = self.directory
        title = 'Сохранить выбор в файл...'
        types = [('Select files', '*.sel'), ('All files', '*')]
        filename = tkfd.asksaveasfilename(
            filetypes=types,
            initialdir=idir,
            initialfile=ifile,
            title=title)
        if not filename: return

        # save selections
        f = open(filename, 'w')
        for child in self.tree.get_children():
            _dict = self.tree.item(child)["values"]
            if _dict[-1]:
                try:
                    f.write(_dict[0] + '\n')
                except EOFError:
                    break
        f.close()

    def openSelected(self):
        # get file name for save
        idir = self.directory
        title = 'Извлечь выбор из файла...'
        types = [('Select files', '*.sel'), ('All files', '*')]
        filename = tkfd.askopenfilename(
            filetypes=types,
            initialdir=idir,
            title=title)
        if not filename: return

        # return selections
        f = open(filename, 'r')
        for lineN in f:
            line = lineN.strip('\n')
            for child in self.tree.get_children():
                _dict = self.tree.item(child)["values"]
                if line == _dict[0]:
                    self.tree.set(child, column=3, value=1)

        f.close()

    def onAmplitude(self):
        name = path.join(self.directory, self.cur_fname)
        A = pf.parusFile(name)

        results = A.SpectralCalculation()
        # Plot amplitudes for two reflections.
        signals = results['signal']
        noise = results['noise']
        power0, power1, Pnoise = pplt.plotAmplitudes(
            signals[:, :, 0:2],
            A.dt,
            A.frqs,
            name,
            noise)

# Проверочная программа
if __name__ == '__main__':
    #создание окна
    root = tk.Tk()
    main(root)
