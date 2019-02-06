import urllib
import html.parser

def dajZoznamKamier():
  return []

class KameraParser (html.parser.HTMLParser):
  def __init__(self):
    self.kameraDivPocet = 0

  def dajAtribut(self, attrs, attrNazov):
    for attr in attrs:
      if attr[0] == attrNazov:
        return attr[1]
    return None

  def handle_starttag(self, tag, attrs):
    if tag == 'div':
      if self.kameraDivPocet == 0:
        if self.dajAtribut(attrs, 'id') == 'maincontent':
          self.kameraDivPocet = 1
      else:
        self.kameraDivPocet += 1
    elif tag == 'a':
      pass

if __name__ == '__main__':
  rslt = urllib.request.urlopen('http://www.shmu.sk/sk/?page=1&id=webkamery')
  pass