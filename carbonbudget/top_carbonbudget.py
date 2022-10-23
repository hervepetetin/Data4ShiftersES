# exec(open('./top_carbonbudget.py').read())

# user-defined input parameters
recompute = True #False
verbose = True
suffix = ''
time1 = '1990010100' ; time2 = '2020123123'
toplot = 'timeseries timeseriespersector'
path_data = '../data/carbonbudget'
path_figures = '../figures/carbonbudget'

# load libraries
import datetime
import numpy as np
import pandas as pd
import os
import requests
import xarray as xr 
import requests
from requests.auth import HTTPBasicAuth
from zipfile import ZipFile
import io
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
from bs4 import BeautifulSoup
import importlib
from pylib import pylib
importlib.reload(pylib)                                                                                                                    

# create data and figures directories
if os.path.isdir(path_data)==False:
		os.makedirs(path_data)
if os.path.isdir(path_figures)==False:
		os.makedirs(path_figures)
		
# execute file with useful functions
exec(open('./tools_carbonbudget.py').read())

# get carbon budget data
fn_save = '{}/data_carbonbudget_{}_{}{}.nc'.format(path_data,time1,time2,suffix)
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

	# get dataset
	if verbose: print('| Prepare dataset')
	variables = ['ghg_emissions','co2_emissions_percapita_wb','population'] 
	ds = xr.Dataset({},coords={'ytime' : args['ytime']})
	for ivar,var in enumerate(variables):
		if var=='ghg_emissions': 
			values_per_sector,sectors = GetSpainGHGEmissionsExtended('GHG',args['ytime'])	
			#values,values_per_sector,values_per_sector_all,sectors,tab = GetSpainEmissions('GES',args['ytime'])	
			ds = ds.merge(xr.Dataset({
					'{}_per_sector_species'.format(var):(['species','sector','ytime'],values_per_sector)},
				coords = {'sector':sectors,
									'species':np.array(['CO2','CH4','HFC','N2O','PFC','SF6'],dtype='object')})) 
		elif var=='population': 
			values = GetDataFromWorldBank('population',args['ytime']) / 1e6 #(millions inhabitants)
			ds = ds.merge(xr.Dataset({var:(['ytime'],values)})) 
		elif var=='co2_emissions_percapita_wb': 
			values = GetDataFromWorldBank('co2_emissions_percapita_wb',args['ytime'])
			ds = ds.merge(xr.Dataset({var:(['ytime'],values)})) 

	# save to netcdf
	ds.to_netcdf(fn_save)

# loop on requested plots
if verbose: print('| Plot')
for plot in toplot.split(' '):
	print(plot)

	if plot=='timeseries':
		for what in ['GHG','CO2']:
			variables_to_plot = ['ghg_emissions','population','ghg_emissions_percapita']
			varleg = {
							'ghg_emissions':'{} emissions\n(ktCO2eq)'.format(what),
							'population':'Population\n(Minhab.)',
							'ghg_emissions_percapita':'{} emissions\n(tCO2eq/inhab.)'.format(what)}
		
			plotfile = '{}/{}_{}_{}_{}{}.pdf'.format(path_figures,plot,what,time1,time2,suffix)		
			pdf_pages = PdfPages(plotfile)
			fontsize = 14
			norm = mcols.PowerNorm(gamma=1, vmin=0, vmax=len(variables_to_plot))
			cmap = plt.cm.get_cmap('viridis',10)
			fig, axarr = plt.subplots(len(variables_to_plot),1,figsize=(8,8),sharex=True)
			fig.subplots_adjust(bottom=0.1, top=0.95, left=0.2, right=0.95, hspace=0.3, wspace=0.5)
			for ivar,var in enumerate(variables_to_plot):
				ax = axarr.flatten()[ivar]
				if var=='ghg_emissions':
					if what=='GHG': 
						values = ds['ghg_emissions_per_sector_species'].sum(['sector','species']).values
					else:
						values = ds['ghg_emissions_per_sector_species'].sum('sector').sel(species=what).values
				elif var=='population':
					values = ds.population.values
				elif var=='ghg_emissions_percapita':
					if what=='GHG': 
						values = ds['ghg_emissions_per_sector_species'].sum(['sector','species']).values/ds['population'].values/1000
					else:
						values = ds['ghg_emissions_per_sector_species'].sum('sector').sel(species=what).values/ds['population'].values/1000				
							
				ax.plot(ds.ytime,values,'o-',color=cmap(norm(ivar)),alpha=0.5,ms=10,linewidth=5)
				ax.set_ylabel(varleg[var],fontsize=fontsize)
				ax.set_xlim([ds['ytime'][0],ds['ytime'][-1]])
				ax.set_axisbelow(True) ; ax.grid(color='lightgrey',linewidth=0.5) 
				ax.tick_params(axis='both', which='major', labelsize=fontsize) 
				ax.tick_params(axis='x', labelrotation=45)
				ax.yaxis.set_major_locator(plt.MaxNLocator(8))	
	
			pdf_pages.savefig(fig) ; plt.close('all')                                                                   
			plt.close('all') ; pdf_pages.close() ; print(plotfile)   

	elif plot=='timeseriespersector':
		for what in ['GHG','CO2']:
			plotfile = '{}/{}_{}_{}_{}{}.pdf'.format(path_figures,plot,what,time1,time2,suffix)		
			pdf_pages = PdfPages(plotfile)
		
			values = ds.ghg_emissions_per_sector_species.sum('species').mean('ytime').values
			wsort = np.argsort(values)[::-1]
			for k in range(6):
				sectors_to_plot = ds.sector.values[wsort][k*10:k*10+10]
		
				variables_to_plot = ['ghg_emissions','populationtotal','ghg_emissions/populationtotal']
				varleg = {
								'ghg_emissions':'{} emissions\n(ktCO2eq)'.format(what),
								'population':'Population\n(Minhab.)',
								'ghg_emissions_percapita':'{} emissions\n(tCO2eq/inhab.)'.format(what)}
		
				fontsize = 14
				norm = mcols.PowerNorm(gamma=1, vmin=0, vmax=len(sectors_to_plot))
				cmap = plt.cm.get_cmap('viridis',10)
				fig, axarr = plt.subplots(int(len(sectors_to_plot)/2),2,figsize=(12,8),sharex=True)
				fig.subplots_adjust(bottom=0.1, top=0.93, left=0.1, right=0.95, hspace=0.55, wspace=0.3)
				for isec,sec in enumerate(sectors_to_plot):
					ax = axarr.flatten()[isec]
					if what=='GHG':
						values = ds['ghg_emissions_per_sector_species'].sum('species').sel(sector=sec).values/ds['population'].values/1000
					else:
						values = ds['ghg_emissions_per_sector_species'].sel(species=what).sel(sector=sec).values/ds['population'].values/1000

					ax.plot(ds.ytime,values,'o-',color=cmap(norm(isec)),alpha=0.5,ms=10,linewidth=5)
					if len(sec)<80:
						title = pylib.SeparateOnSeveralLines(sec,nmax=50)
					else:
						title = pylib.SeparateOnSeveralLines(sec[:80],nmax=50)+'[...]'
					ax.set_title(title,fontsize=fontsize)
					ax.set_xlim([ds['ytime'][0],ds['ytime'][-1]])
					ax.set_axisbelow(True) ; ax.grid(color='lightgrey',linewidth=0.5) 
					ax.tick_params(axis='both', which='major', labelsize=fontsize) 
					ax.tick_params(axis='x', labelrotation=45)
	
				pdf_pages.savefig(fig) ; plt.close('all')                                                                   
			plt.close('all') ; pdf_pages.close() ; print(plotfile)   



# https://www.miteco.gob.es/es/calidad-y-evaluacion-ambiental/temas/sistema-espanol-de-inventario-sei-/resumen_inventario_gei-ed_2022_tcm30-534394.pdf
