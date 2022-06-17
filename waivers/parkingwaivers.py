# -*- coding: utf-8 -*-
"""
Accessory Off-Street Parking for Residences:
Effective (Required by Zoning) vs. Actual Spaces Built
2010-Present

Assumptions: All Market Rate Units, No Special Districts
Last Modified: June 2022
"""

import pandas as pd
from sodapy import Socrata
import os
import numpy as np 

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

#%% Effective Parking: Data Download

# import and filter housing database
# hdb_df = pd.read_csv(local_path + 'Parking/Waivers/HousingDB/HousingDB_post2010_completed_jobs.csv', dtype = str)
# hdb_df = hdb_df[hdb_df['Job_Type'] == 'New Building']

# cols = ['BBL',
#         'BIN',
#         'CompltYear',
#         'UnitsCO',
#         'ZoningDst1',
#         'ZoningDst2',
#         'SpeclDst2',
#         'CommntyDst',
#         'Latitude',
#         'Longitude']

# hdb_df = hdb_df[cols]

# cols_di = {'CompltYear': 'year',
#             'UnitsCO': 'units',
#             'ZoningDst1': 'zonedist',
#             'ZoningDst2': 'zonedistb',
#             'SpeclDst2': 'spdist',
#             'CommntyDst': 'cd',
#             'Latitude': 'lat',
#             'Longitude': 'long'}

# hdb_df.rename(columns = cols_di, inplace = True)
# hdb_df.columns = hdb_df.columns.str.lower()

# # import and filter PLUTO
# data_id = '64uk-42ks'
# results = client.get(data_id, limit = 860000)
# pluto_df = pd.DataFrame.from_records(results)

# cols = ['bbl', 
#         'lotarea',
#         'lotfront',
#         'lottype',
#         'bldgclass',
#         'zonedist1',
#         'zonedist2',
#         'overlay1',
#         'spdist1']

# pluto_df = pluto_df[cols]

# # merge dfs and export 
# pluto_df['bbl'] = pluto_df['bbl'].str.split('.').str.get(-2)
# reslots_df = pd.merge(hdb_df, pluto_df, how = 'inner', on = 'bbl') # need to fix: lose ~150 rows 
# reslots_df.to_csv(path + 'input/reslots.csv', index = False)

#%% Effective Parking: Data Cleaning

# required accessory off-street parking spaces for residences when permitted in commercial districts (zr 36-30)
# permitted off-street parking in the manhattan core (zr 13-10) and long island city area (zr 16-10)
# requirements where group parking facilities are provided (zr 25-23)
# applicability of (accessory off-street parking) regulations in community district 14, queens (zr 25-027)
# applicability of (accessory off-street parking) regulations in waterfront area (zr 25-025)
# reduced requirements for small zoning lots (zr 25-241)

reslots_df = pd.read_csv(path + 'input/reslots.csv', dtype = str)
reslots_df[['units', 'lotarea', 'lotfront']] = reslots_df[['units', 'lotarea', 'lotfront']].astype(float)

# convert districts from... 

# ... mixed use to their residential component
reslots_df['zonedistadj'] = reslots_df['zonedist'].str.split('/').str.get(-1) # mx zones

# ... commercial to residential district equivalents (zr 36-30)
rde_df = pd.read_csv(path + 'input/resdistequiv.csv', dtype = str)
rde_di = rde_df.set_index('commdist')['resdist'].to_dict()
reslots_df['zonedistadj'] = reslots_df['zonedistadj'].replace(rde_di)

# ... commercial overlay to the residential districts in which they are mapped (zr 36-30)
overlay = ('C1-1', 'C1-2', 'C1-3', 'C1-4', 'C1-5', 'C2-1', 'C2-2', 'C2-3', 'C2-4', 'C2-5')
overlay_cond = (reslots_df['zonedistadj'].str.startswith(overlay)) & (reslots_df['zonedistb'].notna())
reslots_df['zonedistb'] = reslots_df['zonedistb'].replace(' ', np.nan)
reslots_df.loc[overlay_cond, 'zonedistadj'] = reslots_df['zonedistb']

# determine if lot is in ...

# ... the manhattan core or long island city area (zr 16-10)
mnc_li = ['101','102', '103', '104', '105', '106', '107', '108'] 
lic_li = pd.read_csv(path + 'input/licbbl.csv', dtype = str).loc[:,'bbl'] # gis point in polygon

reslots_df['mnc_lic'] = (reslots_df['cd'].isin(mnc_li)) | (reslots_df['bbl'].isin(lic_li))

# ... a lower density growth management area (zr 25-23)
ldgma_si = ('R1', 'R2','R3','R4A', 'R4-1', 'C1', 'C2', 'C3A', 'C4')
ldgma_bx10 = ('R1', 'R2','R3','R4A', 'R4-1', 'R6', 'R7', 'C1', 'C2', 'C3A')   

ldgma_si_cond = (reslots_df['cd'].str.startswith('5')) & (reslots_df['zonedistadj'].str.startswith(ldgma_si))
ldgma_bx10_cond = (reslots_df['cd'] == '210') & (reslots_df['zonedistadj'].str.startswith(ldgma_bx10))

reslots_df['ldgma'] = ldgma_si_cond | ldgma_bx10_cond

# adjust district name if governed by the regulations of another, including lots in a ...

# ... brooklyn R8B (zr 25-23)
bk_r8_cond = (reslots_df['cd'].str.startswith('3')) & (reslots_df['zonedistadj'] == 'R8B')
reslots_df.loc[bk_r8_cond, 'zonedistadj'] = 'R8'

# ... queens cd14 R6 or R7, but not in the adverne or edgemere urban renewal areas (zr 25-027)
ura_li = pd.read_csv(path + 'input/urabbl.csv', dtype = str).loc[:,'bbl'] # gis point in polygon
ura_cond = (reslots_df['cd'] == '414') & (~reslots_df['bbl'].isin(ura_li)) & (reslots_df['zonedistadj'].str.startswith(('R6', 'R7')))
reslots_df.loc[ura_cond,'zonedistadj'] = 'R5'

# ... waterfront area (zr 25-025)
wtr_cond = (reslots_df['lottype'] == '2') & (reslots_df['zonedistadj'] == 'R7-3')
reslots_df.loc[wtr_cond, 'zonedistadj'] = 'R7-2'

# determine if lot is considered small (zr 25-241)
small10k_li = ['R6', 'R7-1', 'R7A', 'R7B', 'R7D', 'R7X']
small15k_li = ['R7-2', 'R8', 'R9', 'R10']

small10k_cond = (reslots_df['lotarea'] <= 10000) & (reslots_df['zonedistadj'].isin(small10k_li))
small15k_cond = (reslots_df['lotarea'].between(10001, 15000)) & (reslots_df['zonedistadj'].isin(small15k_li)) & (reslots_df['zonedistadj'] != 'R8B')

reslots_df['small'] = small10k_cond | small15k_cond

#%% Effective Parking: Spaces Required

# import standard and small lot parking requirements
reqpark_df = pd.read_csv(path + 'input/reqpark.csv')

# set variables for lots not counted
# c_notcounted = 0 # commercial
# m_notcounted = 0 # manufacturing
# o_notcounted = 0 # other

#         if reslots_df['zonedistadj'].str.startswith('C') is True: 
#             c_notcounted += 1
#         elif reslots_df['zonedistadj'].str.startswith('M') is True:
#             m_notcounted += 1
#         else: 
#             o_notcounted += 1

# get required parking spaces per dwelling unit
def get_required_parking(row):
    if (row['zonedistadj'] in list(reqpark_df['zonedist'])) is False:
        multiplier = 0
    elif row['mnc_lic'] is True: 
        multiplier = 0
    elif row['small'] is True:
        ldgma_bx10_small_R71_cond = (row['cd'] == '210') & (row['zonedistadj'] == 'R7-1') &  (row['lotarea'] <= 10000) # zr 25-241
        if ldgma_bx10_small_R71_cond is True:
            multiplier = .5
        else:
            multiplier =  reqpark_df.loc[reqpark_df['zonedist'] == row['zonedistadj'], 'small'].values[0]
    elif row['ldgma'] is True:
        if row['zonedist'].startswith(('C1', 'C2')): # zr 36-321
            multiplier = 1
        else:
            multiplier = 1.5
    else: 
        multiplier = reqpark_df.loc[reqpark_df['zonedist'] == row['zonedistadj'], 'standard'].values[0]
    return multiplier

reslots_df['reqpark'] = reslots_df.apply(lambda row: get_required_parking(row), axis = 1)
reslots_df['reqspaces'] = reslots_df['units'] * reslots_df['reqpark']

#%% Effective Parking: Spaces Waived 
 
# waiver of requirements for small zoning lots in high bulk districts (zr 25-242)
# waiver of requirements for narrow zoning lots in certain districts (zr 25-243)
# waiver of requirements for small number of spaces (zr 25-26)

# determine if lot..

# is considered small or narrow
singlefam = reslots_df['bldgclass'].str.startswith('A')
interiorlot = (reslots_df['lottype'] != 3) & (reslots_df['lottype'] != 4) 

small_w_cond = (reslots_df['lotarea'] <= 10000) & (reslots_df['zonedist'].isin(small15k_li)) & (reslots_df['zonedist'] != 'R8B')
narrow_w_cond = (reslots_df['zonedist'].isin(['R3A', 'R4-1']) & (singlefam) & (interiorlot)

reslots_df['small_narrow'] = small_w_cond | narrow_w_cond               

# generates small number of spaces
spaces1_w_li = ['R4B', 'R5B', 'R5D']
spaces5_w_li = ['R6', 'R7-1', 'R7B']
spaces15_w_li = ['R7-2', 'R7A', 'R7D', 'R7X', 'R8', 'R9', 'R10']        

           
# get required parking spaces with waiver
def get_waiver_parking(row):
    if row['small_narrow'] is True:
        spaces = 0
    elif:
    else:
    return spaces

reslots_df['waiverparking'] = reslots_df.apply(lambda row: get_waiver_parking(row))

#%% Actual Parking