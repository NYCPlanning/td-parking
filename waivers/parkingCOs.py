# -*- coding: utf-8 -*-
"""
Accessory Off-Street Parking for Residences: 
Certificate of Occupany (CO) Parking Rates 
New Buildings Completed Between 2010 and 2020

Given a Building Information Number (BIN), this script finds and downloads 
that property's most recent CO from DOB Building Information Search (BIS)
portal. It then reads the number of parking spaces built to approximate 
actual (rather than required or effective) parking rates across the city.   

Last Modified: July 2022
"""
import pandas as pd 
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import re 
import subprocess
import os 
from pdfminer.high_level import extract_text

path = 'C:/Users/M_Free/Desktop/td-parking/waivers/'
# path = '/Users/Work/Desktop/GitHub/td-parking/waivers/'

#%% Download CO PDFs

binum_df = pd.read_csv(path + 'output/for_co_test.csv', dtype = str)
        
def get_co_filenames(binum):  
    """ 
    This function takes a BIN to create a string query that accesses the
    CO PDF listing for that property and returns a list of filenames.
    
    Note: BIS uses load balancer that shows a wait screen when traffic is
    high and prevents data from being extracted with the requests module.
    Selenium, however, can wait until the CO PDF listing page loads. 
    """    
    s = Service(path + 'input/chromedriver')
    browser = webdriver.Chrome(service = s)
    url = (f'https://a810-bisweb.nyc.gov/bisweb/COsByLocationServlet?'
            f'requestid=1&allbin={binum}')
    browser.get(url) 
    
    try: 
        WebDriverWait(browser, 15).until(
            EC.title_is('C of O PDF Listing for Property'))
    finally:                                               
        soup = BeautifulSoup(browser.page_source, 'html.parser')
        browser.close()
    
    filenames = []
    file_pattern = re.compile(r".*((\.pdf)|(\.PDF))$")
    for link in soup.find_all('a'):
        if file_pattern.match(link.text):
            filenames.append(link.text[:-4])
    
    return filenames

def get_best_co_filename(filenames):
    """ 
    This function takes a list of filenames and returns the name of the 
    final CO (JobNumber.PDF, JobNumberF.PDF) or if not available, 
    the most recent temporary CO (JobNumberDelimiterItemNumber.PDF) 
    with the highest item number. 
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
    
def get_co_url(filename):
    """ 
    This function takes the best CO filename and returns a string query to
    access a PDF of the file. 
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

    # url = f'https://a810-bisweb.nyc.gov/bisweb/CofoDocumentContentServlet?cofomatadata1=cofo&cofomatadata2={boro}&cofomatadata3={jobnum1}&cofomatadata4={jobnum2}&cofomatadata5={jobnum3}.PDF'
    url = (f'https://a810-bisweb.nyc.gov/bisweb/CofoDocumentContentServlet?'
            f'cofomatadata1=cofo&cofomatadata2={boro}&cofomatadata3={jobnum1}'
            f'&cofomatadata4={jobnum2}&cofomatadata5={jobnum3}.PDF')

    return url

# def download_co_pdf(url, binum):
#     """ 
#     This function takes a BIN and a string query to access a PDF of that
#     property's CO and downloads the file to a folder. 
    
#     Note: Python modules like requests or urllib couldn't read the online 
#     PDFs. Either a text extraction not allowed error would appear or the
#     code would "run" and never execute. As a workaround, this function runs 
#     a js file that reads the PDFs. 
#     """ 
#     node = '/usr/local/bin/node'
#     js = path + 'input/pdf-reader/index.js'
#     output = path + 'output/pdfs' 
#     subprocess.Popen([node, js, url, binum, output]).wait()

test_df = pd.DataFrame(columns = ['bin', 'filename', 'url'])

for binum in binum_df['bin']:
    filenames = get_co_filenames(binum)
    filename = get_best_co_filename(filenames)
    url = get_co_url(filename[0])
    # download_co_pdf(url, binum)

    test_df = test_df.append({'bin': binum,
                              'filename': filename[0],
                              'url': url},
                             ignore_index = True)
    
#%% Extract Parking Spaces from PDFs
#%% Extract Parking Spaces From PDFs

def get_potential_parking(text): 
    """ 
    This function takes text extracted from a CO PDF, searches for strings
    that indicate there may be parking present and returns the number of 
    COs that may have parking.
    """ 
    parking_li = ['parking', 'garage', 'car', 'vehicle'] 
    
    if any(x in text.lower() for x in parking_li):
        parking = 1
    else: 
        parking = 0
    return parking

count = 0

for pdf in os.listdir(path + 'output/pdfs_test/'):
    text = extract_text(path + 'output/pdfs_test/' + pdf)
    count += get_potential_parking(text)

print(count)
    
def get_parking_spaces(text):
    """ 
    This function takes text extracted from a CO PDF, searches for patterns
    that indicate there's parking present and returns the number of spaces.
    """ 
    pattern1 = re.compile(r"Type and number of open spaces:\nParking spaces \((\d+)\)").search(text)
    pattern2 = re.compile(r"/\((\d+)\)\s*(?i)accessory parking spaces").search(text)
        
    if pattern1: 
        spaces = pattern1.group(1)
    elif pattern2:
        spaces = pattern2.group(1) # need to make sure its the first occurence
        spaces = 'pattern not found'
    return spaces

spaces_df = pd.DataFrame(columns = ['bin', 'spaces'])

for pdf in os.listdir(path + 'output/pdfs_test/'):
    text = extract_text(path + 'output/pdfs_test/' + pdf)
    spaces_df = spaces_df.append({'filename': pdf.split('.', 1)[0],
                                 'spaces': get_parking_spaces(text)},
                                 ignore_index = True)
       

# no co 