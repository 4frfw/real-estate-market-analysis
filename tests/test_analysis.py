import sys,unittest
from pathlib import Path
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from analyze import calculate,payment,R
class Tests(unittest.TestCase):
 def setUp(self):self.h=pd.read_csv(R/'data/raw/housing.csv');self.m=pd.read_csv(R/'data/raw/macro.csv')
 def test_rows(self):self.assertEqual(len(calculate(self.h,self.m)),6)
 def test_real(self):self.assertAlmostEqual(calculate(self.h,self.m).primary_real_growth.iloc[-1],(108.8/109.52-1)*100)
 def test_premium(self):self.assertAlmostEqual(calculate(self.h,self.m).premium.iloc[-1],55.9158632778)
 def test_duplicate(self):
  with self.assertRaises(ValueError):calculate(pd.concat([self.h,self.h.iloc[:1]]),self.m)
 def test_mismatch(self):
  with self.assertRaises(ValueError):calculate(self.h,self.m.iloc[:-1])
 def test_negative(self):
  with self.assertRaises(ValueError):calculate(self.h.assign(primary=-1),self.m)
 def test_missing(self):
  with self.assertRaises(ValueError):calculate(self.h.assign(primary=float('nan')),self.m)
 def test_infinite(self):
  with self.assertRaises(ValueError):calculate(self.h.assign(primary=float('inf')),self.m)
 def test_zero(self):self.assertEqual(payment(0),25000)
 def test_payment(self):self.assertAlmostEqual(payment(8),50186.404138,places=4)
 def test_monotonic(self):self.assertLess(payment(8),payment(20))
 def test_first_missing(self):self.assertTrue(pd.isna(calculate(self.h,self.m).primary_mean_change.iloc[0]))
if __name__=='__main__':unittest.main(verbosity=2)
