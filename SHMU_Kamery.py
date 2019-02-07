import urllib.request
import html.parser
import re

def dajZoznamKamier():
  parser = KameraParser()
  with urllib.request.urlopen(shmuAdresa + '?page=1&id=webkamery') as stranka:
    parser.feed(stranka.read().decode('utf-8'))
  return parser.kamery

def dajObrazkyKamery(kameraLink):
  parser = ObrazkyParser()
  with urllib.request.urlopen(shmuAdresa + kameraLink + '&c=360') as stranka:
    parser.feed(stranka.read().decode('utf-8'))
  return parser.obrazky


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
      self.kamery.append((self.aktualnaKamera, data))
      self.aktualnaKamera = None
      self.vNazveKamery = False


class ObrazkyParser (html.parser.HTMLParser):
  def __init__(self):
    super(ObrazkyParser, self).__init__()
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
          self.obrazky.append((najdene.group(2), najdene.group(1)))
          start = najdene.span()[1]
        else:
          start = -1


shmuAdresa = 'http://www.shmu.sk/sk/'

if __name__ == '__main__':
  rslt = urllib.request.urlopen('http://www.shmu.sk/sk/?page=1&id=webkamery')
  pass