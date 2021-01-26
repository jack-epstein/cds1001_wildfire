#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt


# In[2]:


#read in the specific files
#grids
grid_gpd = gpd.read_file('county_grid.shp')

#powerlines
pl = gpd.read_file('California_Electric_Transmission_Lines.shp')
powerlines = pl[['OBJECTID', 'geometry']]
powerlines = powerlines.to_crs('epsg:3857')
powerlines['pl_length'] = powerlines['geometry'].length

#roads
roads_gpd = gpd.read_file('tl_2019_06_prisecroads.shp')
roads = roads_gpd[['LINEARID', 'geometry']]
roads = roads.to_crs('epsg:3857')
roads['road_length'] = roads['geometry'].length


# In[3]:


#joins with grids and each other gis file
powerline_gdf = gpd.sjoin(grid_gpd, powerlines, op='intersects', how='left')
road_gdf = gpd.sjoin(grid_gpd, roads, op='intersects', how='left')


# In[4]:


#group by the grids, get count of power lines per grid and total length
powergrid = powerline_gdf.groupby(['GRID_ID']).agg({'OBJECTID':'count', 'pl_length': 'sum'})
powergrid = powergrid.rename(columns={"OBJECTID": "pl_count", "pl_length": "total_pl_length"})


# In[5]:


#group by the grids, get count of roads per grid and total length
roadgrid = road_gdf.groupby(['GRID_ID']).agg({'LINEARID':'count', 'road_length': 'sum'})
roadgrid = roadgrid.rename(columns={'LINEARID': "road_count", "road_length": "total_road_length"})


# In[6]:


#join these 2 new dfs - then join with the full gpd
fullmerge = powergrid.join(roadgrid, how='outer')
full_gpd = grid_gpd.join(fullmerge, on='GRID_ID', how='right')


# In[7]:


#save cleaned data as a new file
full_gpd.to_file("grid_infrastructure.shp")

