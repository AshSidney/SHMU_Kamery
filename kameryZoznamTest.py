import unittest
import SHMU_Kamery

class Test_Kamery(unittest.TestCase):
  def test_zoznamKamier(self):
    kamery = SHMU_Kamery.dajZoznamKamier()
    self.assertGreater(len(kamery), 0)
    for kamera in kamery:
      self.assertIsInstance(kamera, tuple)
      self.assertEqual(len(kamera), 2)
      self.assertIsInstance(kamera[0], str)
      self.assertTrue(kamera[0].startswith('?page=1&id=webkamery&kamera=hdcam'))
      self.assertIsInstance(kamera[1], str)
      self.assertGreater(len(kamera[1]), 0)

  def test_kameraObrazky(self):
    kamery = SHMU_Kamery.dajZoznamKamier()
    obrazky = SHMU_Kamery.dajObrazkyKamery(kamery[0][0])
    self.assertEqual(len(obrazky), 360)

class Test_NastrojeParsera(unittest.TestCase):
  def test_dajAtribut(self):
    attrs = (('id', 'mainclass'),('href', 'http://link.address.com'),('class_name', 'test class'))
    self.assertEqual(SHMU_Kamery.dajAtribut(attrs, 'pokus'), None)
    self.assertEqual(SHMU_Kamery.dajAtribut(attrs, 'href'), 'http://link.address.com')
    self.assertEqual(SHMU_Kamery.dajAtribut(attrs, 'id'), 'mainclass')
    self.assertEqual(SHMU_Kamery.dajAtribut(attrs, 'invalid'), None)

  def test_spracujObrazky(self):
    parser = SHMU_Kamery.ObrazkyParser()
    parser.vSkripte = True
    obrazky = parser.handle_data('''  var img_dts = new Array(); var img_files = new Array();
      img_dts[0]='07.02.2019 05:04 SEČ'; img_files[0]='20190207_050400.jpg';
      img_dts[1]='07.02.2019 05:06 SEČ'; img_files[1]='20190207_050600.jpg';
      img_dts[2]='07.02.2019 05:08 SEČ'; img_files[2]='20190207_050800.jpg';''')
    self.assertEqual(len(parser.obrazky), 3)
    self.assertEqual(parser.obrazky[0], ('20190207_050400.jpg', '07.02.2019 05:04 SEČ'))
    self.assertEqual(parser.obrazky[1], ('20190207_050600.jpg', '07.02.2019 05:06 SEČ'))
    self.assertEqual(parser.obrazky[2], ('20190207_050800.jpg', '07.02.2019 05:08 SEČ'))


if __name__ == '__main__':
  unittest.main()
