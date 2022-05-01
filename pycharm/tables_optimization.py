#Import libreries
import pandas as pd
from datetime import datetime, timedelta

import sqlite3

## SQL Functions
#------------------------------------------------------------------------------------
def connect_to_sqlite_db(db_path):
    #Generates (or creates if it doesn't exist) the db connection.
    conn = sqlite3.connect(db_path)
    return conn

def apply_command_to_sqlite_db(conn):
    #Applies the command
    conn.commit()
    return

def disconnect_from_sqlite_db(conn):
    #Close connection
    conn.close()
    return

def get_table_names(conn):
    sql_result = conn.execute(
        """ SELECT
                name
            FROM 
                sqlite_master
            WHERE
                type='table'
    ;""")
    return sql_result.fetchall()

## Date Functions
#------------------------------------------------------------------------------------
def get_month_first_day(year_month):
    #year_month: '202204'
    firstday = str(datetime(int(year_month[:-2]), int(year_month[4:]), 1).strftime("%Y%m%d"))
    return firstday


def get_month_last_day(year_month):
    #year_month: '202204'
    if int(year_month[4:]) == 12:
        firstday_next_month = datetime(int(year_month[:-2]) + 1, 1, 1)
    else:
        firstday_next_month = datetime(int(year_month[:-2]), int(year_month[4:]) + 1, 1)
    lastday = str((firstday_next_month - timedelta(days=1)).strftime("%Y%m%d"))
    return lastday

## Month Analyses Functions
#------------------------------------------------------------------------------------
def get_cards_daily_data():
    #Connect to local DB
    # the .. indicates to go back a directory.
    #if it's at the same level then use "sqlite_db/mtg_cards.db" insted.
    conn = connect_to_sqlite_db("../sqlite_db/mtg_cards.db")

    #SQL query for testing
    sql_result = conn.execute(
        """ SELECT
                scryfall_daily_prices.card_id,
                scryfall_daily_prices.usd,
                scryfall_daily_prices.usd_foil,
                scryfall_daily_prices.date_time
            FROM 
                scryfall_daily_prices
    ;""")

    #Obtains the table column names because sqlite query returns only the data.
    colums_names = [column[0] for column in sql_result.description]
    #Creates a pandas dataframe qith the query data and the column names.
    daily_sql_df = pd.DataFrame.from_records(data=sql_result.fetchall(), columns=colums_names)

    #Close connection
    disconnect_from_sqlite_db(conn)

    return daily_sql_df

def number_of_full_months(unique_day_list):
    year_month_list = [x[:-2] for x in unique_day_list]
    unique_year_month_list = list(set(year_month_list))

    full_month = []
    for year_month in unique_year_month_list:
        if get_month_first_day(year_month) in unique_day_list and \
                get_month_last_day(year_month) in unique_day_list:
            full_month.append(year_month)

    return full_month

def save_to_month_db_table(month_dataframe, logger):
    #Connect to local DB
    conn = connect_to_sqlite_db("../sqlite_db/mtg_cards.db")

    #Load pandas dataframe into scryfall_monthly_prices table. Append Because it will add new prices each month
    row_num = month_dataframe.to_sql(name="scryfall_monthly_prices", con=conn, if_exists="append", index=False)
    logger.LOG.info(f"{datetime.now().strftime('%Y%m%d %H:%M:%S')}: {row_num} append to scryfall_monthly_prices table")

    #Close connection
    disconnect_from_sqlite_db(conn)
    return

def drop_oldest_month(start_date, end_date, logger):
    #Connect to local DB
    conn = connect_to_sqlite_db("../sqlite_db/mtg_cards.db")

    #SQL query for testing
    conn.execute(
        """ DELETE
            FROM 
                scryfall_daily_prices
            WHERE
            scryfall_daily_prices.date_time BETWEEN '""" + start_date + """' AND '""" + end_date + """'
    ;""")
    #Applies the command
    apply_command_to_sqlite_db(conn)

    #Cleans the pages and tables. Otherwise the size remains the same.
    conn.execute("""VACUUM;""")
    #Applies the command
    apply_command_to_sqlite_db(conn)

    #Close connection
    disconnect_from_sqlite_db(conn)

    logger.WARNING.info(f"{datetime.now().strftime('%Y%m%d %H:%M:%S')}: Information between {start_date} "
                    f"and {end_date} was deleted from scryfall_daily_prices table.")
    print(f"Information between {start_date} and {end_date} was deleted from scryfall_daily_prices table.")
    return

def compact_oldest_month(daily_df, year_month_list, month_window, logger):
    #year_month: '202204'
    year_month_list.sort()
    month_list = [int(x[4:]) for x in year_month_list]
    month_list.sort()

    #Generate month number auxiliar column
    daily_df['month_num'] = pd.DatetimeIndex(daily_df['date_time']).month
    #number of month to compact
    compact_num = len(month_list) - month_window

    for mun in range(0, compact_num):
        month_df = daily_df[daily_df['month_num'] == month_list[mun]].copy()
        #Add reference to '202204' for table orientation purpouses
        month_df['month'] = year_month_list[mun]
        #Grouping based on required values (reset_index solves the doble-header level)
        month_df2 = month_df.groupby(['card_id', 'month', 'month_num']).agg(
            usd_start=('usd', 'first'), usd_max=('usd', 'max'), usd_min=('usd', 'min'), usd_end=('usd', 'last'),
            usd_avg=('usd', 'mean'),
            usd_foil_start=('usd_foil', 'first'), usd_foil_max=('usd_foil', 'max'), usd_foil_min=('usd_foil', 'min'),
            usd_foil_end=('usd_foil', 'last'), usd_foil_avg=('usd_foil', 'mean')).reset_index()

        #Store the compact month in the month db table
        month_df2.drop('month_num', axis=1, inplace=True)
        save_to_month_db_table(month_df2, logger)

        #Once compact is done we drop the month data from the daily table
        drop_oldest_month(get_month_first_day(year_month_list[mun]),
                          get_month_last_day(year_month_list[mun]), logger)

        #print(month_df2.head(10))
        #month_df2.to_csv("test/compact.csv", sep=";")
    return

def monthly_compacting(month_window, logger):

    #Get all the daily cards info currently available
    all_daily_df = get_cards_daily_data()
    #all_daily_df = pd.read_csv("test/replenish_test.csv", sep=";")
    all_daily_df['date_time'] = all_daily_df['date_time'].astype(str)

    month_list = number_of_full_months(all_daily_df['date_time'].unique())
    #Check if compacting is needed
    if len(month_list) < month_window + 1:
        logger.LOG.info(f"{datetime.now().strftime('%Y%m%d %H:%M:%S')}: No need for monthly optimization.")
        #Not yet enough data
        return

    #Let's compact and save to the monthly table
    logger.LOG.info(f"{datetime.now().strftime('%Y%m%d %H:%M:%S')}: Monthly optimizarion is needed.")
    logger.LOG.info(f"{datetime.now().strftime('%Y%m%d %H:%M:%S')}: {len(month_list)} month of daily data found.")
    compact_oldest_month(all_daily_df, month_list, month_window, logger)
    return


def table_optimization_analyses(logger, month_window=3, annual_window=1):
    #Evaluate possible monthly compacting of daily data.
    monthly_compacting(month_window, logger)
    return