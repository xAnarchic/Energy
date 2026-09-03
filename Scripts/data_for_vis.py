from Market_index_price import midp_api_call, dataframe_evaluation, settlement_periods, excluding_midp_outliers
import os
from dotenv import load_dotenv
import mysql.connector as connector
from mysql.connector import errorcode

class SQLConnection:

    def __init__(self, prepared_data):

        try:
            load_dotenv()
            self.connection = connector.connect(
                host=os.environ.get("HOST"),
                user=os.environ.get("USER"),
                password=os.environ.get("PASS"),
                database=os.environ.get("DATABASE")
            )

            self.data = prepared_data

        except connector.Error as err:
            if err.errno == connector.errorcode.ER_ACCESS_DENIED_ERROR:
                print('Cannot sign in')
            elif err is None:
                print("Successful connection")
            else:
                print({err}, "----")

    def table_creation(self):

        table = """
                CREATE TABLE IF NOT EXISTS midp_data(
                                            id INT NOT NULL auto_increment,
                                            start_time VARCHAR(255),
                                            data_provider VARCHAR(255),
                                            settlement_date VARCHAR(255),
                                            settlement_period VARCHAR(255),
                                            price VARCHAR(255),
                                            volume VARCHAR(255),
                                            primary key (id));
                """

        self.connection.cursor().execute(table)


    def data_input(self):

        insertion_query = "INSERT INTO midp_data (start_time, data_provider, settlement_date, settlement_period, price, volume) VALUES (%s, %s, %s, %s, %s, %s)"
        self.connection.reconnect()
        self.connection.cursor().executemany(insertion_query, self.data)
        self.connection.commit()


def prep_data(url):

    df = dataframe_evaluation(midp_api_call(url))
    data = excluding_midp_outliers(df, settlement_periods())

    #Converting dataframe into a list of tuples
    prepared_data = ([tuple(x) for x in data.itertuples(index = False)])

    return prepared_data



if __name__ == "__main__":

    initial_api_url = "https://data.elexon.co.uk/bmrs/api/v1//balancing/pricing/market-index?from=2026-08-25T00:00Z&to=2026-08-30T00:00Z&settlementPeriodTo=1&dataProviders=APXMIDP"
    prepped_data = prep_data(initial_api_url)
    obj = SQLConnection(prepped_data)
    obj.table_creation()    #Only call this once initially
    obj.data_input()