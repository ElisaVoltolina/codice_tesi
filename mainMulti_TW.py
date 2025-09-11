from darpMulti_TW import* 
from readREAL import extract_darp_data


json_file_path= "router_bus_main\dati_conv\input_modello_8b.json"

darp_data= extract_darp_data(json_file_path)


solution= solve_darp(**darp_data)
