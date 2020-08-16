import tkinter
import tkinter.ttk
import tkinter.filedialog
import PIL.ImageTk
import threading
import queue
import collections
import os.path
import SHMU_Kamery
import json


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
    self.nastavenia = Nastavenia('config.json')

  def ukonci(self):
    self.kamery.ukonci()
    if self.aktualnaKamera is not None:
      self.aktualnaKamera.ukonci()
    self.nastavenia.uloz()
    
  def nastavKameru(self, kamera):
    self.kamery.schovaj()
    self.aktualnaKamera = AktualnaKamera(self, kamera)

class Nastavenia:
  def __init__(self, subor):
    self.subor = subor
    try:
      self.data = json.load(open(self.subor, 'r'))
    except:
      self.data = {}

  def uloz(self):
    json.dump(self.data, open(self.subor, 'w'))

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
    self.videoVlakno = None
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
    self.rychlostPopis = tkinter.Label(self, text='Počet obrazkov/s')
    self.rychlost = tkinter.Entry(self, width=2)
    self.rychlost.insert(0, '8')
    self.prehladTlacidlo = tkinter.Button(self, text='Prezri video', command=self.prezriVideo)
    self.videoTlacidlo = tkinter.Button(self, text='Vytvor video', command=lambda : self.vytvorAnimaciu('V'))
    self.gifOddelovac = tkinter.ttk.Separator(self, orient=tkinter.HORIZONTAL)
    self.gifNekonecno = tkinter.IntVar()
    self.gifNekonecnoVolba = tkinter.Checkbutton(self, text='Nekonečné opakovanie', variable=self.gifNekonecno, command=self.zmenaNekonecna)
    self.gifTlacidlo = tkinter.Button(self, text='Vytvor gif', command=lambda : self.vytvorAnimaciu('G'))
    self.opakovaniaPopis = tkinter.Label(self, text='Počet opakovaní')
    self.opakovania = tkinter.Entry(self, width=4)
    self.opakovania.insert(0, '1')
    self.koncovyIntervalPopis = tkinter.Label(self, text='Koncový interval [ms]')
    self.koncovyInterval = tkinter.Entry(self, width=4)
    self.koncovyInterval.insert(0, '250')
    self.navratTlacidlo = tkinter.Button(self, text='Späť', command=self.naPrehladKamier)
    self.stavNacitania = tkinter.ttk.Progressbar(self, orient=tkinter.HORIZONTAL, maximum=len(self.nazvyObrazkov),
      mode='determinate')
    self.guiNazov.grid(row=0, column=0, columnspan=3)
    self.guiObrazok.grid(row=1, column=0, rowspan=10)
    self.casovaOs.grid(row=10, column=0)
    self.zaciatok.grid(row=1, column=1, padx=4, pady=4)
    self.koniec.grid(row=1, column=2, padx=4, pady=4)
    self.zaciatokTlacidlo.grid(row=2, column=1, padx=4, pady=4)
    self.koniecTlacidlo.grid(row=2, column=2, padx=4, pady=4)
    self.rychlostPopis.grid(row=3, column=1, padx=4, pady=4)
    self.rychlost.grid(row=3, column=2, padx=4, pady=4)
    self.prehladTlacidlo.grid(row=4, column=1, padx=4, pady=4)
    self.videoTlacidlo.grid(row=4, column=2, padx=4, pady=4)
    self.gifOddelovac.grid(row=5, column=1, columnspan=2, sticky=tkinter.W+tkinter.E)
    self.gifNekonecnoVolba.grid(row=6, column=1)
    self.gifTlacidlo.grid(row=6, column=2, padx=4, pady=4)
    self.opakovaniaPopis.grid(row=7, column=1)
    self.opakovania.grid(row=7, column=2)
    self.koncovyIntervalPopis.grid(row=8, column=1)
    self.koncovyInterval.grid(row=8, column=2)
    self.grid_rowconfigure(9, weight=1)
    self.navratTlacidlo.grid(row=9, column=1, columnspan=2, sticky=tkinter.S, padx=4, pady=4)
    self.stavNacitania.grid(row=10, column=1, columnspan=2)
    SpracovanieVPozadi.__init__(self)

  def schovaj(self):
    self.ukonci()
    self.grid_forget()

  def spracujUdalosti(self):
    if self.videoVlakno is not None and not self.videoVlakno.zapisBezi:
      self.videoVlakno.join()
      self.videoVlakno = None
      self.stavNacitania.grid_forget()
    SpracovanieVPozadi.spracujUdalosti(self)

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

  def dajHodnotu(self, vstupnePole, defHodnota):
    try:
      return int(vstupnePole.get())
    except:
      vstupnePole.delete(0, tkinter.END)
      vstupnePole.insert(0, str(defHodnota))
      return defHodnota

  def dajZaciatok(self):
    return self.dajHodnotu(self.zaciatok, 0)

  def dajKoniec(self):
    return self.dajHodnotu(self.koniec, 359)

  def dajRychlost(self):
    return self.dajHodnotu(self.rychlost, 10)

  def dajGifNekonecno(self):
    return self.gifNekonecno.get() != 0

  def dajGifOpakovania(self):
    return 0 if self.dajGifNekonecno() else self.dajHodnotu(self.opakovania, 1)

  def dajKoncovyInterval(self):
    return self.dajHodnotu(self.koncovyInterval, 250)

  def vytvorAnimaciu(self, typ):
    adresar = self.master.nastavenia.data['adresar'] if 'adresar' in self.master.nastavenia.data else '~/Videos'
    suborTypy = (('gif subory','*.gif'),) if typ == 'G' else (('avi subory','*.avi'),('vsetky subory','*.*'))
    nazovVidea = tkinter.filedialog.asksaveasfilename(initialdir=adresar, title='Vyber cielovy subor', filetypes=suborTypy)
    if nazovVidea == '':
      return
    nazov, pripona = os.path.splitext(nazovVidea)
    if pripona == '':
      nazovVidea += '.gif' if typ == 'G' else '.avi'
    self.master.nastavenia.data['adresar'] = os.path.split(nazov)[0]
    start = self.dajZaciatok()
    koniec = self.dajKoniec() + 1
    if self.videoVlakno is None:
      self.videoVlakno = VideoZapis(self.vsetkyObrazky[start:koniec], nazovVidea, self)
      self.stavNacitania = tkinter.ttk.Progressbar(self, orient=tkinter.HORIZONTAL, mode='indeterminate')
      self.stavNacitania.grid(row=10, column=1, columnspan=2)
      self.stavNacitania.start()

  def prezriVideo(self):
    self.prehladTlacidlo.configure(text='Zastav video', command=self.zastavVideo)
    self.prehravanieVidea = True
    self.posunVideo()

  def posunVideo(self):
    if not self.prehravanieVidea:
      return
    index = self.casovaOs.get() + 1
    if index > self.dajKoniec():
      index = self.dajZaciatok()
    self.casovaOs.set(index)
    self.zmenaPozicie(None)
    self.after(int(1000 / self.dajRychlost()), self.posunVideo)

  def zastavVideo(self):
    self.prehladTlacidlo.configure(text='Prezri video', command=self.prezriVideo)
    self.prehravanieVidea = False

  def nastavZaciatok(self):
    self.zaciatok.delete(0, tkinter.END)
    self.zaciatok.insert(0, str(self.casovaOs.get()))

  def nastavKoniec(self):
    self.koniec.delete(0, tkinter.END)
    self.koniec.insert(0, str(self.casovaOs.get()))

  def zmenaNekonecna(self):
    self.opakovania.configure(state=tkinter.DISABLED if self.dajGifNekonecno() else tkinter.NORMAL)

  def naPrehladKamier(self):
    self.schovaj()
    self.master.kamery.zobraz()


class VideoZapis(threading.Thread):
  def __init__(self, obrazky, nazovVidea, parametre):
    super().__init__()
    self.obrazky = obrazky
    self.nazovVidea = nazovVidea
    self.parametre = parametre
    self.zapisBezi = True
    self.start()

  def run(self):
    SHMU_Kamery.vytvorAnimaciu(self.obrazky, self.nazovVidea, self.parametre)
    self.zapisBezi = False


if __name__ == '__main__':
  root = tkinter.Tk()
  app = GUIApp(master=root)
  app.mainloop()
  app.ukonci()
