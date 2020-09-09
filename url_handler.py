import time
import datetime
import sys
import re
import json

def get_urls_from_stock_list_KR(stock_code):
    # stock_code should be string
    return "http://search.itooza.com/index.htm?seName="+stock_code

def get_urls_from_stock_list_US(stock_code):
    # stock_code should be string
    return "http://usdev.itooza.com/stocks/invest/"+stock_code