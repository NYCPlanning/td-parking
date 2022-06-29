# -*- coding: utf-8 -*-
"""
Certificate of Occupancy Reader:
Given a BIN, return the number of residential parking spaces on the most recent CO.   
"""
import pandas as pd 
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import time
from bs4 import BeautifulSoup
import re 

path = 'C:/Users/M_Free/Desktop/td-parking/waivers/'
# path = '/Users/Work/Desktop/GitHub/td-parking/waivers/'
url = 'https://a810-bisweb.nyc.gov/bisweb/COsByLocationServlet?requestid=1&allbin='
bin_num_df = pd.read_csv(path + 'output/for_co_test.csv', dtype = str)

#%% Download CO PDF

s = Service(path + 'input/chromedriver')
browser = webdriver.Chrome(service = s)
# browser.get(url + '1087549')
# browser.get(url + '1087877')
browser.get(url + '1087368')
time.sleep(7)
soup = BeautifulSoup(browser.page_source, 'html5lib')
browser.close()

# create list of pdf file names
filename_li = []
filepattern = re.compile(r".*((\.pdf)|(\.PDF))$")
for link in soup.find_all('a'):
    if filepattern.match(link.text):
        filename_li.append(link.text[:-4])

def get_best_co(filenames):
    """ 
    takes list of co file names
    returns the final co or if not available, the latest temp co
    """
    filestoreturn = []
    jobitem_di = {}
    
    for link in filenames:
        splitby = ''
        if re.compile(r"[A-z]").match(link[0]): 
            continue
        elif re.compile(r".+(f|F)$").match(link): 
            filestoreturn.append(link)
            continue
        elif 'TCO' in link:
            splitby = 'TCO'
        elif '-T-' in link:
            splitby = '-T-'
        elif 'T' in link:
            splitby = 'T'
        elif '-' in link:
            splitby = '-'
        else:
            filestoreturn.append(link)
            continue
        
        # split temp co filenames by job number and item number
        jobnum, itemnum = link.split(splitby)
        
        # determine which temp co has the highest item number
        if jobnum in jobitem_di:
            if int(itemnum) > int(jobitem_di.get(jobnum)):
                jobitem_di[jobnum] = itemnum 
        else: 
            jobitem_di[jobnum] = itemnum 
    
    for key in jobitem_di.keys():
        if (key in filestoreturn) | (key + 'F' in filestoreturn):
            continue
        else:
            filestoreturn.append(key + '-' + jobitem_di[key])
    
    return filestoreturn
      
print(get_best_co(filename_li))       

def get_co_pdf(filename):
    """ 
    takes co file name
    returns url with a pdf of the file
    """
    boro_di = {'1': 'M',
               '2': 'X',
               '3': 'B',
               '4': 'Q',
               '5': 'R'}
    
    boro = boro_di[filename[0]]
    jobnum1 = filename[:3]
    jobnum2 = filename[3:6] + '000'
    jobnum3 = filename 

    url = f'https://a810-bisweb.nyc.gov/bisweb/CofoDocumentContentServlet?cofomatadata1=cofo&cofomatadata2={boro}&cofomatadata3={jobnum1}&cofomatadata4={jobnum2}&cofomatadata5={jobnum3}.PDF'

    return url

print(get_co_pdf('103174084'))

# high demand 
# no co 

