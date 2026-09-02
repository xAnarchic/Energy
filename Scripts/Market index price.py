import requests
from responses import _recorder
import pandas as pd
import numpy as np
import statistics


#function requests historical market index price data - would use futures for a real pricing quote
@_recorder.record(file_path="..\\Tests\\Integration\\Fixtures\\fixture.yaml")
def midp_api_call():

    api_response = requests.get(
        url = 'https://data.elexon.co.uk/bmrs/api/v1/balancing/pricing/market-index?from=2026-08-25T23%3A00Z&to=2026-08-30T23%3A00Z&settlementPeriodFrom=1&settlementPeriodTo=50&dataProviders=APXMIDP&format=json'
    )

    data = api_response.json()["data"]
    return data

def dataframe_evaluation(data):

    dframe = pd.DataFrame(data = data)
    nulls = np.where(pd.isnull(dframe))
    if nulls[0].size == 0 and nulls[1].size == 0:
        sorted_df = dframe.sort_values(by = ["settlementPeriod", "startTime"])
        return sorted_df


def detecting_midp_outliers(sorted_data):

    period = sorted_data.loc[sorted_data["settlementPeriod"] == 3]
    price_of_period = period.get("price")
    print(period.to_string())

    average = statistics.mean(price_of_period)
    q1 = price_of_period.quantile(0.25, interpolation="midpoint")
    q3 = price_of_period.quantile(0.75, interpolation="midpoint")
    iqr = q3 - q1
    outlier_min = q3 + (1.5 * iqr)
    outlier_max = q1 - (1.5 * iqr)
    print(average)

    print(period.loc[(period["price"] < outlier_min) | (period["price"] > outlier_max)])

if __name__ == "__main__":
    df = dataframe_evaluation(midp_api_call())
    detecting_midp_outliers(df)