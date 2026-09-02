import responses
import requests
import unittest
import datetime



class TestAPIUrl(unittest.TestCase):

    def setUp(self):
        self.str_date = "2026-08-25T00:30Z"
        self.curr_formatted_date =  datetime.datetime.strptime("2026-08-25T00:30Z", "%Y-%m-%dT%H:%MZ")

    def test_comparing_settlement_dates(self):
        past_date = self.curr_formatted_date - datetime.timedelta(hours=3)
        self.assertGreater(self.curr_formatted_date, past_date)


class TestAPIResponse(unittest.TestCase):

    @responses.activate
    def setUp(self):
        responses._add_from_file(file_path="..\\Fixtures\\api_response.yaml")
        api = requests.get("https://data.elexon.co.uk/bmrs/api/v1/balancing/pricing/market-index?from=2026-08-25T23%3A00Z&to=2026-08-30T23%3A00Z&settlementPeriodFrom=1&settlementPeriodTo=50&dataProviders=APXMIDP&format=json")
        self.api = api.json()

    #API limits request period to a week
    def test_settlement_periods(self):
        self.assertLessEqual(len(self.api["data"]), 336)


if __name__ == "__main__":
    unittest.main()

