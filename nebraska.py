#This is a quick analysis of Nebraska USHCN station data wherein 
# a simple average of the monthly values for all stations is taken and plotted as a 10-year running
# mean for both the raw station values and the adjusted and homogenized values.
# Then a simple gridding scheme is applied for both datasets and the results plotted.
#
# Users can obtain the USHCN data by running the following commands in their CLI:
# wget ftp://ftp.ncdc.noaa.gov/pub/data/ushcn/v2.5/ushcn.tavg.latest.FLs.52j.tar.gz
# wget ftp://ftp.ncdc.noaa.gov/pub/data/ushcn/v2.5/ushcn.tavg.latest.raw.tar.gz
# wget ftp://ftp.ncdc.noaa.gov/pub/data/ushcn/v2.5/ushcn-v2.5-stations.txt
# tar -zxvf ushcn.tavg.latest.raw.tar.gz 
# tar -zxvf ushcn.tavg.latest.FLs.52j.tar.gz
# The analysis can then be run by running in the CLI:
# python ./ushcn_analysis.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

state_code = input("ENTER TWO LETTER STATE CODE OR LEAVE BLANK FOR ALL US STATIONS: ")
stn_list = []
stn_specs = [(0,11),(38,40)]
df_stations = pd.read_fwf('./ushcn-v2.5-stations.txt', colspecs=stn_specs, index_col=None, header=None)
state_abbrev = [
'AL',
'AZ',
'AR',
'CA',
'CO',
'CT',
'DE',
'FL',
'GA',
'ID',
'IL',
'IN',
'IA',
'KS',
'KY',
'LA',
'ME',
'MD',
'MA',
'MI',
'MN',
'MS',
'MO',
'MT',
'NE',
'NV',
'NH',
'NJ',
'NM',
'NY',
'NC',
'ND',
'OH',
'OK',
'OR',
'PA',
'RI',
'SC',
'SD',
'TN',
'TX',
'UT',
'VT',
'VA',
'WA',
'WV',
'WI',
'WY'
]

if state_code in state_abbrev:
    df_stations = df_stations[df_stations[1] == state_code]
else:
    df_stations = df_stations


li_raw = []
li_adj = []
it = 9
specs = [
        (0, 2), 
        (0, 11),
        (12,16)
        ]

for i in range(0,12):
    specs.append((16+i*it, 22+i*it))

for station in df_stations[0]:
    filepath_raw = './ushcn.v2.5.5.20221114/' + station + '.raw.tavg'
    df_raw = pd.read_fwf(filepath_raw, colspecs=specs, index_col=None, header=None)
    li_raw.append(df_raw)

    filepath_adj = './ushcn.v2.5.5.20221114/' + station + '.FLs.52j.tavg'
    df_adj = pd.read_fwf(filepath_adj, colspecs=specs, index_col=None, header=None)
    li_adj.append(df_adj)

# processing raw average
stn_raw = pd.concat(li_raw, axis=0, ignore_index=True)
stn_raw = stn_raw[~stn_raw.eq(-9999).any(1)]

for m in range(3, 15):
    stn_raw[m] = stn_raw[m] / 100

stn_raw['average'] = stn_raw[[3,4,5,6,7,8,9,10,11,12,13,14]].mean(axis=1)

rawAbs = stn_raw.groupby(2).mean('average').reset_index()

rawAbs['rolling10yr'] = rawAbs['average'].rolling(min_periods=1, window=10,center=False).mean()
rawAbs['rollingF'] = (rawAbs['rolling10yr']*9/5)+32
rawAbs = rawAbs[rawAbs[2].between(1900, 2022)]

#processing adjusted average
stn_adj = pd.concat(li_adj, axis=0, ignore_index=True)
stn_adj = stn_adj[~stn_adj.eq(-9999).any(1)]

for m in range(3, 15):
    stn_adj[m] = stn_adj[m] / 100

stn_adj['average'] = stn_adj[[3,4,5,6,7,8,9,10,11,12,13,14]].mean(axis=1)

adjAbs = stn_adj.groupby(2).mean('average').reset_index()

adjAbs['rolling10yr'] = adjAbs['average'].rolling(min_periods=1, window=10,center=False).mean()
adjAbs['rollingF'] = (adjAbs['rolling10yr']*9/5)+32
adjAbs = adjAbs[adjAbs[2].between(1900, 2022)]

#plots of average absolutes
plt.plot(rawAbs[2], rawAbs['rollingF'], label = "Average Raw Absolute")
plt.plot(adjAbs[2], adjAbs['rollingF'], label = "Average Adjusted Absolute")
plt.legend()
plt.ylabel('Temperature (deg F)')
plt.savefig("US_Raw_avg.png")
