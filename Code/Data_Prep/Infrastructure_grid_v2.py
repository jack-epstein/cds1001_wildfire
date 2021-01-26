#!/usr/bin/env python
# coding: utf-8

# $\mathbf{Sources:}$<br>
# Powerlines: https://cecgis-caenergy.opendata.arcgis.com/datasets/260b4513acdb4a3a8e4d64e69fc84fee_0/data <br>
# Roads: https://www.arcgis.com/home/item.html?id=64a95b092457466388f09136e331ff09

# In[1]:


#import libraries
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from datetime import datetime


# In[2]:


#read in outlines for final gdfs
#note -- if we change our base grid size, we will need to update these and rerun this notebook
month_grid = pd.read_csv('month_grid.csv')
week_grid = pd.read_csv('week_grid.csv')


# In[3]:


#read in the specific shape files
#grids
grid_gpd = gpd.read_file('county_grid.shp')

#powerlines - read in file, create date fields and remove unneeded columnes
pl = gpd.read_file('PowerlinesData/California_Electric_Transmission_Lines.shp')
pl['created_date'] = pd.to_datetime(pl['Creator_Da'], format='%Y-%m-%d')
pl['created_month'] = pd.DatetimeIndex(pl['created_date']).month
pl['created_year'] = pd.DatetimeIndex(pl['created_date']).year
pl['created_week'] = pl['created_date'].dt.isocalendar().week
pl['week_id'] = pl['created_year'].astype(str)+'_'+pl['created_week'].astype(str)
pl['month_id'] = pl['created_year'].astype(str)+'_'+pl['created_month'].astype(str)
#make jan 2008 the minimum time period -- so move all dates before this to 1990 to fill the grid
pl.loc[(pl.month_id <= '2010_9'),'month_id']='1990_1'
pl.loc[(pl.week_id <= '2010_9'),'week_id']='1990_1'
#slim down to only needed fields and add in a length 
powerlines = pl[['OBJECTID', 'geometry', 'created_date', 'month_id', 'week_id']]
powerlines = powerlines.to_crs('epsg:3857')
powerlines['pl_length'] = powerlines['geometry'].length

#roads - read in file and remove unneeded columns. no need for date fields as we can't get this data
roads_gpd = gpd.read_file('RoadsData/tl_2019_06_prisecroads.shp')
roads = roads_gpd[['LINEARID', 'geometry']]
roads = roads.to_crs('epsg:3857')
roads['road_length'] = roads['geometry'].length


# In[4]:


#join grid shapefile with roads gdf
road_gdf = gpd.sjoin(grid_gpd, roads, op='intersects', how='left')


# In[5]:


#group by the grids, get count of roads per grid and total length
roadgrid = road_gdf.groupby(['GRID_ID']).agg({'LINEARID':'count', 'road_length': 'sum'})
roadgrid = roadgrid.rename(columns={'LINEARID': "road_count", "road_length": "total_road_length"})


# In[6]:


#join grid shapefile with powerlines gdf
powerline_gdf = gpd.sjoin(grid_gpd, powerlines, op='intersects', how='left')


# In[7]:


#group by the grids and time, get count of power lines per grid and total length
powergrid_sub_month = powerline_gdf.groupby(['GRID_ID','month_id']).agg({'OBJECTID':'count', 'pl_length': 'sum'})
powergrid_sub_month = powergrid_sub_month.reset_index()
powergrid_sub_month = powergrid_sub_month.rename(columns={"OBJECTID": "pl_count", "pl_length": "total_pl_length"})
powergrid_sub_month['GRID_ID'] = powergrid_sub_month['GRID_ID'].astype(int)
#set the oldest date -- filled in here as jan 1970 to be jan 1990
#WILL NEED TO MAKE A CHANGE HERE TO ADJUST TO PRE-2008
powergrid_sub_month['month_id'] = powergrid_sub_month['month_id'].replace("1970_1","1990_1")


#repeat by week
powergrid_sub_week = powerline_gdf.groupby(['GRID_ID','week_id']).agg({'OBJECTID':'count', 'pl_length': 'sum'})
powergrid_sub_week = powergrid_sub_week.reset_index()
powergrid_sub_week = powergrid_sub_week.rename(columns={"OBJECTID": "pl_count", "pl_length": "total_pl_length"})
powergrid_sub_week['GRID_ID'] = powergrid_sub_week['GRID_ID'].astype(int)
#set the oldest date -- filled in here as jan 1970 to be jan 1990
powergrid_sub_week['week_id'] = powergrid_sub_week['week_id'].replace("1970_1","1990_1")


# In[8]:


#join the month grid with the powergrid and change blanks to 0s
powergrid_month = month_grid.merge(powergrid_sub_month, how='left', on=['GRID_ID','month_id'])
powergrid_month = powergrid_month.fillna(0)

#repeat by week
powergrid_week = week_grid.merge(powergrid_sub_week, how='left', on=['GRID_ID','week_id'])
powergrid_week = powergrid_week.fillna(0)


# In[9]:


#get running totals of the number of powerlines and length for a given grid space
#this will have the point in time totals for a given period and space
powergrid_month_cumu = powergrid_month.merge(powergrid_month.groupby(['GRID_ID']).cumsum(), how='inner', left_index=True, right_index=True)
powergrid_month_cumu = powergrid_month_cumu.drop(['pl_count_x','total_pl_length_x'], axis=1)
powergrid_month_cumu = powergrid_month_cumu.rename(columns={'pl_count_y': "pl_count", "total_pl_length_y": "total_pl_length"})


#repeat by week
powergrid_week_cumu = powergrid_week.merge(powergrid_week.groupby(['GRID_ID']).cumsum(), how='inner', left_index=True, right_index=True)
powergrid_week_cumu = powergrid_week_cumu.drop(['pl_count_x','total_pl_length_x'], axis=1)
powergrid_week_cumu = powergrid_week_cumu.rename(columns={'pl_count_y': "pl_count", "total_pl_length_y": "total_pl_length"})


# In[10]:


#join the road and powerline data together
#then join this together with the initial grid_gpd to get the geometry data
fullmerge_month = powergrid_month_cumu.join(roadgrid, how='left', on='GRID_ID')
full_gpd_month = grid_gpd.merge(fullmerge_month, on='GRID_ID', how='right')

#repeat by week
fullmerge_week = powergrid_week_cumu.join(roadgrid, how='left', on='GRID_ID')
full_gpd_week = grid_gpd.merge(fullmerge_week, on='GRID_ID', how='right')


# In[11]:


#save cleaned data as a new file - one for month and one for week
full_gpd_month.to_file("grid_infrastructure_monthly.shp")
full_gpd_week.to_file("grid_infrastructure_weekly.shp")

