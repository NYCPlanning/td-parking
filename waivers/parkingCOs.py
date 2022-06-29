# -*- coding: utf-8 -*-
"""
Certificate of Occupancy Reader:
Given a BIN, return the number of residential parking spaces on the most recent CO.   

https://github.com/ResidentMario/nyc-active-construction-sites/blob/master/src/co_reader.py
https://regex101.com/
"""
import pandas as pd 
from selenium import webdriver
import time
from bs4 import BeautifulSoup
import re 

# path = 'C:/Users/M_Free/Desktop/td-parking/waivers/'
path = '/Users/Work/Desktop/GitHub/td-parking/waivers/'

bin_num_df = pd.read_csv(path + 'output/for_co_test.csv', dtype = str)

url = 'https://a810-bisweb.nyc.gov/bisweb/COsByLocationServlet?requestid=1&allbin='
 
driver = webdriver.Chrome(executable_path = '/Users/Work/Desktop/GitHub/td-parking/waivers/input/chromedriver')
driver.get(url + '1087549')

time.sleep(7)

soup = BeautifulSoup(driver.page_source, 'html5lib')

atag_li = []

filepattern = re.compile(r".*((\.pdf)|(\.PDF))$")

for link in soup.find_all('a'):
    if filepattern.match(link.text):
        atag_li.append(link.text[:-4])
        

driver.close()

def best_co(atag):
    
    filestoreturn = []
    jobitem_di = {}
    
    for link in atag:
        splitby = ''
        if re.compile(r"[A-z]").match(link[0]):
            continue
        elif re.compile(r".+(f|F)$").match(link):
            filestoreturn.append(link)
            print('append')
            continue
        elif 'TCO' in link:
            splitby = 'TCO'
            print('hi - tco')
        elif 'T' in link:
            splitby = 'T'
        elif '-' in link:
            splitby = '-'
        else:
            filestoreturn.append(link)
            print('end')
            continue
    
        jobnum, itemnum = link.split(splitby)
    
        if jobnum in jobitem_di:
            if int(itemnum) > int(jobitem_di.get(jobnum)):
                jobitem_di[jobnum] = itemnum 
        else: 
            jobitem_di[jobnum] = itemnum 
    
    for key in jobitem_di.keys():
        if (key in filestoreturn) | (key + 'F' in filestoreturn):
            print('already have final')
        else:
            filestoreturn.append(key + '-' + jobitem_di[key])
    
    return filestoreturn

x = best_co(atag_li)        
        
            
print(best_co(atag_li))          
        
