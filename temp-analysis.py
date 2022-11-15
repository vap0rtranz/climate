# Run the ofllowing in your CLI to get copies of the data:
# wget ftp://ftp.ncdc.noaa.gov/pub/data/ghcn/v4/ghcnm.tavg.latest.qcu.tar.gz
# tar -zxvf ghcnm.tavg.latest.qcu.tar.gz
# You will also need a global land mask for gridding. The one I used is here:
# https://drive.google.com/file/d/1nSDlTfMbyquCQflAvScLM6K4dvgQ7JBj/view

import pandas as pd
import numpy as nm
import glob
import matplotlib.pyplot as plt

dirList = glob.glob('ghcnm*')

name = glob.glob('ghcnm*')

GHCNDat = glob.glob(name[0] + "/*.dat")
GHCNmeta = glob.glob(name[0] + "/*.inv")
landmask = "./landmask.dta"

# load the GHCNV4 monthly with column names
colspecs = [(0, 2), (0, 11), (11, 15), (15, 19)]
names = ['country_code', 'station', 'year', 'variable']
i = 19
for m in range(1, 13):
    mon = str(m)
    colspecs_tmp = (i, i + 5)
    names_tmp = 'VALUE' + mon

    colspecs.append(colspecs_tmp)
    names.append(names_tmp)

    i = i + 8

ghcnv4 = pd.read_fwf(GHCNDat[0],
                     colspecs=colspecs, names=names)
print("ghcn data loaded")

# load landmask
lndmsk = pd.read_stata(landmask)

# Load station metadata
stnMeta = pd.read_fwf(GHCNmeta[0], colspecs=[(0, 2), (0, 12), (12, 21), (21, 31),
                                          (31, 38), (38, 69)],
                      names=['country_code', 'station',
                             'lat', 'lon', 'elev', 'name'])

print("stn metadata loaded")

# create grids
grid_size = 5
count = -90 + (grid_size / 2)
stnMeta['latgrid'] = 0

for x in range(-90, 90, 5):
    stnMeta.loc[stnMeta['lat'].between(x, x+5), 'latgrid'] = count
    count = count + grid_size

count = -180 + (grid_size / 2)
stnMeta['longrid'] = 0

for x in range(-180, 180, 5):
    stnMeta.loc[stnMeta['lon'].between(x, x+5), 'longrid'] = count
    count = count + grid_size

stnMeta['gridbox'] = stnMeta['latgrid'].map(str) + " lat " + stnMeta['longrid'].map(str) + " lon"
stnMetaGrid = stnMeta.merge(lndmsk, on='gridbox')
stnMetaGrid['grid_weight'] = nm.sin((stnMetaGrid['latgrid'] + grid_size / 2) * nm.pi / 180) - nm.sin(
    (stnMetaGrid['latgrid'] - grid_size / 2) * nm.pi / 180)
stnMetaGrid['grid_weight'] = stnMetaGrid['grid_weight'] * stnMetaGrid['land_percent']

# clean ghcn and create anomalies

ghcnv4NoNullYears =  ghcnv4.replace(-9999, nm.nan)

print("replaced null values")

for m in range(1, 13):
    ghcnv4NoNullYears['VALUE' + str(m)] = ghcnv4NoNullYears['VALUE' + str(m)] / 100

print("converted to whole degrees")

ghcnv4NoNullYears = ghcnv4NoNullYears[ghcnv4NoNullYears.year.notnull()]

ghcnlong = ghcnv4NoNullYears.set_index('station')
ghcnlong = ghcnlong.reset_index()
ghcnlong = pd.melt(ghcnlong, id_vars=['station', 'year'],
                   value_vars=['VALUE1', 'VALUE2', 'VALUE3', 'VALUE4', 'VALUE5', 'VALUE6',
                               'VALUE7', 'VALUE8', 'VALUE9', 'VALUE10', 'VALUE11', 'VALUE12'])

print("converted wide to long")

ghcnBaselines = ghcnlong[ghcnlong['year'].between(1961, 1990)]
ghcnBaselines = ghcnBaselines.drop(columns='year')
ghcnBaselines = ghcnBaselines.groupby(['station', 'variable']).mean()
ghcnBaselines = ghcnBaselines.rename(columns={"value": "baseline"})

ghcnAnoms = ghcnlong.merge(ghcnBaselines, on=['station', 'variable'])
ghcnAnoms['anomalies'] = ghcnAnoms['value'] - ghcnAnoms['baseline']

print("calculated anomalies")

# merge on the metadata
ghcnAnomsGrid = ghcnAnoms.merge(stnMetaGrid, on=['station'])
ghcnAnomsGrid = ghcnAnomsGrid[ghcnAnomsGrid.anomalies.notnull()]
ghcnAnomsGrid = ghcnAnomsGrid.drop(columns=['baseline', 'lat', 'lon', 'elev', 'latgrid', 'longrid', 'land_percent',
                                            'ocean_percent', 'value'])
ghcnAnomsGrid = ghcnAnomsGrid.groupby(['gridbox', 'variable', 'year']).mean().reset_index()

print("gridded the data")

def weighted_average(group):
    weights = group['grid_weight']
    anomalies = group['anomalies']
    return nm.average(anomalies, weights=weights)


ghcnAnomsWtd = ghcnAnomsGrid.groupby(['year']).apply(func=weighted_average).reset_index()
ghcnAnomsWtd.columns.values[1] = "anomalies"


ghcnAnomsWtd['rolling10yr'] = ghcnAnomsWtd['anomalies'].rolling(min_periods=1, window=10,center=False).mean()
ghcnAnomsWtd['rollingF'] = (ghcnAnomsWtd['rolling10yr']*9/5)+32
ghcnAnomsWtd['annualF'] = (ghcnAnomsWtd['anomalies']*9/5)+32
ghcnAnomsWtd = ghcnAnomsWtd[ghcnAnomsWtd['year'].between(1900, 2022)]

ghcnAnomsWtd.to_excel(r'./ghcn_analysis.xlsx', index=False)

plt.plot(ghcnAnomsWtd['year'], ghcnAnomsWtd['rollingF'], label = "Average Raw 10yr")
plt.plot(ghcnAnomsWtd['year'], ghcnAnomsWtd['annualF'], label = "Average Raw Annual")
plt.legend()
plt.ylabel('Temperature (deg F)')
plt.savefig("global_anomaly.png")
