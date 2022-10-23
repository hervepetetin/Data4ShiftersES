# exec(open('./top_electricity.py').read())

# user-defined input parameters
recompute = False
verbose = True
suffix = ''
time1 = '2011010100' ; time2 = '2021123123'
toplot = 'contribution_ccaa_per_gtype generation_per_ccaa'
toplot = 'generation_per_ccaa'
path_data = '../data/electricity'
path_figures = '../figures/electricity'

# load libraries
import datetime
import matplotlib.ticker as ticker
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm, PowerNorm
from matplotlib.ticker import MaxNLocator
from matplotlib.axes import Axes
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.lines import Line2D
import matplotlib.dates as mdates
from matplotlib import collections as mc
import matplotlib.colors as mcols 
import numpy as np
import os
import pandas as pd
import requests
import xarray as xr 
import csv, pyodbc
import importlib
from pylib import pylib
importlib.reload(pylib)                                                                                                                  


# create data and figures directories
if os.path.isdir(path_data)==False:
		os.makedirs(path_data)
if os.path.isdir(path_figures)==False:
		os.makedirs(path_figures)
		
# execute file with useful functions
exec(open('./tools_electricity.py').read())

# define CCAAs (including entire peninsula)
ccaa = np.array(['Peninsula',
	'Islas Canarias',	'Islas Baleares',	'Comunidad de Ceuta',	'Comunidad de Melilla',
	'Andalucía', 	'Aragón',	'Cantabria', 'Castilla la Mancha', 'Castilla y León',
	'Cataluña', 'País Vasco', 'Principado de Asturias', 'Comunidad de Madrid',
	'Comunidad de Navarra', 'Comunidad Valenciana', 'Extremadura', 'Galicia',
	'La Rioja', 'Región de Murcia'])

# define types of electricity generation
gtype = np.array(['Total generation','Coal','Cogeneration','Combined cycle','Hydro','Non-renewable waste','Renewable waste',
 	'Other renewables','Pumped storage','Solar photovoltaic','Thermal solar','Fuel + Gas','Nuclear',
 	'Wind','Hydroeolian','Steam turbine','Diesel engines','Gas turbine'],dtype='object')

# get electricity data
fn_save = '{}/data_electricity_{}_{}{}.nc'.format(path_data,time1,time2,suffix)
if recompute==False and os.path.isfile(fn_save)==True:
	# read dataset
	ds = xr.open_dataset(fn_save)
	ds.close()
else:
	# prepare directories
	dir = os.path.dirname(fn_save)
	if os.path.isdir(dir)==False:
		os.makedirs(dir)
	
	# create time arrays
	if verbose: print('| Create time arrays')
	args = pylib.PrepareTimeArrays(time1, time2)

	# get electricity demand dataset
	if verbose: print('| Get electricity demand data')
	ds = GetDemandData(args,ccaa,fn_save)

	# add electricity generation dataset
	ds = ds.merge(GetGenerationData(args,gtype,ccaa,fn_save))

	# add relative contribution per CCAA
	ds = ds.merge(GetContribution(ds))

	# save to netcdf
	ds.to_netcdf(fn_save)



# loop on requested plots
if verbose: print('| Plot')
for plot in toplot.split(' '):
	print(plot)
	
	if plot=='contribution_ccaa_per_gtype':	
		values = ds.ygeneration.sel(ccaa='Peninsula').mean('ytime').values
		gtype_toplot = ds.gtype.values[np.argsort(values)[::-1]]

		plotfile = '{}/{}_{}_{}{}.pdf'.format(path_figures,plot,time1,time2,suffix)
		pdf_pages = PdfPages(plotfile)
		fontsize,markersize,alpha = 14,8,0.5
		marker = dict(zip(ds.ccaa.values,list(Line2D.markers.keys())[:ds.dims['ccaa']]))
		norm = mcols.PowerNorm(gamma=1, vmin=0, vmax=ds.dims['ccaa']-1)
		cmap = plt.cm.get_cmap('viridis',ds.dims['ccaa']) 
		for gtype in gtype_toplot:
			if np.isfinite(ds.ycontribution.sel(gtype=gtype).values).any()==False: continue
			fig, axarr = plt.subplots(1,2,figsize=(8,8))
			fig.subplots_adjust(bottom=0.1, top=0.8, left=0.15, right=0.95, hspace=0.3, wspace=0.5)
			for ipanel in range(2):
				ax = axarr.flatten()[ipanel]
				for iccaa,ccaa in enumerate(ds.ccaa.values):
					if ipanel==0: values = ds.ycontribution.sel(ccaa=ccaa,gtype=gtype).values
					if ipanel==1: values = ds.ygeneration.sel(ccaa=ccaa,gtype=gtype).values
					if np.isfinite(values).any()==False: continue
					if ccaa=='Peninsula' or np.nanmax(values)==0: continue
					label = '{} ({:0.0f}|{:0.0f}|{:0.0f}%)'.format(ccaa,np.nanmean(values),values[0],values[-1])
					ax.plot(ds.ytime,values,'{}-'.format(marker[ccaa]),color=cmap(norm(iccaa)),alpha=alpha,label=label,ms=7)
					
				if ipanel==0:
					ax.set_ylabel('Contribution of each CCAA\nto total production (%)', fontsize=fontsize)                                                                                            
					total_gtype = ds.ygeneration.sel(gtype=gtype,ccaa='Peninsula').mean('ytime').values
					total = ds.ygeneration.sel(gtype='Total generation',ccaa='Peninsula').mean('ytime').values
					title = '{} ({:0.0f} GWh/year; {:0.0f}%)'.format(gtype,total_gtype,total_gtype/total*100)
					ax.set_title(title,fontsize=fontsize)
					handles, labels = ax.get_legend_handles_labels()
				else:
					ax.set_ylabel('Production (GWh/year)', fontsize=fontsize)
					
				#ax.set_xlim([ds['{}time'.format(ts)][0],ds['{}time'.format(ts)][-1]])
				ax.set_xlim([ds['ytime'][0],ds['ytime'][-1]])
				ax.set_axisbelow(True) ; ax.grid(color='lightgrey',linewidth=0.5) 
				ax.tick_params(axis='both', which='major', labelsize=fontsize) 
				ax.tick_params(axis='x', labelrotation=45)
				ax.yaxis.set_major_locator(plt.MaxNLocator(8))	
	
			fig.legend(handles, labels, loc='upper center',fontsize=fontsize*0.6,ncol=3) 
	
			pdf_pages.savefig(fig) ; plt.close('all')                                                                   
		plt.close('all') ; pdf_pages.close() ; print(plotfile)   
  

	elif plot=='generation_per_ccaa':
		
		plotfile = '{}/{}_{}_{}{}.pdf'.format(path_figures,plot,time1,time2,suffix)		
		pdf_pages = PdfPages(plotfile)
		fontsize,markersize = 14,8
		marker = dict(zip(ds.gtype.values,list(Line2D.markers.keys())[:ds.dims['gtype']]))

		values = ds.ygeneration.sum('ccaa').mean('ytime').values
		values = ds.ygeneration.sum('ccaa').mean('ytime').values/ds.ygeneration.sum('ccaa').sel(gtype='Total generation').mean('ytime').values*100
		gtype_toplot = ds.gtype.values[np.where((values > 1) & (values!=100))]
		
		values = ds.ygeneration.sel(gtype='Total generation').mean('ytime').values
		ccaa_toplot = ds.ccaa.values[np.argsort(values)[::-1]]#[:3]

		norm = mcols.PowerNorm(gamma=1, vmin=0, vmax=len(gtype_toplot)-1)
		cmap = plt.cm.get_cmap('viridis',15)  

		for igtype,gtype in enumerate(ds.gtype.values):
			values_total = ds.dgeneration.sel(gtype='Total generation',ccaa='Peninsula').sum('dtime').values
			values = ds.dgeneration.sel(gtype=gtype,ccaa='Peninsula').sum('dtime').values
			print('{:>25s} {:10.0f} {:10.0f}%'.format(gtype,values,values/values_total*100))
	
		for ccaa in ccaa_toplot:
			fig, axarr = plt.subplots(4,1,figsize=(8,8),sharex=True)
			fig.subplots_adjust(bottom=0.1, top=0.8, left=0.2, right=0.95, hspace=0.3, wspace=0.5)
			for ipanel in range(4):
				ax = axarr.flatten()[ipanel]
				for igtype,gtype in enumerate(gtype_toplot):

					ts='y' if ipanel<2 else 'm'
					if ipanel in [0,2]:
						ax.set_ylabel('Generation\n(GWh/{})'.format({'y':'year','m':'month','d':'day'}[ts]), fontsize=fontsize)                                                                                            
						values = ds['{}generation'.format(ts)].sel(gtype=gtype,ccaa=ccaa).values
					elif ipanel in [1,3]:
						ax.set_ylabel('(%spain)', fontsize=fontsize)                                                                                            
						values_peninsula = ds['{}generation'.format(ts)].sel(gtype=gtype,ccaa='Peninsula').values
						values = ds['{}generation'.format(ts)].sel(gtype=gtype,ccaa=ccaa).values/values_peninsula*100

					alpha = 0.5
			
					part_peninsula_for_gtype = ds.ygeneration.sel(gtype=gtype,ccaa=ccaa).values/\
											ds.ygeneration.sel(gtype=gtype,ccaa='Peninsula').values*100
					part_ccaa = ds.ygeneration.sel(gtype=gtype,ccaa=ccaa).values/\
											ds.ygeneration.sel(gtype='Total generation',ccaa=ccaa).values*100
			
					label = '{} ({:0.0f}|{:0.0f}|{:0.0f}%spain ; {:0.0f}|{:0.0f}|{:0.0f}%region)'.format(gtype,
							np.nanmean(part_peninsula_for_gtype),part_peninsula_for_gtype[0],part_peninsula_for_gtype[-1],
							np.nanmean(part_ccaa),part_ccaa[0],part_ccaa[-1])
					if ts=='y': ax.plot(ds['{}time'.format(ts)],values,'{}-'.format(marker[gtype]),color=cmap(norm(igtype)),label=label,markersize=markersize,alpha=alpha)
					if ts=='m': ax.plot(ds['{}time'.format(ts)],values,'{}-'.format(marker[gtype]),color=cmap(norm(igtype)),label=label,markersize=markersize*0.2,alpha=alpha)

					if ipanel==0:
						ccaa_mean = ds.ygeneration.sel(gtype='Total generation',ccaa=ccaa).mean('ytime').values
						total_mean = ds.ygeneration.sel(gtype='Total generation',ccaa='Peninsula').mean('ytime').values
						ccaa_percentage = np.nanmean(ccaa_mean/total_mean*100)
						title = '{}\n(mean={:0.0f}GWh/year; {:0.0f}%)'.format(ccaa,ccaa_mean,ccaa_percentage)
						ax.set_title(title,fontsize=fontsize)
						handles, labels = ax.get_legend_handles_labels()
				
				ax.set_xlim([ds['{}time'.format(ts)][0],ds['{}time'.format(ts)][-1]])
				ax.set_axisbelow(True) ; ax.grid(color='lightgrey',linewidth=0.5) 
				ax.tick_params(axis='both', which='major', labelsize=fontsize) 
				ax.tick_params(axis='x', labelrotation=45)
				ax.yaxis.set_major_locator(plt.MaxNLocator(8))	
	
			fig.legend(handles, labels, loc='upper center',fontsize=fontsize*0.6,ncol=2) 
	
			pdf_pages.savefig(fig) ; plt.close('all')                                                                   
		plt.close('all') ; pdf_pages.close() ; print(plotfile)   
  
	elif plot=='demand_per_ccaa':
		# load dataset
		fn_save = './data_{}_{}_{}.nc'.format(time1,time2,nccaa)
		ds = xr.open_dataset(fn_save)
		ds.close()

		plotfile = './plot_{}.pdf'.format(plot)
		pdf_pages = PdfPages(plotfile)
		fontsize,markersize = 14,8
		marker = dict(zip(ds.gtype.values,list(Line2D.markers.keys())[:ds.dims['gtype']]))

		values = ds.ygeneration.sum('ccaa').mean('ytime').values
		gtype_toplot = ds.gtype.values[np.where(values/np.nansum(values)*100 > 1)]

		values = ds.ygeneration.sel(gtype='Total generation').mean('ytime').values
		ccaa_toplot = ds.ccaa.values[np.argsort(values)[::-1]]#[:3]

		norm = mcols.PowerNorm(gamma=1, vmin=0, vmax=len(gtype_toplot)-1)
		cmap = plt.cm.get_cmap('viridis',15)  

		for igtype,gtype in enumerate(ds.gtype.values):
			values_total = ds.dgeneration.sel(gtype='Total generation',ccaa='Peninsula').sum('dtime').values
			values = ds.dgeneration.sel(gtype=gtype,ccaa='Peninsula').sum('dtime').values
			print('{:>25s} {:10.0f} {:10.0f}%'.format(gtype,values,values/values_total*100))
	
		for ccaa in ccaa_toplot:
			fig, axarr = plt.subplots(4,1,figsize=(8,8),sharex=True)
			fig.subplots_adjust(bottom=0.1, top=0.8, left=0.2, right=0.95, hspace=0.3, wspace=0.5)
			for ipanel in range(4):
				ax = axarr.flatten()[ipanel]
				for igtype,gtype in enumerate(gtype_toplot):

					ts='y' if ipanel<2 else 'm'
					if ipanel in [0,2]:
						ax.set_ylabel('Generation\n(GWh/{})'.format({'a':'year','m':'month','d':'day'}[ts]), fontsize=fontsize)                                                                                            
						values = ds['{}generation'.format(ts)].sel(gtype=gtype,ccaa=ccaa).values
					elif ipanel in [1,3]:
						ax.set_ylabel('(%)', fontsize=fontsize)                                                                                            
						values_peninsula = ds['{}generation'.format(ts)].sel(gtype=gtype,ccaa='Peninsula').values
						values = ds['{}generation'.format(ts)].sel(gtype=gtype,ccaa=ccaa).values/values_peninsula*100
				
					if gtype=='Total generation': continue
					alpha = 0.5
			
					values_peninsula = ds.ygeneration.sel(gtype=gtype,ccaa='Peninsula').values
					values_ccaa_vs_peninsula = ds.ygeneration.sel(gtype=gtype,ccaa=ccaa).values/values_peninsula*100
					values_ccaa_total = ds.ygeneration.sel(gtype='Total generation',ccaa=ccaa).values
					values_ccaa_vs_ccaa = ds.ygeneration.sel(gtype=gtype,ccaa=ccaa).values/values_ccaa_total*100
			
					label = '{} ({:0.0f}%|{:0.0f}%|{:0.0f}% ; {:0.0f}%|{:0.0f}%|{:0.0f}%)'.format(gtype,
							np.nanmean(values_ccaa_vs_ccaa),values_ccaa_vs_ccaa[0],values_ccaa_vs_ccaa[-1],
							np.nanmean(values_ccaa_vs_peninsula),values_ccaa_vs_peninsula[0],values_ccaa_vs_peninsula[-1])
					if ts=='y': ax.plot(ds['{}time'.format(ts)],values,'{}-'.format(marker[gtype]),color=cmap(norm(igtype)),label=label,markersize=markersize,alpha=alpha)
					if ts=='m': ax.plot(ds['{}time'.format(ts)],values,'{}-'.format(marker[gtype]),color=cmap(norm(igtype)),label=label,markersize=markersize*0.2,alpha=alpha)

					if ipanel==0:
						ccaa_mean = ds.ygeneration.sel(gtype='Total generation',ccaa=ccaa).mean('ytime').values
						total_mean = ds.ygeneration.sel(gtype='Total generation',ccaa='Peninsula').mean('ytime').values
						ccaa_percentage = np.nanmean(ccaa_mean/total_mean*100)
						title = '{}\n(mean={:0.0f}GWh/year; {:0.0f}%)'.format(ccaa,ccaa_mean,ccaa_percentage)
						ax.set_title(title,fontsize=fontsize)
						handles, labels = ax.get_legend_handles_labels()
				
				ax.set_xlim([ds['{}time'.format(ts)][0],ds['{}time'.format(ts)][-1]])
				ax.set_axisbelow(True) ; ax.grid(color='lightgrey',linewidth=0.5) 
				ax.tick_params(axis='both', which='major', labelsize=fontsize) 
				ax.tick_params(axis='x', labelrotation=45)
				ax.yaxis.set_major_locator(plt.MaxNLocator(8))	
	
			fig.legend(handles, labels, loc='upper center',fontsize=fontsize*0.6,ncol=2) 
	
			pdf_pages.savefig(fig) ; plt.close('all')                                                                   
		plt.close('all') ; pdf_pages.close() ; print(plotfile)   