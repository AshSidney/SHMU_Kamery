import urllib.request
import html.parser

def dajZoznamKamier():
  kamery = KameraParser()
  with urllib.request.urlopen(shmuAdresa + '?page=1&id=webkamery') as stranka:
    kamery.feed(stranka.read().decode('utf-8'))
  return kamery.kamery


class KameraParser (html.parser.HTMLParser):
  def __init__(self):
    super(KameraParser, self).__init__()
    self.kamery = []
    self.kameraDivPocet = 0
    self.aktualnaKamera = None
    self.vNazveKamery = False

  def dajAtribut(self, attrs, attrNazov):
    for attr in attrs:
      if attr[0] == attrNazov:
        return attr[1]
    return None

  def handle_starttag(self, tag, attrs):
    if self.kameraDivPocet == 0:
      if tag == 'div' and self.dajAtribut(attrs, 'id') == 'maincontent':
        self.kameraDivPocet = 1
    else:
      if tag == 'div':
        self.kameraDivPocet += 1
      elif tag == 'a':
        self.aktualnaKamera = self.dajAtribut(attrs, 'href')
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


shmuAdresa = 'http://www.shmu.sk/sk/'

if __name__ == '__main__':
  rslt = urllib.request.urlopen('http://www.shmu.sk/sk/?page=1&id=webkamery')
  pass