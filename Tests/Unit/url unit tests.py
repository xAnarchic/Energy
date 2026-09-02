import unittest
import datetime
import re


class TestUrlDate(unittest.TestCase):

    def setUp(self):
        self.date_param = "2026-08-25T00:30Z"
        self.date_param_past = "2026-08-25T00:00Z"

    def test_year_position(self):
        self.assertTrue(re.match("20[0-9]{2}" , self.date_param[0:4]) is not None)

    def test_year_value(self):
        self.assertEqual(self.date_param[0:4], str(datetime.datetime.today().year))

    def test_date_hyphens(self):
        match_indices = []
        for m in re.finditer("-", self.date_param):
            match_indices.append(m.start())
        self.assertEqual(match_indices, [4,7])

    def test_month_format(self):
        self.assertTrue(re.match("[0-1][0-9]", self.date_param[5:7]))

    def test_month_min(self):
        self.assertGreaterEqual(int(self.date_param[5:7]), 0)

    def test_month_max(self):
        self.assertLessEqual(int(self.date_param[5:7]), 12)

    def test_day_format(self):
        self.assertTrue(re.match("[0-2][0-9]", self.date_param[8:10]))

    def test_day_min(self):
        self.assertGreaterEqual(int(self.date_param[8:10]), 1)

    #Make an integration test that accounts for leap years (calendar module) and months with less than 31 days
    def test_day_max(self):
        self.assertLessEqual(int(self.date_param[8:10]), 31)

    def test_hour_format(self):
        self.assertTrue(re.match("[0-2][0-9]", self.date_param[11:13]))

    def test_hour_min(self):
        self.assertGreaterEqual(int(self.date_param[11:13]), 0)

    def test_hour_max(self):
        self.assertLessEqual(int(self.date_param[11:13]), 23)

    def test_minutes_format(self):
        self.assertTrue(re.match("[0,3]0", self.date_param[14:16]))

    def test_minutes_min(self):
        self.assertIn(int(self.date_param[14:16]), [00,30])

    def test_date_T(self):
        self.assertTrue(self.date_param[10] == "T")

    def test_date_Z(self):
        self.assertTrue(self.date_param[-1] == "Z")

    def test_date_formatting(self):
        formatted_date = datetime.datetime.strptime(self.date_param, "%Y-%m-%dT%H:%MZ")
        self.assertEqual(formatted_date, datetime.datetime(2026,8, 25, 0, 30))




if __name__ == "__main__":
    unittest.main()
