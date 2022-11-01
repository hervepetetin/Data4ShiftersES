# Data4ShiftersES

Python scripts for preprocessing and plotting data of interest for the Shifters Spain.

One directory per type of data used:
- **electricity** : electricity open-data from Red Electrica Española (REE)
(https://www.ree.es/es/apidatos). Currently, the script handles electricity generation and demand data.
- **greenhouse gases emissions** : greenhouse gases emissions of Spain, from MITECO
(Tabla resumen de emisiones. Ed. 2022-Inventario Nacional;
https://www.miteco.gob.es/es/calidad-y-evaluacion-ambiental/temas/sistema-espanol-de-inventario-sei-/Inventario-GEI.aspx)
and World Bank (https://data.worldbank.org/country/spain?view=chart).

** Organisation of the directories **

The `data` directory includes the netcdf files where are stored the preprocessed data.
The `figures` directory includes the plot PDFs generated.
The `pylib` directory includes some generic functions useful for the different analysis
(and is used as an additional python library). The other directories correspond to the analysis directory, currently one per data source.
They include the python scripts for preprocessing and plotting the data. The main python script          
to be executed is always named as `top_<>.py`. Another script named `tools_<>.py` includes
some additional functions.

** Structure of python top scripts **

All python top script are structure as follows : (1) user-defined input parameters
(paths, time period to consider, plots requested), (2) library load, (3) preprocessing data,
(4) plotting data. All the preprocessed data is kept into a single xarray dataset (and saved
into a single netcdf file) (xarray dataset are a multi-dimensional extension of pandas dataframes).
Through the `recompute` parameter, the user can choose to re-compute all the preprocessing, or the
read the existing netcdf file.




