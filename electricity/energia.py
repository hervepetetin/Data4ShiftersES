# exec(open('./energia.py').read())

# load libraries
import datetime
import numpy as np
import pandas as pd
import os
import requests
import xarray as xr 

# input parameters
time1 = '2011010100' ; time2 = '2021123123'
#time1 = '2011010100' ; time2 = '2022073123'
#time1 = '2020010100' ; time2 = '2021123123'

# define additional information
geo_ids = {
	'Peninsula':8741,
	'Islas Canarias':8742,
	'Islas Baleares':8743,
	'Comunidad de Ceuta':8744,
	'Comunidad de Melilla':8745,
	'Andalucía':4,
	'Aragón':5,
	'Cantabria':6,
	'Castilla la Mancha':7,
	'Castilla y León':8,
	'Cataluña':9,
	'País Vasco':10,
	'Principado de Asturias':11,
	'Comunidad de Madrid':13,
	'Comunidad de Navarra':14,
	'Comunidad Valenciana':15,
	'Extremadura':16,
	'Galicia':17,
	'La Rioja':20,
	'Región de Murcia':21}
#geo_ids = {'Peninsula':8741,'Andalucía':4,'Cataluña':9}
ccaa = np.array(list(geo_ids.keys()),dtype='object')
nccaa = len(ccaa)

gtype = np.array(['Total generation','Coal','Cogeneration','Combined cycle','Hydro','Non-renewable waste','Renewable waste',
 	'Other renewables','Pumped storage','Solar photovoltaic','Thermal solar','Fuel + Gas','Nuclear',
 	'Wind','Hydroeolian','Steam turbine','Diesel engines','Gas turbine'],dtype='object')
ngtype = len(gtype)

def SplitArray(x,n_per_group=None,n_groups=None):
    import numpy as np
    if not n_groups is None:
        n_per_group = np.ceil(len(x)/n_groups)

    istat, grp, grps = 0, [], []
    while istat <= len(x)-1:
        grp += [istat]
        if len(grp)==n_per_group:
            grps += [grp]
            grp = []
        istat += 1
    if len(grp)!=0: grps += [grp]
    return(grps)

# create time arrays
args = {}
args['time1'] = time1
args['time2'] = time2
args['date1'] = pd.to_datetime(datetime.datetime.strptime(time1, '%Y%m%d%H')) # (starting time)
args['date2'] = pd.to_datetime(datetime.datetime.strptime(time2, '%Y%m%d%H')) # (ending time, included)
args['date1_first_day_of_month'] = pd.to_datetime(datetime.datetime.strptime(time1[0:6]+'0100', '%Y%m%d%H'))
args['date1_first_day_of_year'] = pd.to_datetime(datetime.datetime.strptime(time1[0:4]+'010100', '%Y%m%d%H'))
args['dtime'] = pd.date_range(args['date1'], args['date2'], freq='D') 
args['ndtime'] = len(args['dtime'])
args['mtime'] = pd.date_range(args['date1_first_day_of_month'], args['date2'], freq='MS')
args['nmtime'] = len(args['mtime'])
args['atime'] = pd.date_range(args['date1_first_day_of_year'], args['date2'], freq='AS')
args['natime'] = len(args['atime'])


def GetGenerationData(args,gtype,ccaa):
	ngtype,nccaa = len(gtype),len(ccaa)
	# create empty dataset
	ds = xr.Dataset({	
						'dgeneration' : (['gtype','ccaa','dtime'],np.full([ngtype,nccaa,args['ndtime']],np.nan)),
						'mgeneration' : (['gtype','ccaa','mtime'],np.full([ngtype,nccaa,args['nmtime']],np.nan)),
						'ageneration' : (['gtype','ccaa','atime'],np.full([ngtype,nccaa,args['natime']],np.nan))},
		coords = {'gtype'	: gtype,
							'ccaa'  : ccaa,
							'dtime' : args['dtime'],
							'mtime' : args['mtime'],
							'atime' : args['atime']})

	# loop on CCAA
	for ccaa,ccaa_id in geo_ids.items():
		print(ccaa)
	
		# locate ccaa in dataset
		iccaa = np.where(ds.ccaa.values==ccaa)[0][0]
	
		# loop on year
		grps = SplitArray(args['dtime'],n_per_group=366)
		for igrp,grp in enumerate(grps):
			#print([args['dtime'][grp[0]].strftime('%Y-%m-%d'),args['dtime'][grp[-1]].strftime('%Y-%m-%d')])
			# request data
			url = ('https://apidatos.ree.es/en/datos/generacion/estructura-generacion?'+
				'start_date={}T00:00&end_date={}T23:59'+
				'&time_trunc=day&geo_limit=ccaa&geo_ids={}').format(
				args['dtime'][grp[0]].strftime('%Y-%m-%d'),args['dtime'][grp[-1]].strftime('%Y-%m-%d'),ccaa_id)
			response = requests.get(url)

			# check if request successful
			if response.status_code!=200:
				print('Request returned an error.')
				print(url)
				print(response.json()['errors'][0]['detail'])
				continue
				
			# get generation types
			ndata = len(response.json()['included'])
			generation_type_ = np.array([response.json()['included'][idata]['type'] for idata in range(ndata)], dtype='object')

			# fill dataset
			for idata in range(ndata):
				gtype_ = response.json()['included'][idata]['type']
				igtype = np.where(ds.gtype.values==gtype_)[0][0]
				attributes_values = response.json()['included'][idata]['attributes']['values']
				# get useful values
				xvalues = [attributes_values[i]['value'] for i in range(len(attributes_values))]
				xdatetime = pd.to_datetime([attributes_values[i]['datetime'][:10] for i in range(len(attributes_values))])
				# get intersection of dates
				wintersect = np.intersect1d(args['dtime'],xdatetime, assume_unique=True, return_indices=True)			
				# fill after change of unit (MWh => GWh)
				ds.dgeneration[dict(gtype=igtype,ccaa=iccaa,dtime=wintersect[1])] = np.array(xvalues)/1e3
				#print('{:3d}  {:>25s} {:12.0f}'.format(igtype,gtype_,xvalues[-1]))
		#print('{:15s}: {:0.0f}'.format(ccaa,ds.dgeneration.sel(ccaa=ccaa).sum().values))

	# add monthly and annual sum
	ds.mgeneration[dict()] = ds.dgeneration.resample(dtime='1MS').sum().values
	ds.ageneration[dict()] = ds.dgeneration.resample(dtime='1YS').sum().values

	# save
	fn_save = './data_generation_{}_{}_{}.nc'.format(time1,time2,nccaa)
	if os.path.isfile(fn_save):
		os.remove(fn_save)
	ds.to_netcdf(fn_save)
	
	return ds


def GetDemandData(args,ccaa):
	nccaa = len(ccaa)
	
	# create empty dataset
	ds = xr.Dataset({	
						'ddemand' : (['ccaa','dtime'],np.full([nccaa,args['ndtime']],np.nan)),
						'mdemand' : (['ccaa','mtime'],np.full([nccaa,args['nmtime']],np.nan)),
						'ademand' : (['ccaa','atime'],np.full([nccaa,args['natime']],np.nan))},
		coords = {'ccaa'  : ccaa,
							'dtime' : args['dtime'],
							'mtime' : args['mtime'],
							'atime' : args['atime']})

	# loop on CCAA
	for ccaa,ccaa_id in geo_ids.items():
		print(ccaa)
	
		# locate ccaa in dataset
		iccaa = np.where(ds.ccaa.values==ccaa)[0][0]
	
		# loop on year
		grps = SplitArray(args['dtime'],n_per_group=366)
		for igrp,grp in enumerate(grps):
			#print([args['dtime'][grp[0]].strftime('%Y-%m-%d'),args['dtime'][grp[-1]].strftime('%Y-%m-%d')])
			# request data
			url = ('https://apidatos.ree.es/en/datos/demanda/evolucion?'+
				'start_date={}T00:00&end_date={}T23:59'+
				'&time_trunc=day&geo_limit=ccaa&geo_ids={}').format(
				args['dtime'][grp[0]].strftime('%Y-%m-%d'),args['dtime'][grp[-1]].strftime('%Y-%m-%d'),ccaa_id)
			response = requests.get(url)

			# check if request successful
			if response.status_code!=200:
				print('Request returned an error.')
				print(url)
				print(response.json()['errors'][0]['detail'])
				continue

			# fill dataset
			attributes_values =response.json()['included'][0]['attributes']['values']
			# get useful values
			xvalues = [attributes_values[i]['value'] for i in range(len(attributes_values))]
			xdatetime = pd.to_datetime([attributes_values[i]['datetime'][:10] for i in range(len(attributes_values))])
			# get intersection of dates
			wintersect = np.intersect1d(args['dtime'],xdatetime, assume_unique=True, return_indices=True)			
			# fill after change of unit (MWh => GWh)
			ds.ddemand[dict(ccaa=iccaa,dtime=wintersect[1])] = np.array(xvalues)/1e3

	# add monthly and annual sum
	ds.mdemand[dict()] = ds.ddemand.resample(dtime='1MS').sum().values
	ds.ademand[dict()] = ds.ddemand.resample(dtime='1YS').sum().values

	# save
	fn_save = './data_demand_{}_{}_{}.nc'.format(time1,time2,nccaa)
	if os.path.isfile(fn_save):
		os.remove(fn_save)
	ds.to_netcdf(fn_save)
	
	return ds

#ds = GetDemandData(args,ccaa)
zz

#GetGenerationData(args,gtype,ccaa)

			
# plot
#exec(open('./analyze_energia.py').read())
