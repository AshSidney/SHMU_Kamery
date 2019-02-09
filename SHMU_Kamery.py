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
    .output(videoSubor)
    .overwrite_output()
    .run_async(pipe_stdin=True)
    )
  for obrazok in obrazky:
    video.stdin.write(obrazok.tobytes())
  video.stdin.close()
  video.wait()


class Kamera:
  def __init__(self, link, nazov):
    self.link = link
    self.nazov = nazov
    self.id = re.match(r'\?page=1&id=webkamery&kamera=(.*)', self.link).group(1)

  def dajCestuObrazku(self):
    return 'data/datawebcam/' + self.id + '/'

class Obrazok:
  def __init__(self, kamera, data):
    self.nazov = data[0]
    self.link = kamera.dajCestuObrazku() + data[1]

  def __eq__(self, value):
    return self.nazov == value.nazov and self.link == value.link


def dajAtribut(attrs, attrNazov):
  for attr in attrs:
    if attr[0] == attrNazov:
      return attr[1]
  return None


class KameraParser (html.parser.HTMLParser):
  def __init__(self):
    super(KameraParser, self).__init__()
    self.kamery = []
    self.kameraDivPocet = 0
    self.aktualnaKamera = None
    self.vNazveKamery = False

  def handle_starttag(self, tag, attrs):
    if self.kameraDivPocet == 0:
      if tag == 'div' and dajAtribut(attrs, 'id') == 'maincontent':
        self.kameraDivPocet = 1
    else:
      if tag == 'div':
        self.kameraDivPocet += 1
      elif tag == 'a':
        self.aktualnaKamera = dajAtribut(attrs, 'href')
      elif tag == 'h3':
        self.vNazveKamery = True

  def handle_endtag(self, tag):
    if tag == 'div' and self.kameraDivPocet > 0:
      self.kameraDivPocet -= 1

  def handle_data(self, data):
    if self.aktualnaKamera is not None and self.vNazveKamery:
      self.kamery.append(Kamera(self.aktualnaKamera, data))
      self.aktualnaKamera = None
      self.vNazveKamery = False


class ObrazkyParser (html.parser.HTMLParser):
  def __init__(self, kamera):
    super(ObrazkyParser, self).__init__()
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
