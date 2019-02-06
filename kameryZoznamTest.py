import unittest
import SHMU_Kamery

class Test_kameryZoznam(unittest.TestCase):
  def test_zoznamKamier(self):
    kamery = SHMU_Kamery.dajZoznamKamier()
    self.assertGreater(len(kamery), 0)

class Test_KameraParser(unittest.TestCase):
  def test_dajAtribut(self):
    attrs = (('id', 'mainclass'),('href', 'http://link.address.com'),('class_name', 'test class'))
    testParser = SHMU_Kamery.KameraParser()
    self.assertEqual(testParser.dajAtribut(attrs, 'pokus'), None)
    self.assertEqual(testParser.dajAtribut(attrs, 'href'), 'http://link.address.com')
    self.assertEqual(testParser.dajAtribut(attrs, 'id'), 'mainclass')
    self.assertEqual(testParser.dajAtribut(attrs, 'invalid'), None)

if __name__ == '__main__':
  unittest.main()
