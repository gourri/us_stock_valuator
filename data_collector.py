# -*- coding: utf-8 -*-
import os
import time
from datetime import datetime
import sys
import re
import json
from selenium import webdriver
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup
import pandas as pd

import url_handler

sleep_time = 2
now = datetime.now()

def read_data_from_itooza_us(stock_code, login_id="", login_passwd=""):
    try:
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        driver = webdriver.Chrome(options=options)
        driver.implicitly_wait(sleep_time)

        
        # Click "login"
        #driver.get("https://login.itooza.com/login.htm")
        driver.get("http://us.itooza.com/stocks/summary/"+stock_code)
        driver.implicitly_wait(sleep_time)
        driver.find_element_by_xpath('//*[@id="header"]/div[1]/div[2]/span[2]/span/a').click()
        driver.implicitly_wait(sleep_time)
        
        # Login form
        driver.find_element_by_xpath('/html/body/div[3]/div[2]/form/div/div[2]/div[1]/div[1]/div[1]/div[1]/input').send_keys(login_id)
        driver.find_element_by_xpath('//*[@id="txtPassword"]').send_keys(login_passwd)
        driver.find_element_by_xpath('//*[@id="login-container-01"]/div[2]/div[1]/div[1]/div[2]/input').click()
        driver.implicitly_wait(sleep_time)
        

        # Get EV
        driver.get("http://us.itooza.com/stocks/summary/"+stock_code)
        driver.implicitly_wait(sleep_time)
        ev = int(driver.find_element_by_xpath('/html/body/div[1]/div[3]/div[3]/div[3]/table[1]/tbody/tr[2]/td').text.replace(',','').replace('백만달러',''))
        print("EV = {}".format(ev))


        # Investment indicators
        driver.get("http://us.itooza.com/stocks/invest/"+stock_code)
        print("Connecting to {}".format("http://us.itooza.com/stocks/invest/"+stock_code))
        driver.implicitly_wait(sleep_time+1)

        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        current_price = float(soup.select('#container > div.schChartTitle > ul:nth-child(3) > li.num')[0].text.replace(',',''))
        print("current_price = {}".format(current_price))

        columns = soup.select('#table_scroll_div > table > thead > tr > th')      # Copy --> Copy selector
        columnlist = []
        for column in columns:
            columnlist.append(''.join(column.text))
        print("columnlist = {}".format(columnlist))

        contents = soup.select('#table_scroll_div > table > tbody > tr')
        dfcontent = []
        alldfcontents = []

        weight_list = []
        for i in range(0, len(columnlist) - len(weight_list)):
            weight_list.append(len(columnlist) - i)

        alldfcontents.append(weight_list)
        for content in contents:
            #dfcontent.append(itooza_indicator_list[n])
            tds = content.find_all("td")
            for td in tds:
                dfcontent.append(td.text.replace('\n','').replace(' ',''))
            if len(dfcontent) > 3:
                alldfcontents.append(dfcontent)
                #print("dfcontent = {}".format(dfcontent))
            dfcontent = []

        #print("len(columns) = {}".format(len(columnlist)))
        #print("len(alldfcontents) = {}".format(len(alldfcontents)))
        for i in range(0, len(alldfcontents)):
            #print("len(alldfcontents[{}]) = {}".format(i, len(alldfcontents[i])))
            if len(alldfcontents[i]) > len(columnlist):
                print("set subset of columns from {} to {}".format(len(alldfcontents[i]), len(columnlist)))
                #print("alldfcontents[{}][0:42]={}".format(i, alldfcontents[i][0:len(columnlist)]))
                alldfcontents[i] = alldfcontents[i][0:len(columnlist)]
        
        for i in range(0, len(alldfcontents)):
            print("len(alldfcontents[{}]) = {}".format(i, len(alldfcontents[i])))

        df_investing = pd.DataFrame(columns=columnlist, data=alldfcontents)

        print(df_investing)

        # df_financial_statement
        driver.get("http://us.itooza.com/stocks/financials/"+stock_code)
        driver.implicitly_wait(sleep_time)
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        columns = soup.select('#ab_class > thead > tr > th')
        columnlist = []
        tmp_columnlist = []
        for column in columns:
            tmp_columnlist.append(''.join(column.text))
        print("len(tmp_columnlist) = {}, tmp_columnlist = {}".format(len(tmp_columnlist), tmp_columnlist))
        chunk_size = int(len(tmp_columnlist)/3)
        columnlist = [tmp_columnlist[i * chunk_size:(i + 1) * chunk_size] for i in range((len(tmp_columnlist) + chunk_size - 1) // chunk_size )]
        print("len(columnlist) = {}, columnlist = {}".format(len(columnlist), columnlist))

        dfcontent = []
        alldfcontents = []
        contents = soup.select('#ab_class > tbody > tr')
        for tr in contents:
            tds = tr.find_all("td")
            for td in tds:
                dfcontent.append(td.text.replace('\n','').replace(' ',''))
            print("len(dfcontent) = {}, dfcontent = {}".format(len(dfcontent), dfcontent))
            if len(dfcontent) > 3:
                alldfcontents.append(dfcontent)
            dfcontent = []
        df_financial = pd.DataFrame(columns=columnlist[0], data=alldfcontents)

        try:
            os.makedirs("./itooza/us/"+now.strftime("%Y%m%d")+"/")    
            print("Directory ", "./itooza/us/"+now.strftime("%Y%m%d")+"/",  " Created ")
        except FileExistsError:
            print("Directory ", "./itooza/us/"+now.strftime("%Y%m%d")+"/",  " Already exists")
        df_investing.to_csv("./itooza/us/"+now.strftime("%Y%m%d")+"/"+stock_code+"_investing.csv", mode="w")
        df_financial.to_csv("./itooza/us/"+now.strftime("%Y%m%d")+"/"+stock_code+"_financial.csv", mode="w")

        driver.close()
        driver.quit()

        return df_investing, df_financial, current_price, ev

    except Exception as e:
        print ('EXCEPTION: {}'.format(e))
        #return pd.DataFrame(), pd.DataFrame(), float(0), 0
        driver.close()
        driver.quit()
        raise e


def read_data_from_files_us(stock_code, date_str):
    try:
        investing_name = "./itooza/us/"+date_str+"/"+stock_code+"_investing.csv"
        financial_name = "./itooza/us/"+date_str+"/"+stock_code+"_financial.csv"
        df_investing = pd.read_csv(investing_name)
        df_financial = pd.read_csv(financial_name)

        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        driver = webdriver.Chrome(options=options)
        driver.implicitly_wait(sleep_time)

        # Get EV
        driver.get("http://us.itooza.com/stocks/summary/"+stock_code)
        driver.implicitly_wait(sleep_time)
        ev = int(driver.find_element_by_xpath('/html/body/div[1]/div[3]/div[3]/div[3]/table[1]/tbody/tr[2]/td').text.replace(',','').replace('백만달러',''))
        print("EV = {}".format(ev))

        # Investment indicators
        driver.get("http://us.itooza.com/stocks/invest/"+stock_code)
        print("Connecting to {}".format("http://us.itooza.com/stocks/invest/"+stock_code))
        driver.implicitly_wait(sleep_time+1)

        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        current_price = float(soup.select('#container > div.schChartTitle > ul:nth-child(3) > li.num')[0].text.replace(',',''))
        print("current_price = {}".format(current_price))

        df_investing.drop(df_investing.columns[[0]], axis=1, inplace=True)
        df_financial.drop(df_financial.columns[[0]], axis=1, inplace=True)        

        return df_investing, df_financial, current_price, ev

    except Exception as e:
        print ('EXCEPTION: {}'.format(e))
        raise e


if __name__ == "__main__":
    stock_code = "VMW"
    df_investing, df_financial, current_price, ev = read_data_from_itooza_us(stock_code)
    print (df_investing)
    print (df_financial)
    print ("current_price = {}".format(current_price))
    print ("ev = {}".format(ev))