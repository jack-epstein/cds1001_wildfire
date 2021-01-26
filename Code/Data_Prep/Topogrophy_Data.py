#!/usr/bin/env python
# coding: utf-8

# https://www.usgs.gov/core-science-systems/eros/coastal-changes-and-impacts/contour-preliminary-contour-data

# ## The goal here is to use countour elevation data to proxy our topography within each grid
# - We can import contoured shapefiles of all of California, which include elevation of each contour line
# - Then super-impose our sqaure grids with these countours
# - We can then look at the average elevation as a general proxy for the full regions elevation
# - We can use standard deviation as a loose proxy for "slope" is areas
# - Another proxy for slope can be the difference between the max and min height in a given grid
# <br><br>
# - NOTE: Elevations are in feet. As a check of these calculations, the mean elevation in California is ~2.9k feet, while our final dataframe is at ~3k

# In[1]:


import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


# In[2]:


#read in files -- do not rerun unless needed, will be slow
socal = gpd.read_file('CA_preliminary_south.gdb')
centcal = gpd.read_file('CA_preliminary_central.gdb')
nocal = gpd.read_file('CA_preliminary_north.gdb')


# In[3]:


#read in grid shapefile
grids = gpd.read_file('county_grid.shp')
grids = grids.to_crs('EPSG:4269')


# In[4]:


#merge into one large geodataframe
full_cali_contour = pd.concat([nocal, centcal, socal])
full_cali_contour.shape


# In[6]:


#join with the grid data - DO NOT RERUN UNLESS NEEDED
grid_contour = gpd.sjoin(grids, full_cali_contour, op='intersects', how='left')


# In[55]:


#narrow down the columns to use -- really only elevation matters
grid_contour_slim = grid_contour[['GRID_ID', 'COUNTYFP', 'GEOID', 'NAME', 'ContourElevation', 'ContourUnits', 'ContourInterval', 'Depression', 'MapID']]


# In[54]:


#group by basic elevation stats
grid_elev_stats = grid_contour_slim.groupby(['GRID_ID']).agg({'ContourElevation':['mean','std','median','max','min']})
grid_elev_stats.columns=['elev_mean','elev_std','elev_median','elev_max','elev_min']
#add in a field with the difference between max and min
grid_elev_stats['elev_range'] = grid_elev_stats['elev_max']-grid_elev_stats['elev_min']


# In[39]:


#rejoin with grid id to get the geometries
grid_elev = grids.merge(grid_elev_stats, on='GRID_ID', how='right')


# In[42]:


#plot out grid by key metrics
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14,10))

ax1.set_title('Mean Elevation by Grid')
ax2.set_title('Elevation STDev by Grid')
ax3.set_title('Median Elevation by Grid')
ax4.set_title('Diff between Max and Min by Grid')
grid_elev.plot(column=('elev_mean'), ax=ax1, legend=True)
grid_elev.plot(column=('elev_std'), ax=ax2, legend=True)
grid_elev.plot(column=('elev_median'), ax=ax3, legend=True)
grid_elev.plot(column=('elev_range'), ax=ax4, legend=True)


# In[57]:


#save newest gdf as shape file and try pushing to git
grid_elev.to_file("grid_elevation_1117.shp")


# In[68]:


#send data to pickle files -- do in small chunks to not kill computer
#commenting out to avoid computation issues
#n_rows = np.round(len(full_cali_contour)/10,0).astype(int)
#full_cali_contour.iloc[:n_rows].to_pickle('topo_raw_1.pkl')


# In[69]:


#next batch - not looping to avoid crashing
#full_cali_contour.iloc[n_rows:2*n_rows].to_pickle('topo_raw_2.pkl')
#full_cali_contour.iloc[2*n_rows:3*n_rows].to_pickle('topo_raw_3.pkl')
#full_cali_contour.iloc[3*n_rows:4*n_rows].to_pickle('topo_raw_4.pkl')


# In[70]:


#next batch
#full_cali_contour.iloc[4*n_rows:5*n_rows].to_pickle('topo_raw_5.pkl')
#full_cali_contour.iloc[5*n_rows:6*n_rows].to_pickle('topo_raw_6.pkl')
#full_cali_contour.iloc[6*n_rows:7*n_rows].to_pickle('topo_raw_7.pkl')


# In[71]:


#last batch
#full_cali_contour.iloc[7*n_rows:8*n_rows].to_pickle('topo_raw_8.pkl')
#full_cali_contour.iloc[8*n_rows:9*n_rows].to_pickle('topo_raw_9.pkl')
#full_cali_contour.iloc[9*n_rows:].to_pickle('topo_raw_10.pkl')

