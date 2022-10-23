
def ScrapINE(variable,ytime):
	# define url
	if variable=='Volumen de agua por tecnica de riego':
		# https://www.ine.es/dyngs/INEbase/es/operacion.htm?c=Estadistica_C&cid=1254736176839&menu=ultiDatos&idp=1254735976602
		url = 'https://www.ine.es/consul/serie.do?d=true&s=DCEF13'
		
	# create object page
	page = requests.get(url)

	# obtain page's information
	soup = BeautifulSoup(page.text,  "html.parser")

	# get values
	values = []
	for i in soup.find_all('td'):
		if '.' in i.text:
			values.append(float(i.text.replace('\t','').replace('\r','').replace('\n','')))

	# get years
	values_years = []
	for i in soup.find_all('th'):
		if i.text[-4:].isdigit():
			values_years.append(int(i.text[-4:]))

	# find values for required years
	result = np.full([len(ytime)],np.nan)
	for iyr,yr in enumerate(ytime):
		w = np.where(np.array(values_years)==yr.year)[0]
		if len(w)!=0:
			result[iyr] = np.array(values)[w[0]]

	return result

def GetSpainGHGEmissionsExtended(variable,ytime):
	'''
	Get Spain GHG emissions (per year)
	'''
	if variable=='GHG': 
		variables_list = ['CO2','CH4','HFC','N2O','PFC','SF6']
	else:
		variables_list = [variable]
	
	fn = '../data/raw/carbonbudget/ipcc_sectors.csv'
	ipcc_sectors = pd.read_csv(fn, sep=';', encoding="ISO-8859-1")
	fn = '../data/raw/carbonbudget/emissions_per_ipcc_sector.csv'
	emissions = pd.read_csv(fn, sep=';')
	columns = emissions.columns
	
	sectors = ipcc_sectors['DESCRIPTION'].values
	result_per_sector = np.full([len(variables_list),len(sectors),len(ytime)],np.nan)
	
	for irow in range(emissions.shape[0]):
		xsector = emissions.iloc[irow]['IPCC_SECTOR']
		xdivision = str(emissions.iloc[irow]['IPCC_DIVISION'])
		xclass = emissions.iloc[irow]['IPCC_CLASS']
		xsubclass = str(emissions.iloc[irow]['IPCC_SUBCLASS'])
		if xsubclass!='nan' and str(xclass)!='nan':
			subtab = emissions[(emissions['IPCC_SECTOR']==xsector) & (emissions['IPCC_DIVISION']==xdivision) & (emissions['IPCC_CLASS']==xclass) & (emissions['IPCC_SUBCLASS']==xsubclass)]
			sec = ipcc_sectors[(ipcc_sectors['IPCC_SECTOR']==xsector) & (ipcc_sectors['IPCC_DIVISION']==xdivision) & (ipcc_sectors['IPCC_CLASS']==xclass) & (ipcc_sectors['IPCC_SUBCLASS']==xsubclass)]['DESCRIPTION'].iloc[0]
		elif xsubclass=='nan' and str(xclass)!='nan':
			subtab = emissions[(emissions['IPCC_SECTOR']==xsector) & (emissions['IPCC_DIVISION']==xdivision) & (emissions['IPCC_CLASS']==xclass)]
			sec = ipcc_sectors[(ipcc_sectors['IPCC_SECTOR']==xsector) & (ipcc_sectors['IPCC_DIVISION']==xdivision) & (ipcc_sectors['IPCC_CLASS']==xclass)]['DESCRIPTION'].iloc[0]
		elif xsubclass=='nan' and str(xclass)=='nan':
			subtab = emissions[(emissions['IPCC_SECTOR']==xsector) & (emissions['IPCC_DIVISION']==xdivision)]
			try:
				sec = ipcc_sectors[(ipcc_sectors['IPCC_SECTOR']==xsector) & (ipcc_sectors['IPCC_DIVISION']==xdivision)]['DESCRIPTION'].iloc[0]
			except:
				continue	
		isec = np.where(sectors==sec)[0][0]
		ok = False
		for ivar,var in enumerate(variables_list):
			unit_conversion = {'CO2':1,'CH4':25,'N2O':298,'PFC':7390,'HFC':12000,'SF6':22200}[var]
			for iyr,yr in enumerate(ytime):
			
				contaminante = np.array([i[:3] for i in subtab['CONTAMINANTE'].values])
				wvar = np.where(contaminante==var)[0]
				if len(wvar)!=0:
					tmp = subtab.iloc[wvar[0]]
					wyr = np.where(emissions.columns=='CO2EQ{}'.format(yr.year))[0]
					if len(wyr)!=0:
						result_per_sector[ivar,isec,iyr] = float(tmp[wyr[0]].replace('.','').replace(',','.'))
						ok = True

		if ok==False:
			print(irow)
			print(emissions.iloc[irow])
			zz
		
	wsectors = np.where(np.isfinite(np.nansum(result_per_sector,axis=(0,2))))[0]
	sectors = sectors[wsectors]
	result_per_sector = result_per_sector[:,wsectors,:]
	
	return result_per_sector,sectors




def GetSpainGHGEmissions(variable,ytime):
	'''
	Get Spain GHG emissions (per year)
	'''
	if variable=='GHG': 
		variables_list = ['CO2','CH4','HFC','N2O','PFC','SF6']
	else:
		variables_list = [variable]
	
	# read data
	url = 'https://www.ine.es/jaxi/files/_px/es/csv_bdsc/t26/p084/base_2010/serie/l0/01001.csv_bdsc'
	tab = pd.read_csv(url,sep=';',decimal=',',thousands='.')
	
	# correct reading of values and years
	values = np.full([tab.shape[0]],np.nan)
	for ival,val in enumerate(tab['Total'].values):
		try:
			values[ival] = float(val.replace('.','').replace(',','.'))
		except:
			values[ival] = np.nan
	tab['Total'] = values
	tab['periodo'] = [int(i[:4]) for i in tab['periodo']]
		
	# get annual emissions
	sectors = np.array([i for i in np.unique(tab['Ramas de actividad (CNAE 2009)'].values) if not i in ['TOTAL SUSTANCIA CONTAMINANTE', 'Total ramas de actividad']],dtype='object')
	result_per_sector = np.full([len(variables_list),len(sectors),len(ytime)],np.nan)
	result = np.full([len(variables_list),len(ytime)],np.nan)
	
	for isec,sec in enumerate(np.append(sectors,'TOTAL SUSTANCIA CONTAMINANTE')):
		subtab = tab[tab['Ramas de actividad (CNAE 2009)']==sec]
		for iyr,yr in enumerate(ytime):
			for ivar,var in enumerate(variables_list):
				variable_column = {
					'CH4':'CH4 - Metano (toneladas)', 
					'CO':'CO - Monóxido de carbono (toneladas)',
					'CO2':'CO2 - Dióxido de carbono (miles de toneladas)',
					'COVNM':'COVNM - Compuestos orgánicos volátiles no metánicos (toneladas)',
					'HFC':'HFC - Hidrofluorocarbonos o compuestos hidrogenofluorcarbonados (miles de toneladas de CO2 equivalente)',
					'N2O':'N2O - Óxido nitroso (toneladas)', 
					'NH3':'NH3 - Amoniaco (toneladas)',
					'NOx':'NOx - Óxidos de nitrógeno (toneladas de NO2 equivalentes)',
					'PFC':'PFC - Perfluorocarbonos o compuestos polifluorcarbonados (miles de toneladas de CO2 equivalente)',
					'PM10':'PM10 - Partículas de diámetro menor o igual a 10 µm (toneladas)',
					'PM2.5':'PM2.5 - Partículas de diámetro menor o igual a 2,5 µm (toneladas)',
					'SF6':'SF6 - Hexafluoruro de azufre (miles de toneladas de CO2 equivalente)',
					'SOx':'SOx - Óxidos de azufre (toneladas de SO2 equivalentes)'}[var]


				tmp = subtab[(subtab['Sustancias contaminantes']==variable_column) & (subtab['periodo']==yr.year)]['Total']				
				if var=='CH4': tmp = tmp/1000*25 #(tCH4 => ktCO2eq)
				if var=='N2O': tmp = tmp/1000*298 #(tN2O => ktCO2eq)
				if len(tmp)!=0:
					if sec=='TOTAL SUSTANCIA CONTAMINANTE':
						result[ivar,iyr] = tmp
					else:
						result_per_sector[ivar,isec,iyr] = tmp
	
	if variable=='GHG': 
		result = np.sum(result,axis=0)
		result_per_sector_all = np.sum(result_per_sector,axis=0)
	
	return result,result_per_sector,result_per_sector_all,sectors,tab



def GetDataFromWorldBank(variable,ytime):
	# find code
	code = {'co2_emissions_percapita_wb': 'EN.ATM.CO2E.PC',
					'population'   							: 'SP.POP.TOTL'    }[variable]
					
					
	# read data
	url = 'https://api.worldbank.org/v2/es/indicator/{}?downloadformat=csv'.format(code)
	response = requests.get(url, stream=True, verify=False)
	with ZipFile(io.BytesIO(response.content)) as myzip:
		fn = [i for i in myzip.namelist() if i.startswith('API')][0]
		with myzip.open(fn) as myfile:
			tab = pd.read_csv(myfile,skiprows=4)
				
	# get data
	result = np.full([len(ytime)],np.nan)
	for iyr,yr in enumerate(args['ytime']):
		yyyy = str(yr.year)
		if yyyy in tab.columns:
			result[iyr] = tab[tab['Country Code']=='ESP'][yyyy].iloc[0]
			
	return result
