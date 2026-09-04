import requests
from responses import _recorder
import pandas as pd
import numpy as np
import statistics
import sys
import datetime
from data_for_vis import prep_data, SQLConnection


# function requests historical market index price data - would use futures for a real pricing quote
@_recorder.record(file_path="..\\Tests\\Integration\\Fixtures\\fixture.yaml")
def midp_api_call(url):
    api_response = requests.get(
        url=url
    )

    data = api_response.json()["data"]
    return data


def dataframe_evaluation(data):
    dframe = pd.DataFrame(data=data)
    nulls = np.where(pd.isnull(dframe))
    if nulls[0].size == 0 and nulls[1].size == 0:
        sorted_df = dframe.sort_values(by=["settlementPeriod", "startTime"])
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


def excluding_midp_outliers(sorted_data, periods: list):
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
        outliers_df = pd.concat([outliers_df, a])

    excluding_outliers_df = excluding_outliers[0]
    for b in excluding_outliers[1:]:
        excluding_outliers_df = pd.concat([excluding_outliers_df, b])

    print(f"\nOutliers: \n {outliers_df.to_string()}")
    print(f"\nExcluding outliers: \n {excluding_outliers_df.to_string()}")

    return excluding_outliers_df

#Would also include other factors such operational costs and profit margins
def pricing_quote_variables(average_midp):
    print("What is their expected annual electricity use? (kWh)")
    annual_use = int(input())
    #Examples of using multipliers to determine pricing depending on a range of variables
    if annual_use < 100000:     #"micro"-sized business
        size_multiplier =  1.12
    elif 100000 <= annual_use  < 200000:    #"small"-sized business
        size_multiplier =  1.09
    elif 200000 <= annual_use  <= 500000:   #"medium"-sized business
        size_multiplier = 1.06
    elif annual_use > 500000:       #"large"-sized business
        size_multiplier = 1.03
    else:
        print("Please enter a valid quantity.")
        sys.exit()


    print("What is their desired rate?")
    rate = input().lower()
    if rate == 'fixed':
        rate_multiplier = 1.1
    elif rate == 'variable':
        rate_multiplier = 1.2   #Just an example, would differ depending on wholesale price variations
    elif rate == 'green':
        rate_multiplier = 1.12  #More expensive than fixed
    elif rate == 'deemed':
        rate_multiplier = 1.5   #Out of contract rates are the most expensive
    else:
        print("Please enter a valid rate.")
        sys.exit()

    print("What is their credit score risk? (1-100)")
    credit = int(input())

    #Examples of how multipliers could work - would involve a more complex calculation than this using other variables
    if credit > 80:   #"low"
        risk_multiplier = 1.1
    elif 40 <= credit < 80:   #"medium"
        risk_multiplier = 1.2
    elif credit < 40:     #"high"
        risk_multiplier = 1.35
    else:
        print("Please enter a valid credit score risk.")
        sys.exit()

    print(f"Multipliers:\nSize: {size_multiplier}\nRate: {rate_multiplier}\nRisk: {risk_multiplier}")

    combined_multiplier = size_multiplier * rate_multiplier * risk_multiplier

    calculated_price = round(combined_multiplier * average, 2)  #Price is in £/MWh
    converted_price = round(calculated_price / 10, 1)    #Converted into p/kWh

    return converted_price


if __name__ == "__main__":

    # Gets current settlement period and as far back a period as the API will allow (a week)
    curr_date = datetime.datetime.now().replace(microsecond=0, second=0)
    if curr_date.minute < 30:
        curr_date = curr_date.replace(minute=00)
    else:
        curr_date = curr_date.replace(minute=30)
    prev_date = (curr_date - datetime.timedelta(days=7)).replace(microsecond=0)

    # Constructing API url
    to_date = datetime.datetime.strftime(curr_date, "%Y-%m-%dT%H:%MZ")
    from_date = prev_date.strftime("%Y-%m-%dT%H:%MZ")

    api_url = f"https://data.elexon.co.uk/bmrs/api/v1//balancing/pricing/market-index?from={from_date}&to={to_date}&settlementPeriodTo=1&dataProviders=APXMIDP&format=json"

    print("Updating database or analysing?")
    resp = input().lower()
    if resp == "updating":

        df = dataframe_evaluation(midp_api_call(api_url))
        data = excluding_midp_outliers(df, settlement_periods())
        prepped_data = prep_data(data)
        obj = SQLConnection(prepped_data)
        obj.data_input()


    elif resp == "analysing":
        df = dataframe_evaluation(midp_api_call(api_url))
        data = excluding_midp_outliers(df, settlement_periods())
        midp = data.get("price")
        average = statistics.mean(midp)
        print(f"Average midp (excluding outliers): {round(average, 2)}")

        print(f"\nFinal price: {pricing_quote_variables(average)}p/kWh")

    else:
        print("Neither selected: closing script.")
        sys.exit()
