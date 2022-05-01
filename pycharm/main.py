#Import libreries
import requests
import pandas as pd
from datetime import datetime
import sqlite3
import sys

#Local files
from tables_optimization import *
from log import RollingLogger

#Setup
#---------------------------------------------
#Current date
now = datetime.now()
date_time = str(now.strftime("%Y%m%d"))

#Getting Bulk Data
#---------------------------------------------
#Downloading the full card json that is generated every day.
#More info about it in: https://scryfall.com/docs/api/bulk-data
def get_bulk_data(api_url):
    return requests.get(api_url)

def get_cards_dataframe(api_response):
    #Translate the response object's content from bytes to dictionary object so
    #it can be easily manipulate it
    api_json = api_response.json() #converts from bytes to dictionary

    #Get cards information from bulk data in the responsed url.
    bulk_url_json = requests.get(api_json['download_uri'], allow_redirects=True)

    #Save data to pandas
    # Load json data to a pandas Data frame.
    url_json = bulk_url_json.json()  # converts from bytes to dictionary
    pandas_df = pd.DataFrame(url_json)

    return pandas_df

def df_general_clean(cards_df):
    columns_list = ['id', 'name', 'image_uris', 'mana_cost', 'cmc', 'power',
                    'toughness', 'reserved', 'foil', 'nonfoil', 'set_id',
                    'set_name', 'rarity', 'frame', 'prices', 'date_time']

    #General Cleaning
    #---------------------------------------------------
    #Discard any card that's not in english
    cards_df_flt = cards_df.loc[cards_df["lang"] == "en"]
    #Discard the cards without image
    cards_df_flt = cards_df_flt.dropna(subset=['image_uris'])
    #Adds date_time to the Data frame
    cards_df_flt['date_time'] = date_time
    #Keep only necessary columns
    cards_df_flt = cards_df_flt[columns_list]

    #Split dictionary-like columns
    #---------------------------------------------------
    #Split dictonary column for cards images
    cards_df_flt = cards_df_flt.join(cards_df_flt.image_uris.apply(pd.Series), how='left')
    #Split dictonary column for cards prices
    cards_df_flt = cards_df_flt.join(cards_df_flt.prices.apply(pd.Series), how='left')
    #Drop innecesary columns after de split
    cards_df_flt.drop(["image_uris", "prices", "large", "png", "art_crop", "border_crop", "tix"],
                      axis=1, inplace=True)
    return cards_df_flt

def save_cards_to_local_db(cards_df):
    #Perform a general clean before storage
    clean_cards_df = df_general_clean(cards_df)

    #Divide dataframe into two different tables
    #   - scryfall_cards: Holds the cards static info(name, set, images, rarity, etc)
    #   - scryfall_daily_prices : Holds the cards columns variable in a daily basis
    #       (regular card price, foil price, etc)
    prices_df = clean_cards_df.copy(deep=True)
    prices_df = prices_df[['id', 'usd', 'usd_foil', 'usd_etched', 'eur', 'eur_foil', 'date_time']]
    prices_df.rename(columns={'id': 'card_id'}, inplace=True)

    cards_static_info_df = clean_cards_df.copy(deep=True)
    cards_static_info_df = cards_static_info_df[['id', 'name', 'mana_cost', 'cmc', 'power', 'toughness',
                                                 'reserved', 'foil', 'nonfoil', 'set_id', 'set_name',
                                                 'rarity', 'frame', 'small', 'normal', 'date_time']]
    cards_static_info_df.rename(columns={'id': 'card_id', 'date_time': 'last_update'}, inplace=True)

    #Connect to local DB
    # the .. indicates to go back a directory.
    # if it's at the same level then use "sqlite_db/mtg_cards.db" insted.
    conn = connect_to_sqlite_db("../sqlite_db/mtg_cards.db")

    #Load pandas dataframe into scryfall_cards table. Append Because it will add new prices each day.
    row_num = prices_df.to_sql(name="scryfall_daily_prices", con=conn, if_exists="append", index=False)
    logger.LOG.info(f"{datetime.now().strftime('%Y%m%d %H:%M:%S')}: {row_num} append to scryfall_daily_prices table")
    #Load pandas dataframe into scryfall_cards table. Replace existing because it's static info.
    row_num = cards_static_info_df.to_sql(name="scryfall_cards", con=conn, if_exists="replace", index=False)
    logger.LOG.info(f"{datetime.now().strftime('%Y%m%d %H:%M:%S')}: {row_num} replaced in scryfall_cards table")

    #Close connection
    disconnect_from_sqlite_db(conn)

if __name__ == '__main__':
    #Let's start the logger
    logger = RollingLogger(max_log_files=5)
    logger.LOG.info(f"{datetime.now().strftime('%Y%m%d %H:%M:%S')}: MTG Price Fetcher")

    #Get the api response for accessing the bulk data.
    api_response = get_bulk_data('https://api.scryfall.com/bulk-data/default-cards')
    if api_response.status_code != 200: #should be 200=ok
        print("Failled to get the api response")
        logger.ERROR.info(f"{datetime.now().strftime('%Y%m%d %H:%M:%S')}: Failled to get the api response")
        sys.exit()

    #Obtain cards dataframe from the response
    cards_bulk_df = get_cards_dataframe(api_response)

    save_cards_to_local_db(cards_bulk_df)

    #Clean and optimize database.
    table_optimization_analyses(logger, month_window=3)
