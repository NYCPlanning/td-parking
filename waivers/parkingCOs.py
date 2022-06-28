# -*- coding: utf-8 -*-
"""
Certificate of Occupancy Reader:
Given a BIN, return the number of residential parking spaces on the most recent CO.   

https://github.com/ResidentMario/nyc-active-construction-sites/blob/master/src/co_reader.py
"""
import pandas as pd 
import requests
from bs4 import beautifulsoup

path = 'C:/Users/M_Free/Desktop/td-parking/waivers/'
bin_num_df = pd.read_csv(path + 'output/for_co.csv', dtype = str)

url = 'https://a810-bisweb.nyc.gov/bisweb/COsByLocationServlet?requestid=1&allbin='

for bin_num in bin_num_df['bin']:
    r = requests.get(url + bin_num)