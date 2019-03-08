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
    self.aktualnaKamera = None

  def ukonci(self):
    self.kamery.ukonci()
    if self.aktualnaKamera is not None:
      self.aktualnaKamera.ukonci()
    
  def nastavKameru(self, kamera):
    self.kamery.schovaj()
    self.aktualnaKamera = AktualnaKamera(self, kamera)


class SpracovanieVPozadi:
  def __init__(self):
    self.udalosti = queue.Queue()
    self.prerusenieVlakna = False
    self.vlakno = threading.Thread(target=self.pracaVPozadi)
    self.vlakno.start()
    self.spracujUdalosti()

  def ukonci(self):
    self.prerusenieVlakna = True

  def spracujUdalosti(self):
    while not self.udalosti.empty():
      udalost = self.udalosti.get()
      if udalost is None:
        self.vlakno.join()
      else:
        self.spracujData(udalost)
    self.after(200, self.spracujUdalosti)

  def pracaVPozadi(self):
    self.udalosti.put(None)

  def spracujData(self, udalost):
    pass


class ZoznamKamier(tkinter.Canvas, SpracovanieVPozadi):
  def __init__(self, master):
    tkinter.Canvas.__init__(self, master, width=1080, height=680)
    self.guiKamery = []
    self.okno = tkinter.Frame(self)
    self.posuvnik = tkinter.Scrollbar(master, orient=tkinter.VERTICAL, command=self.yview)
    self.configure(yscrollcommand=self.posuvnik.set)
    self.create_window((0,0), window=self.okno, anchor=tkinter.NW, tags='self.okno')
    self.bind('<Configure>', self.konfiguraciaKamier)
    self.okno.bind('<Configure>', self.konfiguraciaPosunu)
    self.zobraz()
    SpracovanieVPozadi.__init__(self)

  def zobraz(self):
    self.grid(row=0, column=0, sticky=tkinter.NSEW)
    self.posuvnik.grid(row=0, column=1, sticky=tkinter.NSEW)
    self.bind_all('<MouseWheel>', self.posunKolieskom)

  def schovaj(self):
    self.grid_forget()
    self.posuvnik.grid_forget()
    self.unbind_all('<MouseWheel>')

  def pracaVPozadi(self):
    for kamera in SHMU_Kamery.dajKamerySNahladmi():
      self.udalosti.put(kamera)
      if self.prerusenieVlakna:
        break
    self.udalosti.put(None)

  def spracujData(self, kamera):
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


class AktualnaKamera(tkinter.Frame, SpracovanieVPozadi):
  def __init__(self, master, kamera):
    tkinter.Frame.__init__(self, master)
    self.kamera = kamera
    self.nazvyObrazkov = SHMU_Kamery.dajObrazkyKamery(self.kamera)
    self.vsetkyObrazky = [None] * len(self.nazvyObrazkov)
    self.aktualnyObrazok = PIL.ImageTk.PhotoImage(SHMU_Kamery.dajObrazok(self.nazvyObrazkov[-1]))
    self.grid(row=0, column=0)
    self.guiNazov = tkinter.ttk.Label(self, text=self.kamera.nazov)
    self.guiObrazok = tkinter.ttk.Label(self, image=self.aktualnyObrazok)
    self.casovaOs = tkinter.Scale(self, orient=tkinter.HORIZONTAL, from_=0, to=len(self.nazvyObrazkov)-1,
      length=self.aktualnyObrazok.width(), command=self.zmenaPozicie)
    self.casovaOs.set(len(self.nazvyObrazkov)-1)
    self.zaciatok = tkinter.Entry(self, width=4)
    self.zaciatok.insert(0, str(0))
    self.koniec = tkinter.Entry(self, width=4)
    self.koniec.insert(0, str(len(self.nazvyObrazkov) - 1))
    self.zaciatokTlacidlo = tkinter.Button(self, text='Nastav začiatok', command=self.nastavZaciatok)
    self.koniecTlacidlo = tkinter.Button(self, text='Nastav koniec', command=self.nastavKoniec)
    self.videoTlacidlo = tkinter.Button(self, text='Vytvor video', command=self.vytvorVideo)
    self.navratTlacidlo = tkinter.Button(self, text='Späť', command=self.naPrehladKamier)
    self.stavNacitania = tkinter.ttk.Progressbar(self, orient=tkinter.HORIZONTAL, maximum=len(self.nazvyObrazkov),
      mode='determinate')
    self.grid_rowconfigure(4, weight=1)
    self.guiNazov.grid(row=0, column=0, columnspan=3)
    self.guiObrazok.grid(row=1, column=0, rowspan=4)
    self.casovaOs.grid(row=5, column=0)
    self.zaciatok.grid(row=1, column=1, padx=4, pady=4)
    self.koniec.grid(row=1, column=2, padx=4, pady=4)
    self.zaciatokTlacidlo.grid(row=2, column=1, padx=4, pady=4)
    self.koniecTlacidlo.grid(row=2, column=2, padx=4, pady=4)
    self.videoTlacidlo.grid(row=3, column=1, columnspan=2, padx=4, pady=4)
    self.navratTlacidlo.grid(row=4, column=1, columnspan=2, sticky=tkinter.S, padx=4, pady=4)
    self.stavNacitania.grid(row=5, column=1, columnspan=2)
    SpracovanieVPozadi.__init__(self)

  def schovaj(self):
    self.ukonci()
    self.grid_forget()

  def pracaVPozadi(self):
    for index in range(len(self.nazvyObrazkov) - 1, -1, -1):
      self.udalosti.put((index, SHMU_Kamery.dajObrazok(self.nazvyObrazkov[index])))
      if self.prerusenieVlakna:
        break
    self.udalosti.put(None)

  def spracujData(self, obrazok):
    self.vsetkyObrazky[obrazok[0]] = obrazok[1]
    self.stavNacitania.step(1)
    if obrazok[0] == 0:
      self.stavNacitania.grid_forget()

  def zmenaPozicie(self, event):
    index = self.casovaOs.get()
    if self.vsetkyObrazky[index] is not None:
      self.aktualnyObrazok = PIL.ImageTk.PhotoImage(self.vsetkyObrazky[index])
    self.guiObrazok.configure(image=self.aktualnyObrazok)

  def vytvorVideo(self):
    start = int(self.zaciatok.get())
    koniec = int(self.koniec.get()) + 1
    SHMU_Kamery.vytvorVideo(self.vsetkyObrazky[start:koniec], 'video.avi', 8)

  def nastavZaciatok(self):
    self.zaciatok.delete(0, tkinter.END)
    self.zaciatok.insert(0, str(self.casovaOs.get()))

  def nastavKoniec(self):
    self.koniec.delete(0, tkinter.END)
    self.koniec.insert(0, str(self.casovaOs.get()))

  def naPrehladKamier(self):
    self.schovaj()
    self.master.kamery.zobraz()


if __name__ == '__main__':
  root = tkinter.Tk()
  app = GUIApp(master=root)
  app.mainloop()
  app.ukonci()
