import unittest
import SHMU_Kamery
import re
import PIL.Image
import os
import os.path
import ffmpeg

class Test_Kamery(unittest.TestCase):
  def test_zoznamKamier(self):
    kamery = SHMU_Kamery.dajZoznamKamier()
    self.assertGreater(len(kamery), 0)
    for kamera in kamery:
      self.assertIsInstance(kamera, SHMU_Kamery.Kamera)
      self.assertTrue(kamera.id.startswith('hdcam'))
      self.assertTrue(kamera.link.startswith('?page=1&id=webkamery&kamera=hdcam'))
      self.assertIsInstance(kamera.nazov, str)
      self.assertGreater(len(kamera.nazov), 0)
      self.assertIsNotNone(kamera.nahladLink)
      self.assertIsNotNone(re.match(r'/data/datawebcam/' + kamera.id + r'/\d{8}_\d{6}.jpg', kamera.nahladLink))

  def test_kamerySNahladmi(self):
    for kamera in SHMU_Kamery.dajKamerySNahladmi():
      self.assertIsInstance(kamera, SHMU_Kamery.Kamera)
      self.assertTrue(kamera.id.startswith('hdcam'))
      self.assertTrue(kamera.link.startswith('?page=1&id=webkamery&kamera=hdcam'))
      self.assertIsInstance(kamera.nazov, str)
      self.assertGreater(len(kamera.nazov), 0)
      self.assertEqual(kamera.nahlad.width, 256)
      self.assertGreater(kamera.nahlad.height, 180)
      self.assertLess(kamera.nahlad.height, 200)
      self.assertEqual(kamera.nahlad.mode, 'RGB')

  def test_kameraObrazky(self):
    kamery = SHMU_Kamery.dajZoznamKamier()
    obrazky = SHMU_Kamery.dajObrazkyKamery(kamery[0])
    self.assertEqual(len(obrazky), 360)
    for obrazok in obrazky:
      self.assertIsInstance(obrazok, str)
      self.assertIsNotNone(re.match(r'/data/datawebcam/' + kamery[0].id + r'/\d{8}_\d{6}.jpg', obrazok))
      #self.assertIsInstance(obrazok.nazov, str)
      #self.assertGreater(len(obrazok.nazov), 0)

  def test_ziskanieObrazku(self):
    kamery = SHMU_Kamery.dajZoznamKamier()
    obrazky = SHMU_Kamery.dajObrazkyKamery(kamery[0])
    obrazok = SHMU_Kamery.dajObrazok(obrazky[0])
    self.assertGreater(obrazok.width, 512)
    self.assertGreater(obrazok.height, 400)
    self.assertEqual(obrazok.format, 'JPEG')

  def test_vytvorVideo(self):
    subor = pripravTestZlozku('testVideo.avi')
    obrazky = [generujObrazok(param) for param in range(25)]
    SHMU_Kamery.vytvorAnimaciu(obrazky, subor, AnimParametre(10))
    self.assertTrue(os.path.exists(subor))
    videoTest = ffmpeg.probe(subor)
    videoData = next((video for video in videoTest['streams'] if video['codec_type'] == 'video'), None)
    self.assertEqual(int(videoData['width']), 300)
    self.assertEqual(int(videoData['height']), 200)
    self.assertEqual(eval(videoData['avg_frame_rate']), 10)
    self.assertEqual(float(videoData['duration']), 2.5)
    self.assertEqual(int(videoData['nb_frames']), 25)

  def test_vytvorGif(self):
    subor = pripravTestZlozku('testAnim.gif')
    obrazky = [generujObrazok(param) for param in range(25)]
    SHMU_Kamery.vytvorAnimaciu(obrazky, subor, AnimParametre(10, 500, 4))
    self.assertTrue(os.path.exists('testdata/testAnim.gif'))
    gifImage = PIL.Image.open(subor)
    self.assertEqual(gifImage.size, (300, 200))
    gifImage.seek(24)
    self.assertEqual(gifImage.tell(), 24)
    with self.assertRaises(EOFError):
      gifImage.seek(25)

def generujObrazok(param):
  pozicia = abs(param % 100 - 50)
  obrazok = PIL.Image.new('RGB', (300, 200), 0xffffff)
  for x in range(100 + pozicia, 150 + pozicia):
    for y in range(80, 120):
      obrazok.putpixel((x, y), 0xff0000)
  return obrazok

def pripravTestZlozku(subor):
  zlozka = 'testData'
  if not os.path.exists(zlozka):
    os.mkdir(zlozka)
  suborVZlozke = os.path.join(zlozka, subor)
  if os.path.exists(suborVZlozke):
    os.unlink(suborVZlozke)
  return suborVZlozke

class AnimParametre:
  def __init__(self, rychlost, koncovyInterval=0, opakovania=1):
    self.rychlost = rychlost
    self.koncovyInterval = koncovyInterval
    self.opakovania = opakovania

  def dajRychlost(self):
    return self.rychlost

  def dajGifOpakovania(self):
    return self.opakovania

  def dajKoncovyInterval(self):
    return self.koncovyInterval


class Test_NastrojeParsera(unittest.TestCase):
  def test_dajAtribut(self):
    attrs = (('id', 'mainclass'),('href', 'http://link.address.com'),('class_name', 'test class'))
    parser = SHMU_Kamery.Parser()
    self.assertEqual(parser.dajAtribut(attrs, 'pokus'), None)
    self.assertEqual(parser.dajAtribut(attrs, 'href'), 'http://link.address.com')
    self.assertEqual(parser.dajAtribut(attrs, 'id'), 'mainclass')
    self.assertEqual(parser.dajAtribut(attrs, 'invalid'), None)

  def test_spracujObrazky(self):
    testKamera = SHMU_Kamery.Kamera('?page=1&id=webkamery&kamera=hdcam06')
    parser = SHMU_Kamery.ObrazkyParser(testKamera)
    parser.vSkripte = True
    obrazky = parser.handle_data('''  var img_files = new Array();
      img_files[0]='/data/datawebcam/hdcam01/20211130_190000.jpg'; 
      img_files[1]='/data/datawebcam/hdcam01/20211130_185800.jpg'; 
      img_files[2]='/data/datawebcam/hdcam01/20211130_185600.jpg';''')
    self.assertEqual(len(parser.obrazky), 3)
    self.assertEqual(parser.obrazky[0], '/data/datawebcam/hdcam01/20211130_190000.jpg')
    self.assertEqual(parser.obrazky[1], '/data/datawebcam/hdcam01/20211130_185800.jpg')
    self.assertEqual(parser.obrazky[2], '/data/datawebcam/hdcam01/20211130_185600.jpg')


if __name__ == '__main__':
  unittest.main()
