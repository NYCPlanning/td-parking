# -*- coding: utf-8 -*-
"""
Accessory Off-Street Parking for Residences:
Effective (Required by Zoning) vs. Actual Spaces Built
2010-Present

Assumptions: All Market Rate Units, No Special Districts
Last Modified: June 2022
"""

import pandas as pd
import geopandas as gpd 
from sodapy import Socrata
import os
import numpy as np 
import matplotlib.pyplot as plt

path = 'C:/Users/M_Free/Desktop/td-parking/waivers/'
local_path = 'C:/Users/M_Free/OneDrive - NYC O365 HOSTED/Projects/'

# DCP proxy
usernm = pd.read_csv('C:/Users/M_Free/Desktop/key.csv', dtype = str).loc[0, 'username']
passwd = pd.read_csv('C:/Users/M_Free/Desktop/key.csv', dtype = str).loc[0, 'password']
p = 'http://'+str(usernm)+':'+str(passwd)+'@dcpproxy1.dcp.nycnet:8080'
os.environ['http_proxy'] = p 
os.environ['HTTP_PROXY'] = p
os.environ['https_proxy'] = p
os.environ['HTTPS_PROXY'] = p

#Socrata API 
data_link = 'data.cityofnewyork.us'
app_token = pd.read_csv('C:/Users/M_Free/Desktop/key_opendata.csv', dtype = str).loc[0, 'token']
client = Socrata(data_link, app_token)

#%% Effective Parking: Data Cleaning

# # import and filter housing database
# hdb_df = pd.read_csv(local_path + 'Parking/Waivers/HousingDB/HousingDB_post2010_completed_jobs.csv', dtype = str)
# hdb_df = hdb_df[hdb_df['Job_Type'] == 'New Building']

# cols = ['BBL',
#         'BIN',
#         'CompltYear',
#         'UnitsCO',
#         'ZoningDst1',
#         'CommntyDst',
#         'Latitude',
#         'Longitude']

# hdb_df = hdb_df[cols]

# cols_di = {'CompltYear': 'year',
#            'UnitsCO': 'units',
#            'ZoningDst1': 'zonedist',
#            'CommntyDst': 'cd',
#            'Latitude': 'lat',
#            'Longitude': 'long'}

# hdb_df.rename(columns = cols_di, inplace = True)
# hdb_df.columns = hdb_df.columns.str.lower()

# # import and filter PLUTO
# data_id = '64uk-42ks'
# results = client.get(data_id, limit = 860000)
# pluto_df = pd.DataFrame.from_records(results)

# cols = ['bbl', 
#         'lotarea',  
#         'lotfront']

# pluto_df = pluto_df[cols]

# # merge dfs and export 
# pluto_df['bbl'] = pluto_df['bbl'].str.split('.').str.get(-2)
# reslots_df = pd.merge(hdb_df, pluto_df, how = 'inner', on = 'bbl') # need to fix: lose ~150 rows 
# reslots_df.to_csv(path + 'input/reslots.csv', index = False)

#%% Effective Parking: Spaces Required 

# permitted off-street parking in the manhattan core (zr 13-10) and long island city area (zr 16-10)
# requirements where group parking facilities are provided (zr 25-23)
# modification of requirements for small zoning lots (zr 25-24)
# waiver of requirements for small number of spaces (zr 25-26)

reslots_df = pd.read_csv(path + 'input/reslots.csv', dtype = str)

# determine if lot is the manhattan core, ... 
mnc_li = ['101','102', '103', '104', '105', '106', '107', '108'] 
reslots_df['mnc'] = reslots_df['cd'].isin(mnc_li)

# ... the long island city area, 
lic_li = pd.read_csv(path + 'input/lic_bbl.csv', dtype = str).loc[:,'bbl'] # gis point in polygon
reslots_df['lic'] = reslots_df['bbl'].isin(lic_li)

# ... or in a lower density growth management area
ldgma_si = ('R1', 'R2','R3','R4A', 'R4-1', 'C1', 'C2', 'C3A', 'C4')
ldgma_bx10 = ('R1', 'R2','R3','R4A', 'R4-1', 'R6', 'R7', 'C1', 'C2', 'C3A')   
                                                              
reslots_df['ldgma'] = np.select([reslots_df['cd'].str.startswith('5') & reslots_df['zonedist'].str.startswith(ldgma_si),
                                 (reslots_df['cd'] == '210') & reslots_df['zonedist'].str.startswith(ldgma_bx10)],
                                [True, 
                                 True],
                                default = False)

# determine if lot is considered small 
small10k_li = []
reslots_df['small10k'] = 
(reslots_df['lotarea'] < 10000) & (reslots_df['zonedist'].isin(small10k_li))

small15k_li = []
reslots_df['small15k'] =   
(reslots_df['lotarea'] < 15000) & (reslots_df['zonedist'].isin(small15k_li))

# import parking requirements
req_df = pd.read_csv(path + 'input/requiredparking.csv')

# get required parking spaces 
def get_parking (df):
    if (df['mnc'] == True) | (df['lic'] == True): # zr 13-10, zr 16-10
        spaces = 0
    elif df['small10k'] == True:
        spaces = df['units'] * req_df['small10k']
    elif df['small15k'] == True:
        spaces = df['units'] * req_df['small15k']
    else:
        spaces = df['units'] * req_df['standard']
    return spaces

#%% Effective Parking: Spaces Waived 

#%% Actual Parking