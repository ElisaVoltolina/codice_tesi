from darpPenality import*
from penality_weights import*
from readREAL import extract_darp_data

json_file_path= "router_bus_main\dati_conv\input_modello_10a.json"

darp_data= extract_darp_data(json_file_path)

P=darp_data['P']
t=darp_data['t']
n=darp_data['n']
e=darp_data['e']
l=darp_data['l']
s=darp_data['s']
PHOME=darp_data['PHOME']


#definisco quale strategia di penalità utilizzo
penalty_weights=create_penalty_weights_pair_difficulty(P, PHOME, n, t, e, l, s, min_penalty=3000, max_penalty=15000)
'''se commento la riga precedente viene usato il valore di defoult di penalità uguale per tutti i nodi= maggiorn numero possibile di richieste eseguite)'''


solution= solve_darp(**darp_data)
