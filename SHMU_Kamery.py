import urllib.request
import html.parser
import ssl
import re
import os.path
import PIL.Image
import ffmpeg # ffmpeg-python 

def dajZoznamKamier():
  parser = KameraParser()
  with urllib.request.urlopen(shmuWebAdresa + '?page=1&id=webkamery') as stranka:
    parser.nacitaj(stranka)
  return parser.kamery

def dajKamerySNahladmi():
  for kamera in dajZoznamKamier():
    kamera.ziskajNahlad()
    yield kamera

def dajObrazkyKamery(kamera):
  parser = ObrazkyParser(kamera)
  with urllib.request.urlopen(shmuWebAdresa + kamera.link + '&c=360') as stranka:
    parser.nacitaj(stranka)
  return parser.obrazky

def dajObrazok(obrazok):
  for retry in range(16):
    try:
      with urllib.request.urlopen(shmuAdresa + obrazok) as obrazokData:
        return PIL.Image.open(obrazokData)
    except:
      pass

def vytvorVideo(obrazky, videoSubor, framerate):
  video = (ffmpeg
    .input('pipe:', format='rawvideo', pix_fmt='rgb24', s='{}x{}'.format(*obrazky[0].size), framerate=framerate)
    .output(videoSubor, **{'b:v' : 8000000})
    .overwrite_output()
    .run_async(pipe_stdin=True)
    )
  for obrazok in obrazky:
    video.stdin.write(obrazok.tobytes())
  video.stdin.close()
  video.wait()

def vytvorGif(obrazky, subor, opakovania, interval, koncovyInterval):
  durations = (len(obrazky) - 1) * [interval]
  durations.append(koncovyInterval)
  obrazky[0].save(subor, save_all=True, append_images=obrazky[1:], duration=durations, loop=opakovania)

def vytvorAnimaciu(obrazky, subor, parametre):
  nazov, pripona = os.path.splitext(subor)
  if pripona == '.gif':
    vytvorGif(obrazky, subor, parametre.dajGifOpakovania(), int(1000/parametre.dajRychlost()), parametre.dajKoncovyInterval())
  else:
    vytvorVideo(obrazky, subor, parametre.dajRychlost())

class Kamera:
  def __init__(self, link):
    self.link = link
    self.id = re.match(r'\?page=1&id=webkamery&kamera=(.*)', self.link).group(1)

  def nastavNazov(self, nazov):
    self.nazov = nazov

  def nastavNahlad(self, nahladLink):
    self.nahladLink = nahladLink

  def ziskajNahlad(self):
    nahlad = dajObrazok(self.nahladLink)
    self.nahlad = nahlad.resize((256, int(nahlad.height * 256 / nahlad.width)), PIL.Image.LANCZOS)

  def dajCestuObrazku(self):
    return 'data/datawebcam/' + self.id + '/'


class Parser (html.parser.HTMLParser):
  def nacitaj(self, stranka):
    data = stranka.read()
    self.feed(data.decode('utf8'))

  def dajAtribut(self, attrs, attrNazov):
    for attr in attrs:
      if attr[0] == attrNazov:
        return attr[1]
    return None

class KameraParser (Parser):
  def __init__(self):
    super().__init__()
    self.kamery = []
    self.kameraDivPocet = 0
    self.vNazveKamery = False
    self.aktualnaKamera = None

  def handle_starttag(self, tag, attrs):
    if self.kameraDivPocet == 0:
      if tag == 'div' and self.dajAtribut(attrs, 'id') == 'maincontent':
        self.kameraDivPocet = 1
    else:
      if tag == 'div':
        self.kameraDivPocet += 1
        if self.dajAtribut(attrs, 'class') == 'text-center':
          self.vNazveKamery = True
      elif tag == 'a':
        self.aktualnaKamera = Kamera(self.dajAtribut(attrs, 'href'))
      elif tag == 'img':
        if self.aktualnaKamera is not None:
          self.aktualnaKamera.nastavNahlad(self.dajAtribut(attrs, 'src'))

  def handle_endtag(self, tag):
    if tag == 'a' and self.aktualnaKamera is not None:
      self.kamery.append(self.aktualnaKamera)
      self.aktualnaKamera = None
    if tag == 'div' and self.kameraDivPocet > 0:
      self.kameraDivPocet -= 1

  def handle_data(self, data):
    if self.aktualnaKamera is not None and self.vNazveKamery:
      self.aktualnaKamera.nastavNazov(data)
      self.vNazveKamery = False

class ObrazkyParser (Parser):
  def __init__(self, kamera):
    super().__init__()
    self.kamera = kamera
    self.obrazky = []
    self.vSkripte = False

  def handle_starttag(self, tag, attrs):
    if tag == 'script':
      self.vSkripte = True

  def handle_endtag(self, tag):
    if self.vSkripte and tag == 'script':
      self.vSkripte = False

  def handle_data(self, data):
    if self.vSkripte and re.match(r'\s*var img_files*', data):
      vzor = re.compile(r'img_files\[\d*\]=\'(.*?)\';')
      start = 0
      while start >= 0:
        najdene = vzor.search(data, start)
        if najdene is not None:
          self.obrazky.append(najdene.group(1))
          start = najdene.end()
        else:
          start = -1


shmuAdresa = 'https://www.shmu.sk/'
shmuWebAdresa = shmuAdresa + 'sk/'
ssl._create_default_https_context = ssl._create_unverified_context
