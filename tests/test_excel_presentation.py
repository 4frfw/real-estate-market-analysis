import runpy
import sys
import unittest
from pathlib import Path
from openpyxl import Workbook, load_workbook
import pandas as pd
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from analyze import calculate


class ExcelPresentationTests(unittest.TestCase):
    def test_saved_charts_and_conclusions(self):
        data = calculate(pd.read_csv(ROOT / 'data/raw/housing.csv'), pd.read_csv(ROOT / 'data/raw/macro.csv'))
        summary = {
            'primary_growth': (data.primary.iloc[-1]/data.primary.iloc[0]-1)*100,
            'secondary_growth': (data.secondary.iloc[-1]/data.secondary.iloc[0]-1)*100,
            'premium': data.premium.iloc[-1],
            'real_primary': data.primary_real_growth.iloc[-1],
            'real_secondary': data.secondary_real_growth.iloc[-1],
        }
        wb = Workbook()
        sheet = wb.active
        sheet.title = 'Data'
        sheet.append(list(data.columns))
        for row in data.itertuples(index=False, name=None):
            sheet.append([None if pd.isna(value) else value for value in row])
        enhance = runpy.run_path(str(ROOT / 'scripts/excel_presentation.py'))['enhance']
        enhance(wb, data, summary)
        enhance(wb, data, summary)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'market.xlsx'
            wb.save(path)
            restored = load_workbook(path)
            self.assertEqual(len(restored['Charts']._charts), 4)
            self.assertEqual([len(chart.series) for chart in restored['Charts']._charts], [2,3,2,2])
            self.assertEqual(restored.sheetnames.count('Conclusions'), 1)
            self.assertAlmostEqual(restored['Conclusions']['B3'].value, summary['primary_growth'])
            self.assertAlmostEqual(restored['Conclusions']['B6'].value, summary['real_primary'])
            self.assertIn('тыс. руб./м²', restored['Guide']['B2'].value)
            self.assertTrue(restored.calculation.fullCalcOnLoad)
            restored.close()


if __name__ == '__main__':
    unittest.main()
