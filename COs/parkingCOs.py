# -*- coding: utf-8 -*-
"""
Accessory Off-Street Parking for Residences: 
Certificate of Occupany (CO) Parking Rates 
New Buildings Completed Between 2010 and 2020

Given a Building Information Number (BIN), this script finds and downloads 
that property's most recent CO from DOB Building Information Search (BIS)
portal. It then reads the number of parking spaces built to approximate 
actual (rather than required or effective) parking rates across the city.   

Last Modified: August 2022
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
from text_to_num import alpha2digit
from tqdm import tqdm

path = '/Users/m_free/Desktop/GitHub/td-parking/COs/'
waiver_path = '/Users/m_free/Desktop/GitHub/td-parking/waivers/output/for_co_waivers.csv'
drive_path = '/Users/m_free/OneDrive - NYC O365 HOSTED/Projects/Parking/ParkingRates/COs/'

#%% Create Helper Functions
        
def get_co_filenames(binum):  
    """ 
    This function takes a BIN to create a string query that accesses the
    CO PDF listing for that property and returns a list of filenames.
    
    Note: BIS uses load balancer that shows a wait screen when traffic is
    high and prevents data from being extracted with the requests module.
    Selenium, however, can wait until the CO PDF listing page loads. 
    """    
    s = Service(path + 'input/chromedriver.exe')
    browser = webdriver.Chrome(service = s)
    url = (f'https://a810-bisweb.nyc.gov/bisweb/COsByLocationServlet?'
            f'requestid=1&allbin={binum}')
    browser.get(url) 
    
    try: 
        WebDriverWait(browser, 30).until(
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

def get_best_co_filenames(filenames):
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
        elif 'TOO' in link:
            splitby = 'TOO'
        elif '-T-' in link:
            splitby = '-T-'
        elif 'TT' in link:
            splitby = 'TT'
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

def get_best_co_filename_url(best_filenames, jobnum):
    """ 
    Description... match job number, no co 
    """
    filename = 'no co'
   
    for name in best_filenames:
        if name.startswith(jobnum):
            filename = name
            break
        else:
            filename = 'diff job num'
    
    return filename

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

    url = (f'https://a810-bisweb.nyc.gov/bisweb/CofoDocumentContentServlet?'
            f'cofomatadata1=cofo&cofomatadata2={boro}&cofomatadata3={jobnum1}'
            f'&cofomatadata4={jobnum2}&cofomatadata5={jobnum3}.PDF')

    return url

def download_co_pdf(url, binum):
    """ 
    This function takes a BIN and a string query to access a PDF of that
    property's CO and downloads the file to a folder. 
   
    Note: Python modules like requests or urllib couldn't read the online 
    PDFs. Either a text extraction not allowed error would appear or the
    code would "run" and never execute. As a workaround, this function runs 
    a js file that reads the PDFs. 
    """ 
    node = '/usr/local/bin/node'
    js = path + 'input/pdf-reader/index.js'
    output = drive_path + 'pdfs_waivers/' 
    
    try:
        subprocess.Popen([node, js, url, binum, output]).wait(timeout = 30)
    except subprocess.TimeoutExpired:
        print('bin not downloaded: ' + binum)
    
#%% Download CO PDFs 

binum_df = pd.read_csv(waiver_path, dtype = str)
# binum_df = binum_df[6136:] 

# urls_df = pd.DataFrame(columns = ['bin', 'filename', 'url'])
urls_df = pd.read_csv(path + 'output/urls.csv')

for index, row in tqdm(binum_df.iterrows(), total = len(binum_df)): 
    
    filenames = get_co_filenames(row['bin'])
    best_filenames = get_best_co_filenames(filenames)
    best_filename = get_best_co_filename_url(best_filenames, row['jobnum'])
    
    if (best_filename == 'no co') | (best_filename == 'diff job num'):
        url = ''
    else:
        url = get_co_url(best_filename)
        download_co_pdf(url, row['bin'] )

    urls_df = pd.concat([urls_df, 
                         pd.DataFrame.from_records([{'bin': row['bin'],
                                                     'filename': best_filename,
                                                     'url': url}])],
                        ignore_index = True)

urls_df.to_csv(path + 'output/urls.csv', index = False)

#%%

pdfs_path = drive_path + 'pdfs_waivers/' 
retry_li = []
binum_df = pd.read_csv(waiver_path, dtype = str)
retry_urls = pd.DataFrame(columns = ['bin', 'filename', 'url'])

for pdf in os.listdir(pdfs_path):
    file = pdfs_path + pdf
    size = os.path.getsize(file)
    pdf = pdf.split('.', 1)[0]
    
    if size < 5000:
        retry_li.append(pdf)
        os.remove(file)

retry_df = binum_df[binum_df['bin'].isin(retry_li)]    

for index, row in tqdm(retry_df.iterrows(), total = len(retry_df)): 
    
    filenames = get_co_filenames(row['bin'])
    best_filenames = get_best_co_filenames(filenames)
    best_filename = get_best_co_filename_url(best_filenames, row['jobnum'])
    
    if (best_filename == 'no co') | (best_filename == 'diff job num'):
        url = ''
    else:
        url = get_co_url(best_filename)
        download_co_pdf(url, row['bin'] )

    retry_urls = pd.concat([retry_urls, 
                         pd.DataFrame.from_records([{'bin': row['bin'],
                                                     'filename': best_filename,
                                                     'url': url}])],
                        ignore_index = True)
    
    
for pdf in os.listdir(pdfs_path):
    file = pdfs_path + pdf
    size = os.path.getsize(file)
    
    pdf = pdf.split('.', 1)[0]
    
    if size < 5000:
        os.remove(file)
        url = retry_urls.loc[retry_urls['bin'] == pdf, 'url'].item()
        download_co_pdf(url, pdf)

retry_urls.to_csv(drive_path + 'retryurls.csv', index = False)

#%% Download CO PDFs - Single Project

binum = '1087979'
jobnum = '104603216'

filenames = get_co_filenames(binum)
best_filenames = get_best_co_filenames(filenames)
best_filename = get_best_co_filename_url(best_filenames)
url = get_co_url(best_filename)

download_co_pdf(url, binum)

#%% Retry Bad PDF Downloads    
  
pdfs_path = drive_path + 'pdfs_waivers/' 

for pdf in os.listdir(pdfs_path):
    file = pdfs_path + pdf
    size = os.path.getsize(file)
    
    pdf = pdf.split('.', 1)[0]
    
    if (pdf in list(urls_df['bin'])) & (size < 5000):
        os.remove(file)
        url = urls_df.loc[urls_df['bin'] == pdf, 'url'].item()
        download_co_pdf(url, pdf)

#%% Extract Parking Spaces From PDFs
    
def get_text(pdf_path):
    """ 
    This function takes a path to a CO PDF and returns the file's text 
    prepped for pattern searching. 
    Note: Text2Num only converts "one" to 1 when it is part of a sequence.
    Isolated it may be a pronoun, which is not relevant for this analysis.
    """ 
    text = extract_text(pdf_path) 
    text = alpha2digit(text, 'en') 
    text = text.lower().replace(' one ', '1') 
    text = text.replace(' ','')
    return text

def get_potential_parking(text): 
    """ 
    This function takes text extracted from a CO PDF, searches for strings
    that indicate there may be parking present and returns the number of 
    COs that may have parking.
    Note: Potential parking is an overcount, since it may capture bikes. 
    """ 
    parking_li = ['parking', 'garage', 'car', 'vehicle'] 

    if any(x in text for x in parking_li):
        parking = 1
    else: 
        parking = 0
    return parking

def get_parking_spaces(text):
    """ 
    This function takes text extracted from a CO PDF, searches for patterns
    that indicate there's parking present and returns the number of spaces.
    """ 
    pattern_li = [r"typeandnumberofopenspaces:\nparkingspaces\((\d+)\)", # type and number of open spaces: parking spaces (#)
                  r"parkingfor\((\d+)\)car", # parking for (#) car
                  r"parkingfor(\d+)car",
                  r"parkingfor\((\d+)\)vehicle", # parking for (#) vehicle
                  r"parkingfor(\d+)vehicle",
                  r"parkingfor\((\d+)\)motorvehicle", # parking for (#) motor vehicle
                  r"parkingfor(\d+)motorvehicle",
                  r"\((\d+)\)accessoryparkingspace", # (#) accessory parking space
                  r"(\d+)accessoryparkingspace",
                  r"\((\d+)\)offstreetparkingspace", # (#) off street parking space
                  r"(\d+)offstreetparkingspace", 
                  r"\((\d+)\)openparkingspace", # (#) open parking space
                  r"(\d+)openparkingspace", 
                  r"\((\d+)\)openspaceparking", # (#) open space parking
                  r"(\d+)openspaceparking", 
                  r"\((\d+)\)parkingspace", # (#) parking space, NEED TO IGNORE FOR BIKES
                  r"(\d+)parkingspace",
                  r"\((\d+)\)cargarage", # (#) car garage, ONE CAR GARAGE THREE PARKING SPACE
                  r"(\d+)cargarage",
                  r"(?<!(?:bicycle))parkingspaces\((\d+)\)", # parking spaces (#), NOT bicycle parking space/s
                  r"(?<!(?:bicycle))parkingspaces(\d+)",
                  r"(?<!(?:bicycle))parkingspace\((\d+)\)", # parking space (#), NOT bicycle parking space/s
                  r"(?<!(?:bicycle))parkingspace(\d+)"]
                               
    spaces = float('nan')
    num = float('nan')
    for pattern in pattern_li:
        p = re.compile(pattern).search(text)
        if p: 
            spaces = p.group(1)
            num = pattern_li.index(pattern) 
            break
    
    return spaces, num    

pdfs_path = path + 'output/pdfs_waivers/'
potential_parking = 0
spaces_df = pd.DataFrame(columns = ['filename', 'bin', 'du', 'spaces', 'pattern'])
bad_downloads_df = pd.DataFrame(columns = ['filename'])

for pdf in os.listdir(pdfs_path):
    try:
        text = get_text(pdfs_path + pdf)
        potential_parking += get_potential_parking(text)
    
        binum_pattern = re.compile(r"buildingidentificationnumber\(bin\):(\d+)").search(text)
        du_pattern = re.compile(r"no\.ofdwellingunits:\n\n(\d+)").search(text)
        
        spaces_df = pd.concat([spaces_df,
                               pd.DataFrame.from_records([{'filename': pdf.split('.', 1)[0],
                                                           'bin': binum_pattern.group(1),
                                                           'du': du_pattern.group(1),
                                                           'spaces': get_parking_spaces(text)[0],
                                                           'pattern': get_parking_spaces(text)[1]}])],
                              ignore_index = True) 
    except: 
        bad_downloads_df = pd.concat([bad_downloads_df,
                                      pd.DataFrame.from_records([{'filename': pdf}])],
                                     ignore_index = True)

