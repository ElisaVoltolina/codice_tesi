from darp import* #proviamo prima quello senza penalità e senza la possibilità di esclusieni per vedere come si comporta
from readREAL import extract_darp_data


json_file_path= "router_bus_main\dati_conv\input_modello_5b.json"

darp_data= extract_darp_data(json_file_path)


solution= solve_darp(**darp_data)



"""n=10
P= darp_data['P']
e=darp_data['e']
l=darp_data['l']

for i in P:
    a=l[i]-e[i]
    a2=l[i+n] - e[i+n]
    print(f"l'ampiezza della time window del nodi pickup {i} è=", a)
    print(f"l'ampiezza della time window del nodi delivery {i+n} è=", a2)


    a2=e[i+n]-l[i]
    print("le distanze delle time window sono=", a2)""" 

