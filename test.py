from utilis2 import *
from readREAL import extract_darp_data
import random
from collections import defaultdict

def heuristic_fast(n, PHOME, HOSP, D, l, e, serv, t_matrix, T, P, q, Q_max, 
                   alpha=1.0, beta=1.0, L=5, pazienti_ordinati=None):
    """
    Versione VELOCE che MANTIENE la qualità:
    - Tutti gli inserimenti vengono provati
    - Ma con strutture dati efficienti
    - E controlli intelligenti
    """
    
    S = {}
    S[0] = [[0, 2*n+1]]
    scart = []
    Time = {}
    Time[0] = {tuple([0, 2*n+1]): np.zeros(2)}

    if pazienti_ordinati is None:
        pazienti_ordinati = order_patients_by_flexibility(PHOME, n, e, l, t_matrix)

    for iteration, paziente_id in enumerate(pazienti_ordinati, start=1):
        print(f"\n--- Iterazione {iteration}: Inserimento paziente {paziente_id} ---")
        
        new_sequences = {}  # key=tuple(route), value=(route, times)
        
        num_prev_sequences = len(S[iteration-1])
        processed = 0
        
        for s in S[iteration-1]:  #QUI DA CAPIRE
            processed += 1
            if processed % 50 == 0:
                print(f"  Processate {processed}/{num_prev_sequences} sequenze...")
            
            s_middle = s[1:-1]
            m = len(s_middle)
            
            #Pre-calcolo i limiti per evitare iterazioni inutili
            max_h = m + 1
            
            # Prova TUTTE le posizioni 
            for h in range(max_h):
                for k in range(h + 1, m + 2):
                    for v in range(k + 1, m + 3):
                        for w in range(v + 1, m + 4):
                            r = Insert(s, n, paziente_id, h, k, v, w)
                            r_tuple = tuple(r)
                            
                            #Controllo duplicaticon dict
                            if r_tuple not in new_sequences:
                                # feasible con early exit
                                ok, t = feasible_fast(r, serv, t_matrix, T, n, e, l, 
                                                     P, D, q, Q_max)
                                if ok:
                                    new_sequences[r_tuple] = (r, t)
        
        # Converti dict a liste
        S[iteration] = [route for route, _ in new_sequences.values()]
        Time[iteration] = {key: times for key, (_, times) in new_sequences.items()}
        
        # Gestione paziente non inseribile
        if len(S[iteration]) == 0:
            print(f"Paziente {paziente_id} non inseribile, aggiunto agli scartati")
            scart.append(paziente_id)
            S[iteration] = copy.deepcopy(S[iteration-1])
            Time[iteration] = copy.deepcopy(Time[iteration-1])
        else:
            print(f"Paziente {paziente_id} inserito in {len(S[iteration])} sequenze")
        
        #Reinserimento scartati 
        if len(S[iteration]) > 0 and len(scart) > 0:
            scart_rimossi = reinserisci_scartati_smart(
                S, Time, iteration, scart, n, serv, t_matrix, 
                T, e, l, P, D, q, Q_max
            )
            for p in scart_rimossi:
                scart.remove(p)
        
        # Selezione best L sequenze
        if len(S[iteration]) > L:
            print(f"Potatura: da {len(S[iteration])} a {L} sequenze")
            # Calcola costi una volta sola
            costs = [(s, f_eur2(n, s, Time, iteration, t_matrix, HOSP, D, l, e, alpha, beta)) 
                     for s in S[iteration]]
            costs.sort(key=lambda x: x[1])
            S[iteration] = [s for s, _ in costs[:L]]
            # Pulisci Time 
            Time[iteration] = {tuple(s): Time[iteration][tuple(s)] for s in S[iteration]}
        
        print(f"Fine iterazione {iteration}: {len(S[iteration])} sequenze, {len(scart)} scartati\n")
    
    # Selezione finale
    print("Fase finale: calcolo dei costi...")
    migliore_sequenza = None
    miglior_costo = float('inf')
    ultima_iterazione = len(pazienti_ordinati)
    
    for s in S[ultima_iterazione]:
        temp = Time[ultima_iterazione][tuple(s)]
        costo = C(n, s, temp, t_matrix, HOSP, D, l, e, scart, alpha, beta)
        if costo < miglior_costo:
            miglior_costo = costo
            migliore_sequenza = s
    
    print(f"Algoritmo completato:")
    print(f"- Pazienti scartati: {scart}")
    print(f"- Miglior costo: {miglior_costo}")
    
    return migliore_sequenza, miglior_costo, scart


def feasible_fast(r, serv, t_matrix, T, n, e, l, P, D, q, Q_max):
    """
    Versione ottimizzata di feasible con EARLY EXIT:
    - Ferma appena trova una violazione
    - Controlli più veloci prima (più economici)
    """
    m = len(r)
    
    # CONTROLLO 1: Verifica ordine pickup-delivery, questo potrebbe non servire!!
    pickup_positions = {}
    delivery_positions = {}
    
    for idx, node in enumerate(r):
        if node in P:
            pickup_positions[node] = idx
        elif node in D:
            delivery_positions[node] = idx
            # Controlla che esista il pickup
            pickup_node = node - n
            if pickup_node not in pickup_positions:
                return False, None
            # Controlla ordine
            if pickup_positions[pickup_node] >= idx:
                return False, None
    
    # CONTROLLO 2: Capacità e tempi (insieme, un solo loop)
    t = np.zeros(m)   #t[j] tempod i arrivo al nodo j
    Q = np.zeros(m)   #Q[j] carico dopo aver visitato nodo j
    ld = {}
    
    Q[0] = 0 
    t[0] = 0
    
    for j in range(1, m):
        prev_node = r[j-1]
        curr_node = r[j]
        
        # Calcola tempo arrivo
        t[j] = max(t[j-1], e[prev_node]) + serv[prev_node] + t_matrix[prev_node][curr_node]
        
        # EARLY EXIT: Violazione time window
        if t[j] > l[curr_node]:
            return False, None
        
        # Calcola carico
        Q[j] = Q[j-1] + q[curr_node]
        
        # EARLY EXIT: Violazione capacità
        if Q[j] < 0 or Q[j] > Q_max:
            return False, None
    
    # CONTROLLO 3: Ride time (solo per delivery nodes)
    for p_node in pickup_positions.keys():
        d_node = p_node + n
        
        pickup_pos = pickup_positions[p_node]
        delivery_pos = delivery_positions[d_node]
        
        ld[d_node] = min(l[d_node], max(t[pickup_pos], e[p_node]) + serv[p_node] + T[p_node]) #ultimo orario possibile per il delivery
        
        # EARLY EXIT: Violazione ride time
        if t[delivery_pos] > ld[d_node]:
            return False, None
    
    return True, t


def reinserisci_scartati_smart(S, Time, iteration, scart, n, serv, 
                               t_matrix, T, e, l, P, D, q, Q_max):
    """
    Reinserimento scartati :
    - Prova tutte le posizioni MA solo su sequenze promettenti
    - Ordina scartati per probabilità di successo
    """
    if len(scart) == 0:
        return []
    
    print(f"Tentativo reinserimento {len(scart)} pazienti scartati...")
    
    # Ordina scartati per time window più flessibile
    scart_sorted = sorted(scart, key=lambda p: (l[p] - e[p]), reverse=True)
    
    # Prendi sequenze con più "spazio" (meno cariche)
    seq_with_load = []
    for s in S[iteration]:
        # Calcola carico medio
        total_load = sum(q[node] for node in s)
        seq_with_load.append((s, total_load))
    
    # Ordina per carico crescente (più spazio disponibile)
    seq_with_load.sort(key=lambda x: x[1])
    
    # Prova su metà migliori sequenze (compromesso qualità/velocità)
    num_seq = max(1, len(seq_with_load) // 2)
    promising_sequences = [s for s, _ in seq_with_load[:num_seq]]
    
    pazienti_reinseriti = []
    new_sequences = {}
    
    for p in scart_sorted:
        found = False
        
        for s in promising_sequences:
            if found:  # Trovato almeno una soluzione, passa al prossimo paziente
                break
                
            s_inner = s[1:-1]
            m = len(s_inner)
            
            # Prova TUTTE le posizioni per questo paziente
            for h in range(m + 2):
                for k in range(h + 1, m + 3):
                    for v in range(k + 1, m + 4):
                        for w in range(v + 1, m + 5):
                            r = Insert(s, n, p, h, k, v, w)
                            r_tuple = tuple(r)
                            
                            if r_tuple not in new_sequences and r_tuple not in Time[iteration]:
                                ok, t = feasible_fast(r, serv, t_matrix, T, n, 
                                                     e, l, P, D, q, Q_max)
                                if ok:
                                    new_sequences[r_tuple] = (r, t)
                                    found = True
                                    
        
        if found:
            print(f"  Paziente {p} reinserito")
            pazienti_reinseriti.append(p)
    
    # Aggiungi nuove sequenze
    if new_sequences:
        S[iteration].extend([route for route, _ in new_sequences.values()])
        Time[iteration].update({key: times for key, (_, times) in new_sequences.items()})
    
    return pazienti_reinseriti


def heuristic_multistart_fast(n, PHOME, HOSP, D, l, e, serv, t_matrix, 
                              T, P, q, Q_max, num_runs=5, L=5):
    """Multi-start con versione veloce"""
    best_solution = None
    best_cost = float('inf')
    best_scart = None
    
    for run in range(num_runs):
        print(f"\n{'='*60}")
        print(f"RUN {run+1}/{num_runs}")
        print(f"{'='*60}")
        
        if run == 0:
            # Prima run: ordinamento per flessibilità
            pazienti = order_patients_by_flexibility(PHOME, n, e, l, t_matrix)
        else:
            # Altre: casuali
            pazienti = order_randomly(PHOME, seed=run)
        
        solution, cost, scart = heuristic_fast(
            n, PHOME, HOSP, D, l, e, serv, t_matrix, T, P, q, Q_max,
            L=L, pazienti_ordinati=pazienti
        )
        
        if cost < best_cost:
            best_solution = solution
            best_scart = scart
            best_cost = cost
            print(f"Nuovo best: {cost:.2f} ({len(scart)} scartati)")
    
    return best_solution, best_cost, best_scart


if __name__ == '__main__':
    json_file_path = "router_bus_main/DATI/input_5c.json"
    data_darp = extract_darp_data(json_file_path)
    
    t_matrix = data_darp['t']
    T = data_darp['T']
    n = data_darp['n']
    e = data_darp['e']
    l = data_darp['l']
    PHOME = data_darp['PHOME']
    HOSP = data_darp['HOSP']
    P = data_darp['P']
    D = data_darp['D']
    q = data_darp['q']
    Q_max = data_darp['Q']
    serv = data_darp['s']
    
   
    best_solution, best_cost, best_scart = heuristic_multistart_fast(n, PHOME, HOSP, D, l, e, serv, t_matrix, T, P, q, Q_max,num_runs=5,L=5  )
    
    print(f"Costo: {best_cost:.2f}")
    print(f"Scartati: {best_scart}")
    print(f"Route: {best_solution}")