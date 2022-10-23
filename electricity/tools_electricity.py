
import numpy as np
import importlib
from pylib import pylib
importlib.reload(pylib)                                                                                                                    


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


def GetGenerationData(args,gtype,ccaa,fn_save):
	ngtype,nccaa = len(gtype),len(ccaa)
	# create empty dataset
	ds = xr.Dataset({	
						'dgeneration' : (['gtype','ccaa','dtime'],np.full([ngtype,nccaa,args['ndtime']],np.nan)),
						'mgeneration' : (['gtype','ccaa','mtime'],np.full([ngtype,nccaa,args['nmtime']],np.nan)),
						'ygeneration' : (['gtype','ccaa','ytime'],np.full([ngtype,nccaa,args['nytime']],np.nan))},
		coords = {'gtype'	: gtype,
							'ccaa'  : ccaa,
							'dtime' : args['dtime'],
							'mtime' : args['mtime'],
							'ytime' : args['ytime']})

	# loop on CCAA
	for ccaa,ccaa_id in geo_ids.items():
		print(ccaa)
	
		# locate ccaa in dataset
		iccaa = np.where(ds.ccaa.values==ccaa)[0][0]
	
		# loop on year
		grps = pylib.SplitArray(args['dtime'],n_per_group=366)
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
	ds.ygeneration[dict()] = ds.dgeneration.resample(dtime='1YS').sum().values

	# save
	if os.path.isfile(fn_save):
		os.remove(fn_save)
	ds.to_netcdf(fn_save)
	
	return ds


def GetDemandData(args,ccaa,fn_save):
	nccaa = len(ccaa)
	
	# create empty dataset
	ds = xr.Dataset({	
						'ddemand' : (['ccaa','dtime'],np.full([nccaa,args['ndtime']],np.nan)),
						'mdemand' : (['ccaa','mtime'],np.full([nccaa,args['nmtime']],np.nan)),
						'ydemand' : (['ccaa','ytime'],np.full([nccaa,args['nytime']],np.nan))},
		coords = {'ccaa'  : ccaa,
							'dtime' : args['dtime'],
							'mtime' : args['mtime'],
							'ytime' : args['ytime']})

	# loop on CCAA
	for ccaa,ccaa_id in geo_ids.items():
		print(ccaa)
	
		# locate ccaa in dataset
		iccaa = np.where(ds.ccaa.values==ccaa)[0][0]
	
		# loop on year
		grps = pylib.SplitArray(args['dtime'],n_per_group=366)
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
	ds.ydemand[dict()] = ds.ddemand.resample(dtime='1YS').sum().values

	# save
	if os.path.isfile(fn_save):
		os.remove(fn_save)
	ds.to_netcdf(fn_save)
	
	return ds



def GetContribution(ds):
	# load libraries
	import xarray as xr
	import numpy as np
	
	# create empty dataset
	res = (xr.Dataset({
		'ycontribution': (['ytime','gtype','ccaa'],np.full([ds.dims['ytime'],ds.dims['gtype'],ds.dims['ccaa']],np.nan)),
		'mcontribution': (['mtime','gtype','ccaa'],np.full([ds.dims['mtime'],ds.dims['gtype'],ds.dims['ccaa']],np.nan)),
		'dcontribution': (['dtime','gtype','ccaa'],np.full([ds.dims['dtime'],ds.dims['gtype'],ds.dims['ccaa']],np.nan))}))

	# compute relative contributions
	for igtype,gtype in enumerate(ds.gtype.values):
		for ts in ['y','m','d']:
			total_peninsula = ds['{}generation'.format(ts)].sel(gtype=gtype,ccaa='Peninsula').values
			if np.isfinite(total_peninsula).any():
				print([gtype,ts])
				for iccaa,ccaa in enumerate(ds.ccaa.values):
					total_ccaa = ds['{}generation'.format(ts)].sel(gtype=gtype,ccaa=ccaa).values
					res['{}contribution'.format(ts)][dict(gtype=igtype,ccaa=iccaa)] = total_ccaa/total_peninsula*100
	return res
