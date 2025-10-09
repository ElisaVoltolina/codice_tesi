from utilis2 import*
from readREAL import extract_darp_data
import random

#euristica con reinserimento dei pazienti
def heuristic(n,PHOME, HOSP, D, l, e, serv, t_matrix, T, P, q, Q_max, alpha=1.0, beta=1.0,L=5, pazienti_ordinati= None):
    """
    Algoritmo euristico per la schedulazione di pazienti con reinserimento degli scartati.
    
    Args:
        n: numero totale di pazienti
        L: limite massimo di sequenze da mantenere ad ogni iterazione
        pazienti: lista dei pazienti da schedulare
    
    Returns:
        tuple: (migliore_sequenza, costo_migliore, pazienti_scartati)
    """
    
    # Inizializzazione
    S = {}  # Dizionario per memorizzare S_i per ogni iterazione
    
    S[0] = [[0, 2*n+1]]   #avevo usato set per non avvere duplicati 
    scart = []  # Lista dei pazienti scartati    **** HO AGGIUNTO 1

    Time={} 
    Time[0] = {tuple([0, 2*n+1]): np.zeros(2)} #innizializzo Time[0]

    #se non specifico niente in input usa ordinamento per flessifilità time windows 
    if pazienti_ordinati is None:
        pazienti_ordinati= order_patients_by_flexibility(PHOME,n, e, l, t_matrix)

    
    """#  DEBUG: testa il primo paziente per vedere perchè non viene inserito
    if len(pazienti_ordinati) > 0:
        primo_paziente = pazienti_ordinati[0]
        debug_first_patient(primo_paziente, n, serv, t_matrix, T, e, l, P, D, q, Q_max)"""



    for iteration, paziente_id in enumerate(pazienti_ordinati, start=1): 

        print(f"\n--- Iterazione {iteration}: Inserimento paziente {paziente_id} ---")
        
        S[iteration] = []  #insieme delle feasible route definte fine allinserimento del paziente
        Time[iteration] = {} #creo un dizionario per ogni iserimento il qiale contiene la sequenza dei tempi per ogni sequenza che viene selezionata
       
        # Inserimento del paziente i
        for s in S[iteration-1]: 
            s_middle=s[1:-1] #sequenza senza i depositi
            # Prova tutti i possibili inserimenti del paziente nelle sequenze esistenti
            for h in range( len(s_middle)+1):  #{1,...,m}
                for k in range(h + 1, len(s_middle) + 2):  #{h+1,..., m+2}
                    for v in range(k + 1, len(s_middle) + 3):
                        for w in range(v + 1, len(s_middle) + 4):
                            r = Insert(s, n, paziente_id, h, k, v, w)
                            if r not in S[iteration]:  #controllo che non esista già la stessa sequenza
                                ok, t= feasible(r, serv, t_matrix,T, n, e , l, P, D, q, Q_max, debug= None)
                                if ok:
                                    S[iteration].append(r)
                                    Time[iteration][tuple(r)]=t
                                
                                    
        #Controllo se paziente i è inseribile
        if len(S[iteration]) == 0:  
            print(f"Paziente {paziente_id} non inseribile, aggiunto agli scartati")
            scart.append(paziente_id) #lo aggiungo agli scarti
            S[iteration]=copy.deepcopy(S[iteration-1])# Mantieni le sequenze precedenti
            Time[iteration]=copy.deepcopy(Time[iteration-1]) 
        else:
            print(f"Paziente {paziente_id} inserito in {len(S[iteration])} sequenze")
        
        #Tentativo reinserimento pazienti scartati (solo se S_i non è vuoto)
        if len(S[iteration]) > 0 and len(scart) > 0:  #provo ad aggiungere i pazienti che alle iterazioni precedenti avevo scartato
            
            pazienti_da_rimuovere = []
            for p in scart:
                temp_sequences = []
                temp_time={}
                # Prova a inserire il paziente scartato in tutte le sequenze attuali
                for s in S[iteration]:
                    s_inner=s[1:-1]
                    for h in range(len(s_inner)+2):  #{0,...,m+1}
                        for k in range(h + 1, len(s_inner) + 3):  #{h+1,..., m+2}
                            for v in range(k + 1, len(s_inner) + 4):
                                for w in range(v + 1, len(s_inner) + 5):
                                    r = Insert(s, n, p, h, k, v, w)  
                                    # Evita duplicati
                                    if r not in temp_sequences and r not in S[iteration]:
                                        ok, t = feasible(r, serv, t_matrix, T, n, e, l, P, D, q, Q_max, debug=None)
                                        
                                        if ok:
                                            temp_sequences.append(r)    #uso temp_seq per non aggiornare S[i] prima di aver finito il ciclo for
                                            temp_time[tuple(r)]=t
                                        
                
                # Se il paziente è stato reinserito con successo
                if len(temp_sequences) > 0:
                    print(f"Paziente scartato {p} reinserito in {len(temp_sequences)} sequenze")
                    S[iteration].extend(temp_sequences)  #append aggiunge solo un elemnto non lo posso usare per una lisat che contiene più elemnti che voglio aggiungere
                    Time[iteration].update(temp_time)
                    pazienti_da_rimuovere.append(p)
                else:
                    print("Non è stato possibile inserire nessun paziente scartato")
            
            # Rimuovi i pazienti reinseriti dalla lista degli scartati
            for p in pazienti_da_rimuovere:
                scart.remove(p)      


        #Selezione delle migliori L sequenze se necessario
        if len(S[iteration]) > L:
            print(f"Potatura: da {len(S[iteration])} a {L} sequenze")
            S[iteration] = select_best(S[iteration], L, lambda s: f_eur2(n,s,Time,iteration,t_matrix, HOSP, D, l, e, alpha=1.0, beta=1.0))     #sorted passerà solo s, e Time rimane "fissato" nella lambda.
        
        print(f"Fine iterazione {iteration}: {len(S[iteration])} sequenze, {len(scart)} scartati\n")
    
    #selezione della sequenza con il miglior costo
    print("Fase finale: calcolo dei costi...")
    migliore_sequenza = None
    miglior_costo = float('inf')

    ultima_iterazione = len(pazienti_ordinati)
    
    
    for s in S[iteration]:  #nooooo
        """#DEBAG
        key = tuple(s)
        if key not in Time[ultima_iterazione]:
            print(f"Chiave mancante: {key}")
            print(f"Numero di chiavi in Time[{ultima_iterazione}]:", len(Time[ultima_iterazione]))
            print("Esempio chiavi presenti:", list(Time[ultima_iterazione2].keys())[:5])
            raise KeyError(f"Sequenza {key} non trovata in Time[{ultima_iterazione}]")
        #FINE DEBAG"""


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






# Multi-start con ordini diversi
def heuristic_multistart(n, PHOME, HOSP, D, l, e, serv, t_matrix,T, P, q, Q_max, num_runs=5):
    """Prova l'euristica con ordini diversi e tieni la migliore"""
    best_solution = None
    best_cost = float('inf')
    best_scart= None
    
    for run in range(num_runs):
        print(f"\n{'='*60}")
        print(f"RUN {run+1}/{num_runs} con seed {run}")
        print(f"{'='*60}")
        
        """# Ordine diverso ad ogni run
        if run == 0:
            # Prima run: usa ordinamento per fessibilità
            #order_func = order_patients_by_flexibility
            pazienti = order_patients_by_flexibility(PHOME,n, e, l, t_matrix)
        elif run == 1:
            # Seconda: ordine opposto
            pazienti = order_patients_by_flexibility(PHOME,n, e, l, t_matrix)
            pazienti = list(reversed(pazienti))
        else:
            # Altre: casuale
            pazienti = order_randomly(PHOME, seed=run)"""


        #ordinamneto casuale per ogni run
        pazienti = order_randomly(PHOME, seed=run)
        # Esegui euristica
        solution, cost, scart = heuristic(n, PHOME, HOSP, D, l, e, serv,t_matrix,T, P, q, Q_max,
                                          pazienti_ordinati=pazienti)
        
        if cost < best_cost:
            best_solution = solution
            best_scart=scart
            best_cost = cost
            print(f" Nuovo best: {cost:.2f} ({len(scart)} scartati)")
    
    return best_solution, best_cost, best_scart










if __name__=='__main__':
    #file
    json_file_path= "router_bus_main/DATI/input_8.json"
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
    
  
    #migliore_sequenza, miglior_costo, scart=heuristic(n,PHOME, HOSP, D, l, e, alpha=1.0, beta=1.0, pazienti_ordinati=None)

#heriusta con 5 run 
    best_Solution, best_cost=heuristic_multistart(n, PHOME, HOSP, D, l, e, serv, t_matrix,T, P, q, Q_max, num_runs=5)
    