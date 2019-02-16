import urllib.request
import html.parser
import re
import PIL.Image
import ffmpeg

def dajZoznamKamier():
  parser = KameraParser()
  with urllib.request.urlopen(shmuWebAdresa + '?page=1&id=webkamery') as stranka:
    parser.feed(stranka.read().decode('utf-8'))
  return parser.kamery

def dajKamerySNahladmi():
  for kamera in dajZoznamKamier():
    kamera.ziskajNahlad()
    yield kamera

def dajObrazkyKamery(kamera):
  parser = ObrazkyParser(kamera)
  with urllib.request.urlopen(shmuWebAdresa + kamera.link + '&c=360') as stranka:
    parser.feed(stranka.read().decode('utf-8'))
  return parser.obrazky

def dajObrazok(obrazok):
  with urllib.request.urlopen(shmuAdresa + obrazok.link) as obrazokData:
    return PIL.Image.open(obrazokData)

def vytvorVideo(obrazky, videoSubor, framerate):
  video = (ffmpeg
    .input('pipe:', format='rawvideo', pix_fmt='rgb24', s='{}x{}'.format(*obrazky[0].size), framerate=framerate)
    .output(videoSubor, **{'b:v' : 800000})
    .overwrite_output()
    .run_async(pipe_stdin=True)
    )
  for obrazok in obrazky:
    video.stdin.write(obrazok.tobytes())
  video.stdin.close()
  video.wait()


class Kamera:
  def __init__(self, link):
    self.link = link
    self.id = re.match(r'\?page=1&id=webkamery&kamera=(.*)', self.link).group(1)

  def nastavNazov(self, nazov):
    self.nazov = nazov

  def nastavNahlad(self, nahladLink):
    self.nahladLink = Obrazok(self, ('', nahladLink))

  def ziskajNahlad(self):
    nahlad = dajObrazok(self.nahladLink)
    self.nahlad = nahlad.resize((256, int(nahlad.height * 256 / nahlad.width)), PIL.Image.LANCZOS)

  def dajCestuObrazku(self):
    return 'data/datawebcam/' + self.id + '/'

class Obrazok:
  def __init__(self, kamera, data):
    self.nazov = data[0]
    cestaObrazku = kamera.dajCestuObrazku()
    najdenyLink = re.search(cestaObrazku + r'(\d{8}_\d{6}.jpg)', data[1])
    self.link = cestaObrazku + (najdenyLink.group(1) if najdenyLink is not None else data[1])

  def __eq__(self, value):
    return self.nazov == value.nazov and self.link == value.link


def dajAtribut(attrs, attrNazov):
  for attr in attrs:
    if attr[0] == attrNazov:
      return attr[1]
  return None


class KameraParser (html.parser.HTMLParser):
  def __init__(self):
    super().__init__()
    self.kamery = []
    self.kameraDivPocet = 0
    self.vNazveKamery = False
    self.aktualnaKamera = None

  def handle_starttag(self, tag, attrs):
    if self.kameraDivPocet == 0:
      if tag == 'div' and dajAtribut(attrs, 'id') == 'maincontent':
        self.kameraDivPocet = 1
    else:
      if tag == 'div':
        self.kameraDivPocet += 1
      elif tag == 'a':
        self.aktualnaKamera = Kamera(dajAtribut(attrs, 'href'))
      elif tag == 'h3':
        self.vNazveKamery = True
      elif tag == 'img':
        if self.aktualnaKamera is not None:
          self.aktualnaKamera.nastavNahlad(dajAtribut(attrs, 'src'))

  def handle_endtag(self, tag):
    if tag == 'div' and self.kameraDivPocet > 0:
      self.kameraDivPocet -= 1
      if self.aktualnaKamera is not None:
        self.kamery.append(self.aktualnaKamera)
        self.aktualnaKamera = None

  def handle_data(self, data):
    if self.aktualnaKamera is not None and self.vNazveKamery:
      self.aktualnaKamera.nastavNazov(data)
      self.vNazveKamery = False


class ObrazkyParser (html.parser.HTMLParser):
  def __init__(self, kamera):
    super().__init__()
    self.kamera = kamera
    self.obrazky = []
    self.vSkripte = False

  def handle_starttag(self, tag, attrs):
    if tag == 'script' and dajAtribut(attrs, 'type') == 'text/javascript':
      self.vSkripte = True

  def handle_endtag(self, tag):
    if self.vSkripte and tag == 'script':
      self.vSkripte = False

  def handle_data(self, data):
    if self.vSkripte and re.match(r'\s*var img_dts.*', data):
      vzor = re.compile(r'img_dts\[\d*\]=\'(.*?)\'; img_files\[\d*\]=\'(.*?)\';')
      start = 0
      while start >= 0:
        najdene = vzor.search(data, start)
        if najdene is not None:
          self.obrazky.append(Obrazok(self.kamera, najdene.groups()))
          start = najdene.span()[1]
        else:
          start = -1


shmuAdresa = 'http://www.shmu.sk/'
shmuWebAdresa = shmuAdresa + 'sk/'
