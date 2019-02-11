import tkinter
import tkinter.ttk
import PIL.ImageTk
import threading
import queue
import collections
import SHMU_Kamery


class GUIApp(tkinter.Frame): 
  def __init__(self, master=None):
    super().__init__(master, width=800, height=600)
    master.grid_rowconfigure(0, weight=1)
    master.grid_columnconfigure(0, weight=1)
    self.grid(column=0, row=0, sticky=tkinter.NSEW)
    self.bind('<Configure>', self.konfiguracia)
    self.guiKamery = []
    self.udalosti = queue.Queue()
    self.nacitanieKamier = threading.Thread(target=self.nacitajKamery)
    self.nacitanieKamier.start()
    self.spracujUdalosti()

  def spracujUdalosti(self):
    while not self.udalosti.empty():
      self.vytvorKamery(self.udalosti.get())
    self.after(1000, self.spracujUdalosti)

  def nacitajKamery(self):
    self.udalosti.put(SHMU_Kamery.dajZoznamKamier())

  def vytvorKamery(self, kamery):
    self.nacitanieKamier.join()
    for kamera in kamery:
      self.guiKamery.append(KameraNahlad(self, kamera))
    self.konfiguracia(collections.namedtuple('Event', ('width', 'height'))(self.winfo_width(), self.winfo_height()))

  def konfiguracia(self, event):
    print('konfiguracia', event, 'pocet kamier', len(self.guiKamery))


class KameraNahlad(tkinter.Frame):
  def __init__(self, master, kamera):
    super().__init__(master)
    self.kamera = kamera
    self.vykresli()

  def vykresli(self):
    self.guiObrazok = PIL.ImageTk.PhotoImage(self.kamera.nahlad)
    self.guiKamera = tkinter.ttk.Label(self, text=self.kamera.nazov, image=self.guiObrazok)



if __name__ == '__main__':
  root = tkinter.Tk()
  app = GUIApp(master=root)
  app.mainloop()
