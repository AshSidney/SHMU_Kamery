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
    self.bind('<Configure>', self.konfiguraciaKamier)

    self.platno = tkinter.Canvas(self, width=800, height=600)
    self.okno = tkinter.Frame(self.platno)
    self.posuvnik = tkinter.Scrollbar(self, orient=tkinter.VERTICAL, command=self.platno.yview)
    self.platno.configure(yscrollcommand=self.posuvnik.set)
    self.platno.grid(row=0, column=0, sticky=tkinter.NSEW)
    self.posuvnik.grid(row=0, column=1, sticky=tkinter.NSEW)
    self.platno.create_window((0,0), window=self.okno, anchor=tkinter.NW, tags='self.okno')
    self.okno.bind('<Configure>', self.konfiguraciaPosunu)

    self.guiKamery = []
    self.udalosti = queue.Queue()
    self.nacitanieKamier = threading.Thread(target=self.nacitajKamery)
    self.nacitanieKamier.start()
    self.spracujUdalosti()

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
    self.guiKamery.append(KameraNahlad(self.okno, kamera))
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
    self.platno.configure(scrollregion=self.platno.bbox(tkinter.ALL))


class KameraNahlad(tkinter.Frame):
  def __init__(self, master, kamera):
    super().__init__(master, borderwidth=4, relief=tkinter.SUNKEN)
    self.kamera = kamera
    self.nahlad = PIL.ImageTk.PhotoImage(self.kamera.nahlad)
    self.guiNahlad = tkinter.ttk.Label(self, image=self.nahlad)
    self.guiNahlad.grid(row=0, column=0)
    self.guiNazov = tkinter.ttk.Label(self, text=self.kamera.nazov)
    self.guiNazov.grid(row=1, column=0)


if __name__ == '__main__':
  root = tkinter.Tk()
  app = GUIApp(master=root)
  app.mainloop()
