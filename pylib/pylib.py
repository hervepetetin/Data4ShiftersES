

def SplitArray(x,n_per_group=None,n_groups=None):
    """ Split array in various groups
    """
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



def GetType(x):
    """ Return the type of the variable in string format
    """
    return(str(type(x)).split("'")[1])

def PrepareTimeArrays(time1, time2, time_scales=['h','d','m','y']):
    """ Prepare time arrays 

    Parameters 
    ----------       
    time1 : str
        Starting time in format '%Y%m%d%H'.

    time2 : str
        Starting time in format '%Y%m%d%H'.

    time_scales : list of str
        List of time scales to be prepared : "h" for hourly time array, 
        "d" for daily time array, "m" for monthly time array (taken as the first 
        day of the month), "y" for yearly time array (taken as the first day of the year)

    Outputs
    -------

    output : dict
        Dictionnary containing (if the corresponding time scale are requested):
             - time1 : str used as input
             - time2 : str used as input
             - date1 : date corresponding to time1
             - date2 : date corresponding to time2
             - htime : date array at hourly scale
             - nhtime : int with total number of hours
             - dtime : date array at daily scale
             - ndtime : int with total number of days
             - mtime : date array at monthly scale
             - nmtime :int with total number of months
             - ytime : date array at yearly scale
             - nytime : int with total number of years
             - years : numpy arrays with years as integers

    Examples
    --------
    >>> from pyeslib import PrepareTimeArrays
    >>> time1,time2 = '2019010300','2019020523'
    >>> res = PrepareTimeArrays(time1, time2, time_scales=['h','d'])
    >>> print(res.keys())
    dict_keys(['time1', 'time2', 'date1', 'date2', 'htime', 'nhtime', 'dtime', 'ndtime'])
    >>> print(res)
    {'time1': '2019010300', 'time2': '2019020523', 'date1': Timestamp('2019-01-03 00:00:00'), 'date2': Timestamp('2019-02-05 23:00:00'), 'htime': DatetimeIndex(['2019-01-03 00:00:00', '2019-01-03 01:00:00',
               '2019-01-03 02:00:00', '2019-01-03 03:00:00',
               '2019-01-03 04:00:00', '2019-01-03 05:00:00',
               '2019-01-03 06:00:00', '2019-01-03 07:00:00',
               '2019-01-03 08:00:00', '2019-01-03 09:00:00',
               ...
               '2019-02-05 14:00:00', '2019-02-05 15:00:00',
               '2019-02-05 16:00:00', '2019-02-05 17:00:00',
               '2019-02-05 18:00:00', '2019-02-05 19:00:00',
               '2019-02-05 20:00:00', '2019-02-05 21:00:00',
               '2019-02-05 22:00:00', '2019-02-05 23:00:00'],
              dtype='datetime64[ns]', length=816, freq='H'), 'nhtime': 816, 'dtime': DatetimeIndex(['2019-01-03', '2019-01-04', '2019-01-05', '2019-01-06',
               '2019-01-07', '2019-01-08', '2019-01-09', '2019-01-10',
               '2019-01-11', '2019-01-12', '2019-01-13', '2019-01-14',
               '2019-01-15', '2019-01-16', '2019-01-17', '2019-01-18',
               '2019-01-19', '2019-01-20', '2019-01-21', '2019-01-22',
               '2019-01-23', '2019-01-24', '2019-01-25', '2019-01-26',
               '2019-01-27', '2019-01-28', '2019-01-29', '2019-01-30',
               '2019-01-31', '2019-02-01', '2019-02-02', '2019-02-03',
               '2019-02-04', '2019-02-05'],
              dtype='datetime64[ns]', freq='D'), 'ndtime': 34}
    """
    # Load libraries
    import datetime
    import pandas as pd
    import numpy as np

    # Check type of inputs
    assert GetType(time1)=='str','time1 should be a string'
    assert GetType(time2)=='str','time2 should be a string'
    assert GetType(time_scales)=='list','time_scales should be a list'
    assert GetType(time_scales[0])=='str','time_scales components should be strings'
    
    # Convert strings into times
    date1 = pd.to_datetime(datetime.datetime.strptime(time1, '%Y%m%d%H')) # (starting time)
    date2 = pd.to_datetime(datetime.datetime.strptime(time2, '%Y%m%d%H')) # (ending time, included)

    # Define first day of the month
    date1_first_day_of_month = pd.to_datetime(datetime.datetime.strptime(time1[0:6]+'01'+time1[8:10], '%Y%m%d%H')) 

    # Define the initial output dictionnary
    output = {'time1' : time1,
              'time2' : time2,
              'date1' : date1,
              'date2' : date2}

    # Add time arrays at hourly scale
    if 'h' in time_scales:
        output['htime'] = pd.date_range(date1, date2, freq='H')       
        output['nhtime'] = len(output['htime'])

    # Add time arrays at daily scale
    if 'd' in time_scales:
        output['dtime'] = pd.date_range(date1, date2, freq='D')         
        output['ndtime'] = len(output['dtime'])

    # Add time arrays at monthly scale (taken as first day of the month)
    if 'm' in time_scales:   
        output['mtime'] = pd.date_range(date1_first_day_of_month, date2, freq='MS') 
        output['nmtime'] = len(output['mtime'])

    # Add time arrays at yearly scale (taken as first day of the year)
    if 'y' in time_scales:
        output['ytime'] = pd.date_range(date1_first_day_of_month, date2, freq='AS') 
        output['nytime'] = len(output['ytime'])
        output['years'] = np.array([i.year for i in output['ytime']])

    return(output)

def SeparateOnSeveralLines(sentence,nmin=None,nmax=None,sep=' '):
	if not nmin is None:
		words = sentence.split(sep)
		nwords = len(words)
		result = ''
		for iword,word in enumerate(words):
			if iword < nwords-1:
				result = '{}{}\n'.format(result,word) if len(word) > nmin else '{}{} '.format(result,word)
			else:
				result = '{}{} '.format(result,word)
	
	if not nmax is None:
		words = sentence.split(sep)
		nwords = len(words)
		result = ''
		for iword,word in enumerate(words):
			if len('{}{} '.format(result.split('\n')[-1],word)) < nmax:
				result = '{}{} '.format(result,word)
			else:
				result = '{}\n{} '.format(result,word)
	return result

