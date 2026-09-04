import requests
from responses import _recorder
import pandas as pd
import numpy as np
import statistics
import sys
import datetime
from data_for_vis import prep_data, SQLConnection



#function requests historical market index price data - would use futures for a real pricing quote
@_recorder.record(file_path="..\\Tests\\Integration\\Fixtures\\fixture.yaml")
def midp_api_call(url):

    api_response = requests.get(
        url = url
    )

    data = api_response.json()["data"]
    return data

def dataframe_evaluation(data):

    dframe = pd.DataFrame(data = data)
    nulls = np.where(pd.isnull(dframe))
    if nulls[0].size == 0 and nulls[1].size == 0:
        sorted_df = dframe.sort_values(by = ["settlementPeriod", "startTime"])
        return sorted_df

def settlement_periods():

    all_periods = []
    try:
        print("How many settlement periods are you interested in?")
        period_num = int(input())

        for settlement_period in range(period_num):
            print(f"Enter your settlement periods, one at a time: \n{settlement_period + 1}):")
            period = int(input())
            all_periods.append(period)

        print(f"You have selected the following settlement periods: {all_periods}. Is this correct? (y/n)")
        confirmation = input()

        while True:
            if confirmation == "y":
                break
            elif confirmation == "n":
                settlement_periods()
            else:
                print("Please select either \"y\" or \"n\".")
                confirmation = input()
                continue

    except ValueError:
            print("Please enter a number")

    return all_periods


def excluding_midp_outliers(sorted_data, periods : list):

    all_outliers = []
    excluding_outliers = []

    for per in periods:
        period = sorted_data.loc[sorted_data["settlementPeriod"] == per]
        print(f"\n---------Settlement period: {per}:---------\n", period)
        price_of_per = period.get("price")
        q1 = price_of_per.quantile(0.25, interpolation="midpoint")
        q3 = price_of_per.quantile(0.75, interpolation="midpoint")
        iqr = q3 - q1
        outlier_max = q3 + (1.5 * iqr)
        outlier_min = q1 - (1.5 * iqr)

        outliers = period.loc[(period["price"] < outlier_min) | (period["price"] > outlier_max)]
        all_outliers.append(outliers)

        non_outliers = period.loc[(period["price"] > outlier_min) & (period["price"] < outlier_max)]
        excluding_outliers.append(non_outliers)

    outliers_df = all_outliers[0]
    for a in all_outliers[1:]:
        outliers_df = pd.concat([outliers_df,a])

    excluding_outliers_df = excluding_outliers[0]
    for b in excluding_outliers[1:]:
        excluding_outliers_df = pd.concat([excluding_outliers_df,b])

    print(f"\nOutliers: \n {outliers_df.to_string()}")
    print(f"\nExcluding outliers: \n {excluding_outliers_df.to_string()}")

    return excluding_outliers_df


def pricing_quote_variables():
    print("What is their expected annual electricity use? (kWh)")
    annual_use = int(input())
    if annual_use < 100000:
        business_class = "micro"
    elif annual_use >= 100000 and annual_use < 200000:
        business_class = "small"
    elif annual_use > 500000:
        business_class = "large"
    else:
        print("Please enter a valid quantity.")
    
    print("What is their desired rate?")
    rate = input().lower((
    if rate == 'fixed':
        pass
    elif rate == 'variable':
        pass
    elif rate == 'green':
        pass
    elif rate == 'deemed':
        pass
    else:
    print("Please enter a valid rate.")
    
    print("What is their credit score?")
    credit = int(input())
    if credit > 80:
        risk = "low"
    elif credit <80 and credit >= 40:
        risk = "medium"
    elif credit < 40:
        risk = "high"
    
    #Use multipliers depending on each variable


if __name__ == "__main__":
    print("Updating database or analysing?")
    resp = input().lower()
    if resp == "updating":
        #Gets current settlement period and as far back a period as the API will allow (a week)
        curr_date = datetime.datetime.now().replace(microsecond = 0, second = 0)
        print(curr_date.minute)
        if curr_date.minute < 30:
            curr_date = curr_date.replace(minute = 00)
        else:
            curr_date = curr_date.replace(minute = 30)
        prev_date = (curr_date - datetime.timedelta(days = 7)).replace(microsecond = 0)

        #Constructing API url
        from_date = datetime.datetime.strftime(curr_date, "%Y-%m-%dT%H:%MZ")
        to_date = prev_date.strftime("%Y-%m-%dT%H:%MZ")

        api_url_constructor = f"https://data.elexon.co.uk/bmrs/api/v1//balancing/pricing/market-index?from={from_date}&to={to_date}&settlementPeriodTo=1&dataProviders=APXMIDP&format=json"

        prepped_data = prep_data(api_url_constructor)

        obj = SQLConnection(prepped_data)
        obj.data_input()

        pass
    elif resp == "analysing":
        df = dataframe_evaluation(midp_api_call())
        data = excluding_midp_outliers(df, settlement_periods())
        midp = data.get("price")
        average = statistics.mean(midp)
        print(f"Average midp (excluding outliers): {round(average, 2)}")
    else:
        print("Neither selected: closing script.")
        sys.exit()
#hi