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

path = 'C:/Users/M_Free/Desktop/td-parking/waivers/'
local_path = 'C:/Users/M_Free/OneDrive - NYC O365 HOSTED/Projects/Parking/Waivers/'

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
# hdb_df = pd.read_csv(local_path + 'HousingDB/HousingDB_post2010_completed_jobs.csv', dtype = str)
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
# reslots_df.to_csv(path + 'output/reslots.csv', index = False)

#%% Effective Parking: Analysis

reslots_df = pd.read_csv(path + 'output/reslots.csv')

# determine if a lot in a lower density growth management area, the manhattan core (CD 1-8) or the long island city area 
ldgma_gdf = gpd.read_file('https://services5.arcgis.com/GfwWNkhOj9bNBqoJ/arcgis/rest/services/nyldgma/FeatureServer/0/query?where=1=1&outFields=*&outSR=4326&f=pgeojson')

mnc_li = ['101','102', '103', '104', '105', '106', '107', '108'] 

# permitted off-street parking in the manhattan core (zr 13-10) and long island city area (zr 16-10)

# requirements where group parking facilities are provided (zr 25-23)

# modification of requirements for small zoning lots (zr 25-24)

# waiver of requirements for small number of spaces (zr 25-26)

#%% Actual Parking