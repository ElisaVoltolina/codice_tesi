from utilis2 import*
from readREAL import extract_darp_data
import random
import time


def heuristic(n,PHOME, HOSP, D, l, e, serv, t_matrix, T, P, q, Q_max, alpha=1.0, beta=1.0,L=5, pazienti_ordinati= None):
    """
    Euristica per la schedulazione di pazienti senza reinserimento degli scartati.

    n: numero totale di pazienti; l: fine delle rispettive time windows; e: inizio time window
    L: limite massimo di sequenze da mantenere ad ogni iterazione
    pazienti: lista dei pazienti da schedulare
    T: tempo max per eseguire una richiesta; q: carico per ogni nodo, Q_max: capienza massima veicolo
    """
    
    # Inizializzazione
    S = {}  # Dizionario per memorizzare S_i per ogni iterazione
    S[0] = [[0, 2*n+1]]    
    scart = []  # Lista dei pazienti scartati    
    Time={} 
    Time[0] = {tuple([0, 2*n+1]): np.zeros(2)} 

    #se non specifico niente in input usa ordinamento per flessifilità time windows 
    if pazienti_ordinati is None:
        pazienti_ordinati= order_patients_by_flexibility(PHOME,n, e, l, t_matrix)


    for iteration, paziente_id in enumerate(pazienti_ordinati, start=1): 

        print(f"\n--- Iterazione {iteration}: Inserimento paziente {paziente_id} ---")
        
        new_sequences = {}  # key=tuple(route), value=(route, times)
        
        num_prev_sequences = len(S[iteration-1])
        processed = 0
        
        for s in S[iteration-1]:  
            
            s_middle = s[1:-1]  #sequenza senza depositi
            m = len(s_middle)
            
            #Pre-calcolo i limiti per evitare iterazioni inutili
            max_h = m + 1
            
            # provo tutte le posizioni 
            for h in range(max_h):
                for k in range(h + 1, m + 2):
                    for v in range(k + 1, m + 3):
                        for w in range(v + 1, m + 4):
                            r = Insert(s, n, paziente_id, h, k, v, w)
                            r_tuple = tuple(r)
                            
                            #Controllo duplicati
                            if r_tuple not in new_sequences:
                                # feasible con early exit
                                ok, t = feasible_fast(r, serv, t_matrix, T, n, e, l, 
                                                     P, D, q, Q_max)
                                if ok:
                                    new_sequences[r_tuple] = (r, t)
        
        # Converti dict a liste
        S[iteration] = [route for route, _ in new_sequences.values()]
        Time[iteration] = {key: times for key, (_, times) in new_sequences.items()}
        
                                
                                    
        #Controllo se paziente i è inseribile
        if len(S[iteration]) == 0:  
            print(f"Paziente {paziente_id} non inseribile, aggiunto agli scartati")
            scart.append(paziente_id) #lo aggiungo agli scarti
            S[iteration]=copy.deepcopy(S[iteration-1])# Mantieni le sequenze precedenti
            Time[iteration]=copy.deepcopy(Time[iteration-1]) 
        else:
            print(f"Paziente {paziente_id} inserito in {len(S[iteration])} sequenze")
        
        

        #Selezione delle migliori L sequenze se necessario
        if len(S[iteration]) > L:
            print(f"Potatura: da {len(S[iteration])} a {L} sequenze")
            # Calcolo costi una volta sola
            costs = [(s, f_eur2(n, s, Time, iteration, t_matrix, HOSP, D, l, e, alpha, beta)) 
                     for s in S[iteration]]
            costs.sort(key=lambda x: x[1])
            S[iteration] = [s for s, _ in costs[:L]]
            # Pulisco Time 
            Time[iteration] = {tuple(s): Time[iteration][tuple(s)] for s in S[iteration]}
        
        print(f"Fine iterazione {iteration}: {len(S[iteration])} sequenze, {len(scart)} scartati\n")
    
    #selezione della sequenza con il miglior costo
    print("Fase finale: calcolo dei costi...")
    migliore_sequenza = None
    miglior_costo = float('inf')
    ultima_iterazione = len(pazienti_ordinati)
    
    
    for s in S[ultima_iterazione]:
        
        temp=Time[ultima_iterazione][tuple(s)]
        costo = C(n,s, temp,t_matrix, HOSP, D, l, e, scart, alpha=1.0, beta=1.0)
        if costo < miglior_costo:
            miglior_costo = costo
            migliore_sequenza = s
    
    print(f"Algoritmo completato:")
    print(f"- Pazienti scartati: {scart}")
    print(f"- Miglior costo: {miglior_costo}")
    print(f"- Migliore sequenza: {migliore_sequenza}")
    
    return migliore_sequenza, miglior_costo, scart






def heuristic_multirun(n, PHOME, HOSP, D, l, e, serv, t_matrix,T, P, q, Q_max, time_limit=60):
    """esegue euristica senza reinserimento nel time limit 
        con ordinamento casuale per ogni run"""
    best_solution = None
    best_cost = float('inf')
    best_scart= None
    
    start_time = time.time()
    run=0
    t=0
    while t < time_limit:
        if run == 0:
            # Prima run: ordinamento deterministico per flessibilità
            pazienti = order_patients_by_flexibility(PHOME, n, e, l, t_matrix)
        else:
            #ordinamneto casuale per tutte le altre run
            pazienti = order_randomly(PHOME, seed=run)
        # Esegui euristica
        solution, cost, scart = heuristic(n,PHOME, HOSP, D, l, e, serv, t_matrix, T, P, q, Q_max, alpha=1.0, beta=1.0,L=5, pazienti_ordinati= pazienti)
        
        if cost < best_cost:
            best_solution = solution
            best_scart=scart
            best_cost = cost
            print(f" Nuovo best: {cost:.2f} ({len(scart)} scartati)")
        run +=1
        t= time.time()-start_time 
    
    return best_solution, best_cost, best_scart, run


def heuristic_multirun1(n, PHOME,HOSP, D, l, e, serv, t_matrix, T, P, q, Q_max, time_limit=60):
    """esegue euristica senza reinserimento per un minuto con ordinamneti diversificati """
    best_solution = None
    best_cost = float('inf')
    best_scart = None
   
    start_time = time.time()
    run = 0
    t = 0
    
    while t < time_limit:
        #alterno tra 3 strategie
        if run == 0:
            # Prima run: ordinamento deterministico per flessibilità
            pazienti = order_patients_by_flexibility(PHOME, n, e, l, t_matrix)
            #print(f"Run {run}: ordinamento FLESSIBILITÀ")
        elif run % 2 == 1:
            # Run dispari: ordinamento casuale pesato
            pazienti = order_biased_random(PHOME, n, e, l, t_matrix, seed=run)
            #print(f"Run {run}: ordinamento BIASED RANDOM")
        else:
            # Run pari: completamente casuale
            pazienti = order_randomly(PHOME, seed=run)
            #print(f"Run {run}: ordinamento RANDOM")
        
       
        solution, cost, scart = heuristic(n, PHOME, HOSP, D, l, e, serv, t_matrix, T, P, q, Q_max, alpha=1.0, beta=1.0, L=5, pazienti_ordinati=pazienti)
       
        if cost < best_cost:
            best_solution = solution
            best_scart = scart
            best_cost = cost
            print(f" Nuovo best: {cost:.2f} ({len(scart)} scartati)")
       
        run += 1
        t = time.time() - start_time
   
    return best_solution, best_cost, best_scart, run


if __name__=='__main__':
    #file
    json_file_path= "router_bus_main/DATI/input_modello_8b.json"
    # estrazione dati
    data_darp= extract_darp_data(json_file_path)
    t_matrix= data_darp['t']
    T= data_darp['T']
    n=data_darp['n']
    e= data_darp['e']
    l=data_darp['l']
    PHOME=data_darp['PHOME']
    HOSP= data_darp['HOSP']
    P=data_darp['P']
    D=data_darp['D']
    q=data_darp['q']
    Q_max=data_darp['Q']
    serv= data_darp['s']
    




    #pazienti=[5, 2, 4, 1, 3]
    #migliore_sequenza, miglior_costo, scart=heuristic(n,PHOME, HOSP, D, l, e, serv, t_matrix, T, P, q, Q_max, alpha=1.0, beta=1.0,L=5, pazienti_ordinati= pazienti)

    #heriusta con time limit
    #best_solution, best_cost, best_scart, num_run=heuristic_multirun(n, PHOME, HOSP, D, l, e, serv, t_matrix,T, P, q, Q_max, time_limit=60)
    


    #prova beam search
    best_order=beam_search_ordering_balanced(n, PHOME, HOSP, D, l, e, serv, t_matrix, T, P, q, Q_max, beam_width=2, alpha=1.0, beta=1.0)
    print("il miglior ordinamento trovato è:", best_order)



#nuova euristica

    #best_sol, best_cost, best_scart=iterated_greedy(n, PHOME, HOSP, D, l, e, serv, t_matrix, T, P, q, Q_max, num_iterations=10, alpha=1.0, beta=1.0, L=5)
    #print("miglior soluzione:", best_sol, "\n miglior costo:", best_cost, "\n scarti.", best_scart) 

    