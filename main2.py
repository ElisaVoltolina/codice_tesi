from darpPenality import*
from utils import save_solution, find_original_ids_from_new_indices

#from readistance import*
from readistance import*


# Parsifica istanza completa (nodi + archi)
nodes_data, travel_times, route_time, capacity = parse_pdptw_instance("new_20/ipdptw-n100-ber0.txt")

#richieste da escludere (DEVE CONTENERE SEMPRE LA NUMERAZIONE ORIGINALE, non i nuovi incidi dopo aver fatto già delle escuksioni)
#exclude_requests = [] 


#Trovo gl ID originali delle nuove coppie ptoblematiche
#original_ids_1 = find_original_ids_from_new_indices("ipdptw-n20-ber.txt", 3, 9, exclude_requests)
#original_ids_2 = find_original_ids_from_new_indices("ipdptw-n20-ber.txt", 6, 12, exclude_requests)

#Aggiungo questi nodi tra quelli da escludere usando i loro ID originali
#exclude_requests.extend([original_ids_1, original_ids_2])


# Converte nel formato DARP (senza calcoli distanze)
darp_data = create_darp_data(nodes_data, travel_times, route_time, capacity)
#darp_data = create_darp_data(nodes_data, travel_times, route_time, capacity)

# Risolvi con il tuo modello
solution= solve_darp(**darp_data)


#variabili necessarie per il plot (plot2.py)
#x_solution = {k: v for k, v in solution[0].items() if v is not None and v > 0.5}
#V=darp_data['V']
#P=darp_data['P']
#D=darp_data['D']