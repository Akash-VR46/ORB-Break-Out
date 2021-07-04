import datetime as dt
from datetime import datetime, timedelta as tt
import os
from socket import socket
import threading 
import pandas as pd
from requests_oauthlib import OAuth2Session
import numpy as np
import time
import requests
import json
from selenium import webdriver
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
#from selenium_help import getCssElement
from nsepy import get_expiry_date
from openpyxl import load_workbook
from threading import Thread
from alice_blue import *
import re
import logging
from queue import Queue

DEBUG = False

LOG_FILE = f'logs/{int(time.time())}.log'

logging.basicConfig(
    format='%(asctime)s:%(threadName)s:(%(levelname)s): %(message)s',
    datefmt='%d-%b-%y %H:%M:%S',
    level=logging.DEBUG if DEBUG else logging.INFO,
    handlers=[logging.FileHandler(LOG_FILE, 'a'), logging.StreamHandler()]
)

ticks_list = []
TRADER_START_TIME = dt.time(hour=9, minute=30)
TRADER_STOP_TIME = dt.time(hour=16, minute=40)
ltp_max = 0
ltp_min = 0
flag_P = 0
fg =0
flag_C = 0
direction = 0
socket_opened = False
price_q = Queue()
price_q1 = Queue()

def login():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    driver = webdriver.Chrome(executable_path='chromedriver.exe', options=options)

    # defining non trading constants
    web_url = 'https://ant.aliceblueonline.com'
    redirect_uri = 'http://127.0.0.1/'
    authorization_base_url = f'{web_url}/oauth2/auth'
    token_url = f'{web_url}/oauth2/token'
    scope = ['orders']
    credentials = pd.read_excel('credentials.xlsx')
    username = credentials['Username'][0]  # get from excel
    password = credentials['Password'][0]  # get from excel
    client_Id = credentials['Client_ID'][0]
    api_id = credentials['Api_id'][0]
    api_secret = credentials['Api_secret'][0]
    answer1 = credentials['Answer1'][0]
    answer2 = credentials['Answer2'][0]

    # ************Configuring alice blue****************
    oauth = OAuth2Session(api_id, redirect_uri=redirect_uri, scope=scope)
    authorization_url, _state = oauth.authorization_url(authorization_base_url, access_type="authorization_code")

    driver.get(authorization_url)
    waitingEle = WebDriverWait(driver, 100).until(EC.presence_of_element_located((By.NAME, 'client_id')))
    clientId = driver.find_element_by_name('client_id')
    clientId.send_keys(str(client_Id))
    p = driver.find_element_by_name('password')
    p.send_keys(password)
    button = driver.find_element_by_class_name('container').find_element_by_xpath(".//div[1]/button")
    button.click()

    waitingEle = WebDriverWait(driver, 100).until(EC.presence_of_element_located((By.NAME, 'answer1')))
    a1 = driver.find_element_by_name('answer1')
    a1.send_keys(answer1)
    a2 = driver.find_element_by_name('answer2')
    a2.send_keys(answer2)
    button = driver.find_element_by_class_name('container').find_element_by_xpath(".//div[1]/button")
    button.click()
    wait = WebDriverWait(driver, 100)
    wait.until(lambda driver: driver.current_url.startswith != "http://127.0.0.1")

    newUrl = driver.current_url
    print(newUrl)
    # driver.close()
    authUrl = 'https' + newUrl[4:]
    print()
    # print(clientId.get_attribute("style"))
    print(token_url)
    oauth = OAuth2Session(api_id, redirect_uri=redirect_uri, scope=scope)
    token = oauth.fetch_token(token_url, authorization_response=authUrl, client_secret=api_secret)

    access_token_a3 = token['access_token']
    alice = {'username': username, 'password': password, 'access_token': access_token_a3,
             'master_contracts_to_download': ['NFO']}
    driver.quit()

    print("*****master contract fetched******")
    return alice

def get_month1(alice):
    instru = alice.search_instruments('NFO', 'NIFTY')

    k = []
    for i in instru:
        k.append(i.expiry)
    k = list(set(k))
    for e, i in enumerate(k):
        if i is None:
            k.remove(None)
    k.sort()
    if k[0] <= k[1]:
        expiry_month = k[0].month
    else:
        expiry_month = k[1].month

    expiry_date_month = ((dt.datetime.strptime(str(expiry_month), "%m")).strftime("%b"))

    return expiry_date_month.upper()

def get_high_low(alice):
    global price_q
    global socket_opened
    month = get_month1(alice)
    symbol = 'NIFTY ' + str(month) + ' FUT'
    alice_instrument_ob = alice.get_instrument_by_symbol('NFO', symbol)
    alice.subscribe(alice_instrument_ob, LiveFeedType.FULL_SNAPQUOTE)

    # ob = ticks(alice,alice_instrument_ob,fl=0)
    # ob.start()
    while True:
        try:
            tck = price_q.get()
        except:
            tck =price_q.get()

        high = tck[0]['high']
        low = tck[0]['low']
        break

        # alice.start_websocket()
        # socket_opened = False
        # print()
    # ob.join()
    return high,low

# class ticks(threading.Thread):
#     def __init__(self,alice,alice_instrument_obj,fl = 0):
#         super(ticks,self).__init__()
#         # self.t = t
#         self.alice_instrument_obj = alice_instrument_obj
#         self.fl = fl
#         self.alice = alice
    
#     def run(self):
#         TRADER_START_TIME = dt.time(hour=9, minute=30)
        
#         # while socket_opened == False:
#         #     pass

            
#         if self.fl == 0:
#             while True:
#             # print(self.alice_instrument_obj)
#                 alice.subscribe(self.alice_instrument_obj, LiveFeedType.FULL_SNAPQUOTE)
#         if self.fl == 1:
#             while True:
#             # alice.start_websocket(subscribe_callback=self.event_handler_quote_update,
#                         #    socket_open_callback=self.open_callback,
#                         #    run_in_background=True)
#                 alice.subscribe(self.alice_instrument_obj, LiveFeedType.COMPACT)

def place_sell_order(inst,quantity):
    t=alice.place_order(transaction_type = TransactionType.Sell,
                            instrument = inst,
                            quantity = quantity,
                            order_type = OrderType.Market,
                            product_type = ProductType.Intraday)
    return t['data']['oms_order_id']
def place_buy_order(inst,quantity):
    t=alice.place_order(transaction_type = TransactionType.Buy,
                            instrument = inst,
                            quantity = quantity,
                            order_type = OrderType.Market,
                            product_type = ProductType.Intraday)
    return t['data']['oms_order_id']

def event_handler_quote_update(message):
    global price_q
    price_q.put([message])
        # print(ticks_list)


def open_callback():
        global socket_opened
        print('socket is opened ')
        socket_opened = True

def event_handler_quote_update1(message):
    global price_q1
    price_q1.put([message])
        # print(ticks_list)


def open_callback1():
        global socket_opened
        print('socket is opened ')
        socket_opened = True


class PE(threading.Thread):
    def __init__(self, params) :
        super(PE, self).__init__()
        self.params = params
        # self.alice1 = alice1

    def sqoff(self):
        inst_list = []
        global price_q
        flag_hp =0
        global fg
        token_list= []
        pe1 = (alice1.get_instrument_by_symbol('NFO',self.params['pe1_strike_price']))
        token_list.append(pe1[1])
        inst_list.append(pe1)
        pe2 = (alice1.get_instrument_by_symbol('NFO',self.params['pe2_strike_price']))
        token_list.append(pe2[1])
        inst_list.append(pe2)
        alice1.subscribe(inst_list,LiveFeedType.COMPACT)
        time.sleep(5)
        # obj1 = ticks(inst_list,fl=1)
        # obj1.start()
        print(token_list)
        while True:
            pe1_sell_ltp = 0
            pe2_buy_ltp = 0

            # print(len(tcks))
            # print(tcks)
            while True:
                tcks = price_q1.get()
                for single in tcks:
                    print(single)
                    # token_list[0]
                    # single['token']
                    if single['token'] == token_list[0]:
                        pe1_sell_ltp = single['ltp']
                    if single['token'] == token_list[1]:
                        pe2_buy_ltp = single['ltp']
                if pe1_sell_ltp > 0 and pe2_buy_ltp > 0:
                    break
            
            ltp_diff = pe1_sell_ltp - pe2_buy_ltp
            print("reached here")
            if ltp_diff <= self.params['Target1_p'] and flag_hp == 0:
                logging.info("target hitted")
                self.params['lot'] = self.params['lot']/2
                order_i1 = place_buy_order(pe1,self.params['lot']) 
                logging.info(f"placed buy order for squareoff with lot {self.params['lot']} at {ltp_diff}")
                order_i2 = place_sell_order(pe2,self.params['lot']) 
                logging.info(f"placed sell order for squareoff with lot {self.params['lot']} at {ltp_diff}")
                prev_ltp =ltp_diff
                trail_sl = ltp_diff + 4
                flag_hp = 1
            elif ltp_diff >= self.params['sl1_p'] and flag_hp == 0:
                logging.info("sl hitted")
                order_i1 = place_buy_order(pe1,self.params['lot']) 
                logging.info(f"placed buy order for squareoff with lot {self.params['lot']} at {ltp_diff}")
                order_i2 = place_sell_order(pe2,self.params['lot']) 
                logging.info(f"placed sell order for squareoff with lot {self.params['lot']} at {ltp_diff}")
                break
            if flag_hp == 1:
                if ltp_diff >= trail_sl:
                    order_i1 = place_buy_order(pe1,self.params['lot'])
                    logging.info(f"placed buy order for squareoff with lot {self.params['lot']} at {ltp_diff}")
                    order_i2 = place_sell_order(pe2,self.params['lot'])
                    logging.info(f"placed sell order for squareoff with lot {self.params['lot']} at {ltp_diff}")
                    # fg =1
                    break 
                else:
                    trail = prev_ltp - ltp_diff
                    if trail > 0:
                        trail_sl -= trail
                        prev_ltp = ltp_diff

            if dt.datetime.today() == dt.datetime.combine(dt.datetime.today(),TRADER_END_TIME):
                order_i1 = place_buy_order(pe1,self.params['lot']) 
                logging.info(f"placed buy order for squareoff with lot {self.params['lot']} at {ltp_diff}")
                order_i2 = place_sell_order(pe2,self.params['lot']) 
                logging.info(f"placed sell order for squareoff with lot {self.params['lot']} at {ltp_diff}")
                break
    # obj1.join()
                

    def run(self):
        self.sqoff()

class CE(threading.Thread):
    def __init__(self, params ) :
        super(CE, self).__init__()
        self.params = params
        # self.alice1 = alice1

    def sqoff(self):
        inst_list = []
        global price_q
        flag_hc =0
        token_list= []
        ce1 = (alice.get_instrument_by_symbol('NFO',self.params['ce1_strike_price']))
        token_list.append(ce1[1])
        inst_list.append(ce1)
        ce2 = (alice.get_instrument_by_symbol('NFO',self.params['ce2_strike_price']))
        token_list.append(ce2[1])
        inst_list.append(ce2)
        alice.subscribe(inst_list,LiveFeedType.COMPACT)
        time.sleep(3)
        # obj1 = ticks(inst_list)
        # obj1.start()
        while True:
            ce1_sell_ltp =0
            ce2_buy_ltp =0
            while True:
                tcks = price_q.get()
                for single in tcks:
                    if single['token'] == token_list[0]:
                        ce1_sell_ltp = single['ltp']
                    if single['token'] == token_list[1]:
                        ce2_buy_ltp = single['ltp']
                if ce2_buy_ltp >0 and ce1_sell_ltp > 0:
                    break
            ltp_diff = ce1_sell_ltp - ce2_buy_ltp
            if ltp_diff <= self.params['Target1_c'] and flag_hc == 0:
                logging.info("Target Reached ")
                self.params['lot'] = int(self.params['lot'])/2
                order_i1 = place_buy_order(ce1,self.params['lot']) 
                logging.info(f"placed buy order for squareoff with lot {self.params['lot']}")
                order_i2 = place_sell_order(ce1,self.params['lot']) 
                logging.info(f"placed sell order for squareoff with lot {self.params['lot']}")
                prev_ltp =ltp_diff
                trail_sl = ltp_diff + 4
                flag_hp = 1
            elif ltp_diff >= self.params['sl1_c'] and flag_hc == 0:
                logging.info(f"SL hit")
                order_i1 = place_buy_order(ce1,self.params['lot']) 
                logging.info(f"placed sell order for squareoff with lot {self.params['lot']} at {ltp_diff}")
                order_i2 = place_sell_order(ce1,self.params['lot']) 
                logging.info(f"placed buy order for squareoff with lot {self.params['lot']} at {ltp_diff}")
                break
            if flag_hc == 1:
                if ltp_diff >= trail_sl:
                    order_i1 = place_buy_order(ce1,self.params['lot']) 
                    logging.info(f"placed buy order for squareoff with lot {self.params['lot']} at {ltp_diff}")
                    order_i2 = place_sell_order(ce2,self.params['lot']) 
                    logging.info(f"placed sell order for squareoff with lot {self.params['lot']} at {ltp_diff}")
                    break
                else:
                    trail = prev_ltp - ltp_diff
                    if trail > 0:
                        trail_sl -= trail
                        prev_ltp=ltp_diff

            if dt.datetime.today() == dt.datetime.combine(dt.datetime.today(),TRADER_END_TIME):
                order_i1 = place_buy_order(ce1,self.params['lot']) 
                logging.info(f"placed buy order for squareoff with lot {self.params['lot']} at {TRADER_END_TIME}")
                order_i2 = place_sell_order(ce2,self.params['lot']) 
                logging.info(f"placed sell order for squareoff with lot {self.params['lot']} at {TRADER_END_TIME}")
                break
        # obj1.join()

                

    def run(self):
        self.sqoff()



def high_break():
    # global flag_P
    print("Inside high")
    pe1_strike_price = 'NIFTY ' +sym_month+" "+ str(int(round(ltp1, -2)) - 100.0) + ' PE' 
    inst1 = alice1.get_instrument_by_symbol("NFO",pe1_strike_price)
    pe2_strike_price = 'NIFTY ' +sym_month+" "+ str(int(round(ltp1, -2)) - 200.0) + ' PE' 
    inst2 = alice1.get_instrument_by_symbol("NFO",pe2_strike_price)
    order_id1 = place_sell_order(inst1,lot)
    logging.info(f"placed sell oreder of {pe1_strike_price} ")
    print(order_id1)
    order_id2 = place_buy_order(inst2,lot)
    logging.info(f"placed Buy oreder of {pe2_strike_price} ")
    print(order_id2)
    flag_P = 1
    # if flag_P == 1 and alice.get_order_history(order_id1)['status'] == 'success' and alice.get_order_history(order_id2)['status'] == 'success'  :

    if flag_P == 1  :    
        print("inside param1")
        # time.sleep(0.01)
        pe1_sell_price = alice1.get_order_history(order_id1)['data'][0]['average_price']
        # time.sleep(0.01)
        pe2_buy_price = alice1.get_order_history(order_id2)['data'][0]['average_price']
        # time.sleep(0.01)
        diff1 = pe1_sell_price - pe2_buy_price
        Target1_p = diff1 - 4
        logging.info(f'Tarfget {Target1_p }')
        sl1_p = diff1 + 4
        logging.info(f'sl {sl1_p}')
        params1  = [{'pe1_strike_price' : pe1_strike_price, 'pe1_sell_price': pe1_sell_price, 'pe2_strike_price': pe2_strike_price,
                    'pe2_buy_price' : pe2_buy_price, 'Target1_p' : Target1_p, 'sl1_p' : sl1_p,'lot':lot }]

        print("param1 read successfully ")
        pe_obj = PE(params1[0])
        pe_obj.start()
        pe_obj.join()


def low_break():

    print("inside low")
    ce1_strike_price = 'NIFTY ' +sym_month+" "+ str(int(round(ltp2, -2)) + 100.0) + ' CE' 
    inst1 = alice.get_instrument_by_symbol("NFO",ce1_strike_price)

    ce2_strike_price = 'NIFTY ' +sym_month+" "+ str(int(round(ltp2, -2)) + 200.0) + ' CE' 
    inst2 = alice.get_instrument_by_symbol("NFO",ce2_strike_price)
    order_id1 = place_sell_order(inst1,lot)
    logging.info(f"placed sell oreder of {order_id1} ")
    print(order_id1)
    order_id2 = place_buy_order(inst2,lot)
    logging.info(f"placed Buy oreder of {order_id2} ")
    print(order_id2)
    flag_C = 1

        
    # elif flag_C == 1 and alice.get_order_history(order_id1)['status'] == 'success' and alice.get_order_history(order_id2)['status'] == 'success'  :
    if flag_C == 1  :
        print("inside param2")
        # time.sleep(0.01)
        ce1_sell_price = alice.get_order_history(order_id1)['data'][0]['average_price']
        # time.sleep(0.01)
        ce2_buy_price = alice.get_order_history(order_id2)['data'][0]['average_price']
        # time.sleep(0.01)
        diff1 = ce1_sell_price - ce2_buy_price
        Target1_c = diff1 - 4
        logging.info(f"target {Target1_c }")
        sl1_c = diff1 + 4
        logging.info(f"sl {sl1_c }")
        params2  = [{'ce1_strike_price' : ce1_strike_price, 'ce1_sell_price': ce1_sell_price, 'ce2_strike_price': ce2_strike_price,
                    'ce2_buy_price' : ce2_buy_price, 'Target1_c' : Target1_c, 'sl1_c' : sl1_c, 'lot':lot }]

        print("param2 load successfully class")
        ce_obj = CE(params2[0])
        ce_obj.start()
        ce_obj.join()

def get_month(alice):
    instru = alice.search_instruments('NFO', 'NIFTY')

    k = []
    for i in instru:
        k.append(i.expiry)
    k = list(set(k))
    for e, i in enumerate(k):
        if i is None:
            k.remove(None)
    k.sort()
    print(k)
    if k[0].month == k[1].month:
        expiry_date = k[0]

        expiry_date_month = ((dt.datetime.strptime(str(expiry_date.month), "%m")).strftime("%b"))
        stringDate = str(expiry_date).split('-')
        formatedDate = f"{stringDate[2]} {expiry_date_month.upper()}{stringDate[0][2:]}"
    else:
        if k[0] <= k[1]:
            expiry_month = k[0].month
        else:
            expiry_month = k[1].month

        formatedDate = ((dt.datetime.strptime(str(expiry_month), "%m")).strftime("%b")).upper()
    
    # return expiry_date_month.upper()
    return formatedDate
        
    


if __name__ == '__main__':
    squareoff_hour = 15
    squareoff_minute = 15
    flag_C = 0
    flag_P = 0
    #   change_in_price = params['change_in_price']
    # change_in_sl = params['change_in_sl']

    TRADER_START_TIME = dt.time(hour=9, minute=15)
    TRADER_END_TIME = dt.time(hour=15, minute=14)
    TRADER_STOP_TIME = dt.time(hour=squareoff_hour, minute=squareoff_minute)
    # CHECK_TIME = dt.time(hour=9,minute=15)
    TEST_TIME = dt.time(hour=9,minute=25)
    AFTER_ORB_TIME = dt.time(hour=9,minute=31)

    if not dt.datetime.combine(dt.datetime.today(),
                               TRADER_STOP_TIME) > dt.datetime.today() > dt.datetime.combine(dt.datetime.today(),
                                                                                             TRADER_START_TIME):
        logging.info('sleeping till trade time')
        while not dt.datetime.combine(dt.datetime.today(),
                                      TRADER_STOP_TIME) > dt.datetime.today() > dt.datetime.combine(dt.datetime.today(),
                                                                                                    TRADER_START_TIME):
            time.sleep(1)

    cred = pd.read_excel("credentials.xlsx")
    lot = int(cred['lots'][0])
    lot = lot * 75
    ORB_TIME = dt.time(hour=9,minute=30)
    alice_dict = login()
    fla = 0
    flag = 0
    alice = AliceBlue(username=alice_dict['username'], password=alice_dict['password'],
                                     access_token=alice_dict['access_token'],
                                     master_contracts_to_download=alice_dict['master_contracts_to_download'])
    alice1 = AliceBlue(username=alice_dict['username'], password=alice_dict['password'],
                                     access_token=alice_dict['access_token'],
                                     master_contracts_to_download=alice_dict['master_contracts_to_download'])

    month = get_month1(alice)
    sym_month = get_month(alice)
    # symbol = "CRUDEOIL " + month + ' 5800 ' + 'PE'
    # print(symbol)

    # alice_instrument_obj = alice.get_instrument_by_symbol('MCX', symbol)

    # while True:
    #     if dt.datetime.today == dt.datetime.combine(dt.datetime.today(),ORB_TIME):
    #         break
    alice.start_websocket(subscribe_callback=event_handler_quote_update,
                          socket_open_callback=open_callback,
                          run_in_background=True)

    alice1.start_websocket(subscribe_callback=event_handler_quote_update1,
                            socket_open_callback=open_callback1,
                            run_in_background=True)
    while True:
        if dt.datetime.combine(dt.datetime.today(),TRADER_END_TIME) > dt.datetime.today() >= dt.datetime.combine(dt.datetime.today(),ORB_TIME):
            high ,low = get_high_low(alice)
            print(high,low)
            print(dt.datetime.today())
            break
        else:
            time.sleep(1)
    # time.sleep(60)
    if dt.datetime.today() >= dt.datetime.combine(dt.datetime.today(),ORB_TIME):
        sym = 'NIFTY ' + str(month) + ' FUT'
        alice_instrument_obj = alice.get_instrument_by_symbol('NFO', sym)     
        # print(alice_instrument_obj)
        alice.unsubscribe(alice_instrument_obj,LiveFeedType.FULL_SNAPQUOTE)
        time.sleep(5)
        alice.subscribe(alice_instrument_obj,LiveFeedType.COMPACT)
        alice1.subscribe(alice_instrument_obj,LiveFeedType.COMPACT)
        time.sleep(2)
        # obj = ticks(alice,alice_instrument_obj,fl=1)
        # obj.start()
        while True:
            pticks = price_q1.get()
            cticks = price_q.get()
            # print(cticks)
            print(cticks[0]['ltp'])
            # print(cticks['ltp'])
            if pticks[0]['ltp'] > high and fla == 0:
                ltp1 = pticks[0]['ltp']
                #buy condition
                print("HIGH BREAKOUT")
                logging.info(f"High Breakout at {ltp1} ")
                fla = 1
                alice1.unsubscribe(alice_instrument_obj,LiveFeedType.COMPACT)
                high_obj = Thread(target=high_break)
                high_obj.start()
                # alice.unsubscribe(alice_instrument_obj,LiveFeedType.COMPACT)
            if cticks[0]['ltp'] < low and flag == 0:
                ltp2 = cticks[0]['ltp']
                print('LOW BREAKOUT')
                logging.info(f"Low Breakout at {ltp2} ")
                flag = 1
                alice.unsubscribe(alice_instrument_obj,LiveFeedType.COMPACT)
                low_obj = Thread(target=low_break)
                low_obj.start()
            if fla == 1 and flag == 1:
                break
        
        high_obj.join()
        low_obj.join()
            
                

            
    
        
        # obj.join()

        

   

