
import datetime as dt
from datetime import timedelta,date
from test import low_break
import pandas as pd
import pandas_ta as ta
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time  ##token, expiry, livedata
import datetime as dt
import requests
import pandas as pd
from ta.momentum import rsi
import time
from kiteconnect import KiteConnect



def getCssElement(driver, cssSelector):
    return WebDriverWait(driver, 100).until(EC.presence_of_element_located((By.CSS_SELECTOR, cssSelector)))


def refresh_enctoken(username='', password='', pin=):
    driver = webdriver.Chrome()
    driver.get("https://kite.zerodha.com/")
    try:
        # passwordField = getCssElement( driver , "input[placeholder=Password]" )
        passwordField = driver.find_element_by_xpath('//*[@id="password"]')
        passwordField.send_keys(password)

        # userNameField = getCssElement( driver , "input[placeholder=User ID (eg: AB0001)]" )
        userNameField = driver.find_element_by_xpath('//*[@id="userid"]')
        userNameField.send_keys(username)

        loginButton = getCssElement(driver, "button[type=submit]")
        loginButton.click()
        WebDriverWait(driver, 100).until(EC.presence_of_element_located((By.CLASS_NAME, 'twofa-value')))
        pinField = driver.find_element_by_class_name('twofa-value').find_element_by_xpath(".//input[1]")
        pinField.send_keys(str(pin))
        loginButton = getCssElement(driver, "button[type=submit]")
        loginButton.click()
    except Exception as e:
        raise Exception(e)
    time.sleep(3)
    cookies = driver.get_cookie('enctoken')
    driver.quit()
    enctoken = cookies['value']
    f = open("enctoken.txt", "w")
    f.write(enctoken)
    f.close()


def get_historical_data(tokens,time):
    f = open('enctoken.txt', 'r')
    enctoken = f.read()
    f.close()
    token = tokens
    todayDT = dt.datetime.today().replace(minute=dt.datetime.today().minute)
    last5DT = todayDT + dt.timedelta(days=-5)
    start_time = last5DT.strftime('%Y-%m-%d')
    end_time = todayDT.strftime('%Y-%m-%d')
    url_part_a = 'https://kite.zerodha.com/oms/instruments/historical/'
    url_part_b = f'/{time}minute?user_id=oe3207&oi=1&from='
    link = url_part_a + str(token) + url_part_b + start_time + '&to=' + end_time
    # print(link)
    headers_dict = {'authorization': f'enctoken {enctoken}',
                    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
                    'Accept': '*/*'}
    web_data = requests.get(link, headers=headers_dict)
    # print(web_data)
    json_data = web_data.json()
    # print(json_data)
    try:
        ohlc = json_data['data']['candles']
    except:
        json_data = web_data.json()
        ohlc = json_data['data']['candles']    
    # print(ohlc)
    df = pd.DataFrame(ohlc, columns=['Time', 'open', 'high', 'low', 'close', 'volume', 'no'])
    df['Time'] = df['Time'].astype(str).str[:19]
    df['Time'] = pd.to_datetime(df['Time'], format='%Y-%m-%d %H:%M:%S')
    df.set_index('Time', inplace=True)
    del df['no']
    return df
def get_access_token(symbol):
    kite = KiteConnect(api_key='6')
    tk = kite._parse_instruments(requests.get("https://api.kite.trade/instruments").text)

    for item in tk:
        if item['tradingsymbol'] == symbol and item['exchange'] == 'CDS':
            return item['instrument_token']

def RSI_MAKE():
    symbol = "NIFTY 50"
    token = get_access_token(symbol)
    df = get_historical_data(token,3)
    df['rsi'] = rsi(close=df['close'], window=14, fillna=False)
    # print(df.tail(2)
    RSI_val = df['rsi'][-1]
    return RSI_val

def RSI_HIGH():
    symbol = "NIFTY 50"
    token = get_access_token(symbol)
    try:
        df = get_historical_data(token,3)
    except:
        refresh_enctoken()
        df = get_historical_data(token,3)
    df['rsi'] = rsi(close=df['close'], window=14, fillna=False)
    # print(df.tail(2))
    RSI_val = df['rsi'][-1]
    HIGH = df['high'][-1]
    return RSI_val,HIGH
def RSI_LOW():
    symbol = "NIFTY 50"
    token = get_access_token(symbol)
    try:
        df = get_historical_data(token,3)
    except:
        refresh_enctoken()
        df = get_historical_data(token,3)
    df['rsi'] = rsi(close=df['close'], window=14, fillna=False)
    # print(df.tail(2))
    RSI_val = df['rsi'][-1]
    LOW = df['low'][-1]
    return RSI_val,LOW


def calc_low(kite,name,sl_time):
    token = kite.ltp('NFO:' + name)['NFO:' + name]['instrument_token']
    while True:
        if dt.datetime.now() == sl_time:
            df = get_historical_data(token,5)
            low_val = df['low'][-2]
            break
        else:
            time.sleep(60)

    return low_val

    
    

# def data_downloader(kite,token,name, interval, delta):
# 	to_date = dt.datetime.now().date()
# 	from_date = to_date - timedelta(days = delta)
# 	data = kite.historical_data(instrument_token = token, from_date = from_date, to_date = to_date, interval = interval)
# 	df = pd.DataFrame(data)
# 	# df['time'] = pd.to_datetime(df['date']).dt.time
# 	# df['day'] = pd.to_datetime(df['date']).dt.day
# 	#df =df.set_index('date')
# 	return df
