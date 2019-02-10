import unittest
import SHMU_Kamery
import re
import PIL.Image
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
      self.assertGreater(kamera.nahlad.width, 512)
      self.assertGreater(kamera.nahlad.height, 400)
      self.assertEqual(kamera.nahlad.format, 'JPEG')

  def test_kameraObrazky(self):
    kamery = SHMU_Kamery.dajZoznamKamier()
    obrazky = SHMU_Kamery.dajObrazkyKamery(kamery[0])
    self.assertEqual(len(obrazky), 360)
    for obrazok in obrazky:
      self.assertIsInstance(obrazok, SHMU_Kamery.Obrazok)
      self.assertIsNotNone(re.match(r'data/datawebcam/' + kamery[0].id + r'/\d{8}_\d{6}.jpg', obrazok.link))
      self.assertIsInstance(obrazok.nazov, str)
      self.assertGreater(len(obrazok.nazov), 0)

  def test_ziskanieObrazku(self):
    kamery = SHMU_Kamery.dajZoznamKamier()
    obrazky = SHMU_Kamery.dajObrazkyKamery(kamery[0])
    obrazok = SHMU_Kamery.dajObrazok(obrazky[0])
    self.assertGreater(obrazok.width, 512)
    self.assertGreater(obrazok.height, 400)
    self.assertEqual(obrazok.format, 'JPEG')

  def test_vytvorVideo(self):
    if os.path.exists('testdata/testVideo.avi'):
      os.unlink('testdata/testVideo.avi')
    obrazky = [generujObrazok(param) for param in range(25)]
    SHMU_Kamery.vytvorVideo(obrazky, 'testdata/testVideo.avi', 10)
    self.assertTrue(os.path.exists('testdata/testVideo.avi'))
    videoTest = ffmpeg.probe('testdata/testVideo.avi')
    videoData = next((video for video in videoTest['streams'] if video['codec_type'] == 'video'), None)
    self.assertEqual(int(videoData['width']), 300)
    self.assertEqual(int(videoData['height']), 200)
    self.assertEqual(eval(videoData['avg_frame_rate']), 10)
    self.assertEqual(float(videoData['duration']), 2.5)
    self.assertEqual(int(videoData['nb_frames']), 25)


def generujObrazok(param):
  pozicia = abs(param % 100 - 50)
  obrazok = PIL.Image.new('RGB', (300, 200), 0xffffff)
  for x in range(100 + pozicia, 150 + pozicia):
    for y in range(80, 120):
      obrazok.putpixel((x, y), 0xff0000)
  return obrazok

class Test_NastrojeParsera(unittest.TestCase):
  def test_dajAtribut(self):
    attrs = (('id', 'mainclass'),('href', 'http://link.address.com'),('class_name', 'test class'))
    self.assertEqual(SHMU_Kamery.dajAtribut(attrs, 'pokus'), None)
    self.assertEqual(SHMU_Kamery.dajAtribut(attrs, 'href'), 'http://link.address.com')
    self.assertEqual(SHMU_Kamery.dajAtribut(attrs, 'id'), 'mainclass')
    self.assertEqual(SHMU_Kamery.dajAtribut(attrs, 'invalid'), None)

  def test_spracujObrazky(self):
    testKamera = SHMU_Kamery.Kamera('?page=1&id=webkamery&kamera=hdcam06')
    parser = SHMU_Kamery.ObrazkyParser(testKamera)
    parser.vSkripte = True
    obrazky = parser.handle_data('''  var img_dts = new Array(); var img_files = new Array();
      img_dts[0]='07.02.2019 05:04 SEČ'; img_files[0]='20190207_050400.jpg';
      img_dts[1]='07.02.2019 05:06 SEČ'; img_files[1]='20190207_050600.jpg';
      img_dts[2]='07.02.2019 05:08 SEČ'; img_files[2]='20190207_050800.jpg';''')
    self.assertEqual(len(parser.obrazky), 3)
    self.assertEqual(parser.obrazky[0], SHMU_Kamery.Obrazok(testKamera, ('07.02.2019 05:04 SEČ', '20190207_050400.jpg')))
    self.assertEqual(parser.obrazky[1], SHMU_Kamery.Obrazok(testKamera, ('07.02.2019 05:06 SEČ', '20190207_050600.jpg')))
    self.assertEqual(parser.obrazky[2], SHMU_Kamery.Obrazok(testKamera, ('07.02.2019 05:08 SEČ', '20190207_050800.jpg')))


if __name__ == '__main__':
  unittest.main()
