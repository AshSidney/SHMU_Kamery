import tkinter
import tkinter.ttk
import PIL.ImageTk
import threading
import queue
import collections
import SHMU_Kamery


class GUIApp(tkinter.Frame): 
  def __init__(self, master=None):
    super().__init__(master)
    master.grid_rowconfigure(0, weight=1)
    master.grid_columnconfigure(0, weight=1)
    self.grid(column=0, row=0, sticky=tkinter.NSEW)
    self.grid_rowconfigure(0, weight=1)
    self.grid_columnconfigure(0, weight=1)
    self.kamery = ZoznamKamier(self)
    
  def nastavKameru(self, kamera):
    print('vybrana kamera', kamera.nazov)
    self.kamery.schovaj()
    self.aktualnaKamera = AktualnaKamera(self, kamera)


class ZoznamKamier(tkinter.Canvas):
  def __init__(self, master):
    super().__init__(master, width=800, height=600)
    self.okno = tkinter.Frame(self)
    self.posuvnik = tkinter.Scrollbar(master, orient=tkinter.VERTICAL, command=self.yview)
    self.configure(yscrollcommand=self.posuvnik.set)
    self.create_window((0,0), window=self.okno, anchor=tkinter.NW, tags='self.okno')
    self.bind('<Configure>', self.konfiguraciaKamier)
    self.okno.bind('<Configure>', self.konfiguraciaPosunu)
    self.bind_all('<MouseWheel>', self.posunKolieskom)
    self.zobraz()

    self.guiKamery = []
    self.udalosti = queue.Queue()
    self.nacitanieKamier = threading.Thread(target=self.nacitajKamery)
    self.nacitanieKamier.start()
    self.spracujUdalosti()

  def zobraz(self):
    self.grid(row=0, column=0, sticky=tkinter.NSEW)
    self.posuvnik.grid(row=0, column=1, sticky=tkinter.NSEW)

  def schovaj(self):
    self.grid_forget()
    self.posuvnik.grid_forget()

  def spracujUdalosti(self):
    while not self.udalosti.empty():
      self.vytvorKameru(self.udalosti.get())
    self.after(200, self.spracujUdalosti)

  def nacitajKamery(self):
    for kamera in SHMU_Kamery.dajKamerySNahladmi():
      self.udalosti.put(kamera)
    self.udalosti.put(None)

  def vytvorKameru(self, kamera):
    if kamera is None:
      self.nacitanieKamier.join()
      return
    self.guiKamery.append(KameraNahlad(self.okno, kamera,self.master))
    self.konfiguraciaKamier(collections.namedtuple('Event', ('width', 'height'))(self.winfo_width(), self.winfo_height()))

  def konfiguraciaKamier(self, event):
    if len(self.guiKamery) == 0:
      return
    sirkaKamery = max(self.guiKamery[0].winfo_width(), 256)
    pocetStlpcov = max(int(event.width / sirkaKamery), 1)
    for index in range(len(self.guiKamery)):
      riadok = int(index / pocetStlpcov)
      stlpec = index - riadok * pocetStlpcov
      self.guiKamery[index].grid(row=riadok, column=stlpec)

  def konfiguraciaPosunu(self, event):
    self.configure(scrollregion=self.bbox(tkinter.ALL))

  def posunKolieskom(self, event):
    self.yview_scroll(1 if event.delta < 1 else -1, 'units')


class KameraNahlad(tkinter.Frame):
  def __init__(self, master, kamera, aplikacia):
    super().__init__(master, borderwidth=4, relief=tkinter.SUNKEN)
    self.kamera = kamera
    self.aplikacia = aplikacia
    self.nahlad = PIL.ImageTk.PhotoImage(self.kamera.nahlad)
    self.guiNahlad = tkinter.ttk.Label(self, image=self.nahlad)
    self.guiNahlad.grid(row=0, column=0)
    self.guiNazov = tkinter.ttk.Label(self, text=self.kamera.nazov)
    self.guiNazov.grid(row=1, column=0)
    self.bind('<Button-1>', self.vyberKamery)
    self.guiNahlad.bind('<Button-1>', self.vyberKamery)
    self.guiNazov.bind('<Button-1>', self.vyberKamery)

  def vyberKamery(self, event):
    self.aplikacia.nastavKameru(self.kamera)


class AktualnaKamera(tkinter.Frame):
  def __init__(self, master, kamera):
    super().__init__(master)
    self.kamera = kamera
    self.grid(row=0, column=0)
    self.guiNazov = tkinter.ttk.Label(self, text=self.kamera.nazov)
    self.obrazky = SHMU_Kamery.dajObrazkyKamery(self.kamera)
    self.aktualnyObrazok = PIL.ImageTk.PhotoImage(SHMU_Kamery.dajObrazok(self.obrazky[-1]))
    self.guiObrazok = tkinter.ttk.Label(self, image=self.aktualnyObrazok)
    self.casovaOs = tkinter.Scale(self, orient=tkinter.HORIZONTAL, from_=0, to=len(self.obrazky)-1,
      length=self.aktualnyObrazok.width(), command=self.zmenaPozicie)
    self.guiNazov.grid(row=0, column=0)
    self.guiObrazok.grid(row=1, column=0)
    self.casovaOs.grid(row=2, column=0)

    self.vsetkyObrazky = []
    self.udalosti = queue.Queue()
    self.nacitanieObrazkov = threading.Thread(target=self.nacitajObrazky)
    self.nacitanieObrazkov.start()
    self.spracujUdalosti()

  def schovaj(self):
    self.grid_forget()

  def spracujUdalosti(self):
    while not self.udalosti.empty():
      self.ulozObrazok(self.udalosti.get())
    self.after(200, self.spracujUdalosti)

  def nacitajObrazky(self):
    for obrazok in self.obrazky:
      self.udalosti.put(SHMU_Kamery.dajObrazok(obrazok))
    self.udalosti.put(None)

  def ulozObrazok(self, obrazok):
    if obrazok is None:
      self.nacitanieObrazkov.join()
    else:
      self.vsetkyObrazky.append(PIL.ImageTk.PhotoImage(obrazok))

  def zmenaPozicie(self, event):
    index = self.casovaOs.get()
    if index < len(self.vsetkyObrazky):
      self.aktualnyObrazok = self.vsetkyObrazky[index]
    else:
      self.aktualnyObrazok = PIL.ImageTk.PhotoImage(SHMU_Kamery.dajObrazok(self.obrazky[index]))
    self.guiObrazok.configure(image=self.aktualnyObrazok)


if __name__ == '__main__':
  root = tkinter.Tk()
  app = GUIApp(master=root)
  app.mainloop()
