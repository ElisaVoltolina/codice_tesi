from darpPenalityStart import*
from penality_weights import*
from readREAL import extract_darp_data
from valid_inequalities import*
from euristica_no_scart import*

json_file_path= "router_bus_main\DATI\input_5a.json"

darp_data= extract_darp_data(json_file_path)

#variabili input euristica
n=darp_data['n']
serv=darp_data['s']
t_matrix=darp_data['t']
Q_max= darp_data['Q']
e=darp_data['e']
l=darp_data['l']
s=darp_data['s']
PHOME=darp_data['PHOME']
P=darp_data['P']
q=darp_data['q'] 
HOSP=['HOSP']
D=darp_data['D']
T=darp_data['T']


#definisco quale strategia di penalità utilizzo
#penalty_weights=create_penalty_weights_pair_difficulty(P, PHOME, n, t, e, l, s, min_penalty=3000, max_penalty=15000)
'''se commento la riga precedente viene usato il valore di defoult di penalità uguale per tutti i nodi= maggiorn numero possibile di richieste eseguite)'''

#euristic_route, _ , _ =heuristic(n,PHOME, HOSP, D, l, e, serv, t_matrix, T, P, q, Q_max, alpha=1.0, beta=1.0,L=5, pazienti_ordinati= None)
#proviamo a dare il risulatato della multi run con limite un minuto
euristic_route,_,_,_= heuristic_multirun(n, PHOME, HOSP, D, l, e, serv, t_matrix,T, P, q, Q_max, time_limit=60)
solution= solve_darp(**darp_data, euristic_solution= euristic_route )    #con euristic_solution= None non ho nessun mip_start

