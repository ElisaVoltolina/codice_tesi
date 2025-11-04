import gurobipy as gb
from valid_inequalities import*
from gurobipy import Model, GRB, quicksum

def solve_darp(V, PHOSP, DHOSP, HOSP, PHOME, P, D, PD, idx, n, t, s, e, l, T, q, Q,  penalty_weights=None, use_valid_inequalities=True, vi_config=None,  euristic_solution=None):
    """provo ad inserire nuove valid inequality e ad aggiungere in mip.start"""
    model = Model("DARP")

    # Se non vengono forniti i pesi delle penalità, usa valori default
    #poi posso privilegarne alcuen
    if penalty_weights is None:
        penalty_weights = {i: 1000 for i in P}  # Penalità alta per incoraggiare il servizio

    # Variabili
    x = model.addVars(idx, vtype=GRB.BINARY, name="x")  #1 se l'arco è attivo, 0 altimenti
    y = model.addVars(P, vtype=GRB.BINARY, name="y")  # 1 se la richiesta viene eseguita, 0 altrimenti
    A = model.addVars(V, vtype=GRB.CONTINUOUS, name="A")   #tempo di arrivo del veicolo al nodo i
    B = model.addVars(V, vtype=GRB.CONTINUOUS, name="B")   #tempo inizio del servizio al nodo i
    L = model.addVars(P, vtype=GRB.CONTINUOUS, name="L")   #tempo di percorrenza dell’utente relativo al nodo i sul veicolo
    WP = model.addVars(HOSP, vtype=GRB.CONTINUOUS, name="WP")  #tempo di attesa del paziente al nodo i (ospedale)
    Q_var = model.addVars(V, vtype=GRB.CONTINUOUS, name="Q")  #carico del veicolo quando lascia il nodo i

    # Funzione obiettivo MODIFICATA
    obj_travel_time = quicksum(t[i][j] * x[i, j] for i,j in idx)   #tempo di percorrenza
    obj_waiting_time = quicksum(WP[i] for i in HOSP)   #tempo attesa all'ospedale (esclusa la durata della visita in sè)
    obj_penalty = quicksum(penalty_weights[i] * (1 - y[i]) for i in P)  # Penalità per richieste non servite

    model.setObjective(obj_travel_time + obj_waiting_time + obj_penalty, GRB.MINIMIZE) 


    # Vincoli
    
    #Ogni richiesta può essere servita al massimo una volta (se servita)
    model.addConstrs((x.sum(i, '*') == y[i] for i in P), name="richiesta_servita_pickup") 
    model.addConstrs((x.sum(i+n, '*') == y[i] for i in P), name="richiesta_servita_delivery")  
    
    # Se una richiesta viene servita, sia pickup che delivery devono essere visitati
    model.addConstrs((x.sum(i, '*') == x.sum(n+i,'*') for i in P), name="pickup_delivery_insieme")  

    # Il veicolo inizia e finisce al deposito
    model.addConstr((x.sum(0, '*') == 1), name="inizio_deposito")
    model.addConstr((x.sum('*', 2*n+1) == 1), name="fine_deposito")

    # Conservazione del flusso
    model.addConstrs((x.sum('*', i) == x.sum(i, '*') for i in PD), name="conservazione_flusso")

    #Garantisci che le richieste outbpund-inbound siano entrambe servite o entrambe non servite
    model.addConstrs((y[i]==y[i+ n//2] for i in PHOME), name="accopiamnete outbound-inbound")

    # Big-M per i vincoli
    big_M = max(l[i] for i in V) + 1000  # Un valore sufficientemente grande
    

    # Assicura che il pickup sia sempre prima del delivery corrispondente (solo se la richiesta è servita)
    for i in P:
        model.addGenConstrIndicator(y[i], True,B[i] + s[i] + t[i][i+n] <= B[i+n],name=f"precedenza_pickup_delivery_{i}")
    
    #Precedenza richiesta outbound-inbound (solo se entrambe sono servite)
    for i in PHOME:
        model.addGenConstrIndicator(y[i],True, B[i+n] + s[i+n] + t[i+n][i+n//2] <= B[i+n//2] , name=f"precedenza_outbound_inbound_{i}")

   
    # Big-M calculation
    M = {}
    for i, j in idx:
        M[i,j] = max(0, l[i] + s[i] + t[i][j] - e[j]) #+ 1000  # Aggiungo un margine di sicurezza  QUI HO CAMBIATO

   
    # Tempo di arrivo e inizio servizio

    # Tempo tra nodi consecutivi con vincolo Big-M
    model.addConstrs((A[j] >= B[i] + s[i] + t[i][j] - M[i,j] * (1 - x[i, j]) for i,j in idx ), name="tempo_arrivoA") 
     
     


    """#PRODIAMO Ad ALLEGGERIRE QUESTA PARTE

    # Variabile binaria per determinare se A[i] è all'interno della finestra temporale
    # Se in_window[i] = 1, allora B[i] = A[i]
    # Se in_window[i] = 0, allora B[i] = e[i]
    in_window = model.addVars(V, vtype=GRB.BINARY, name="in_window")

    for i in V:
        if i==0 or i==2*n +1: #per i depositi i vincoli sono sempre attivi
             model.addConstrs((A[i] >= e[i] - big_M * (1 - in_window[i]) for i in V), name="in_window_check1")
             model.addConstrs((A[i] <= e[i] + big_M * in_window[i] for i in V), name="in_window_check2")
        elif i in P:
            model.addGenConstrIndicator(y[i],True, A[i] >= e[i] - big_M * (1 - in_window[i]), name=f"in_window_check1_pickup_{i}" )
            model.addGenConstrIndicator(y[i], True, A[i] <= e[i] + big_M * in_window[i], name=f"in_window_check2-pickup_{i}" )
        elif i in D:
            model.addGenConstrIndicator(y[i-n], True, A[i] >= e[i] - big_M * (1 - in_window[i]), name=f"in_window_check1_delivery_{i}" )
            model.addGenConstrIndicator(y[i-n], True, A[i] <= e[i] + big_M * in_window[i], name=f"in_window_check2_delivery_{i}" )
    
    
    for i in V:
        if i==0 or i==2*n +1: #per i depositi i vincoli sono sempre attivi
            model.addConstrs((B[i] >= A[i] - big_M * (1 - in_window[i]) for i in V), name="set_B_if_in_window1")
            model.addConstrs((B[i] <= A[i] + big_M * (1 - in_window[i]) for i in V), name="set_B_if_in_window2")
    
            model.addConstrs((B[i] >= e[i] - big_M * in_window[i] for i in V), name="set_B_if_not_in_window1")
            model.addConstrs((B[i] <= e[i] + big_M * in_window[i] for i in V), name="set_B_if_not_in_window2")
        elif i in P:
            model.addGenConstrIndicator(y[i],True, B[i] >= A[i] - big_M * (1 - in_window[i]), name=f"set_B_if_in_window1_pickup_{i}" )
            model.addGenConstrIndicator(y[i], True, B[i] <= A[i] + big_M * (1 - in_window[i]), name=f"set_B_if_in_window2_pickup_{i}" )

            model.addGenConstrIndicator(y[i],True, B[i] >= e[i] - big_M * in_window[i], name=f"set_B_if_not_in_window1_pickup_{i}" )
            model.addGenConstrIndicator(y[i], True, B[i] <= e[i] + big_M * in_window[i], name=f"et_B_if_not_in_window2_pickup_{i}" )

            # Per richieste NON servite, imposta tempi a 0 
            #model.addGenConstrIndicator(y[i], False, A[i] == 0, name=f"reset_A_pickup_non_servito_{i}")
            #model.addGenConstrIndicator(y[i], False, B[i] == 0, name=f"reset_B_pickup_non_servito_{i}")
        elif i in D:
            model.addGenConstrIndicator(y[i-n],True, B[i] >= A[i] - big_M * (1 - in_window[i]), name=f"set_B_if_in_window1_delivery_{i}" )
            model.addGenConstrIndicator(y[i-n], True, B[i] <= A[i] + big_M * (1 - in_window[i]), name=f"set_B_if_in_window2_delivery_{i}" )

            model.addGenConstrIndicator(y[i-n],True, B[i] >= e[i] - big_M * in_window[i], name=f"set_B_if_not_in_window1_delivery_{i}" )
            model.addGenConstrIndicator(y[i-n], True, B[i] <= e[i] + big_M * in_window[i], name=f"et_B_if_not_in_window2_delivery_{i}" )

            # Per richieste NON servite, imposta tempi a 0 
            #model.addGenConstrIndicator(y[i-n], False, A[i] == 0, name=f"reset_A_delivery_non_servito_{i}")
            #model.addGenConstrIndicator(y[i-n], False, B[i] == 0, name=f"reset_B_delivery_non_servito_{i}")
    
   #se imposto a zero quando non servita diventa infattibile PERCHè"""
    
    
    # VINCOLI TEMPORALI 

    # 1. PROPAGAZIONE TEMPORALE tra nodi consecutivi
    for i, j in idx:
        model.addConstr(
            A[j] >= B[i] + s[i] + t[i][j] - M[i,j] * (1 - x[i,j]), 
            name=f"tempo_arrivo_{i}_{j}"
        )

    # 2. B >= A sempre (inizio servizio dopo arrivo)
    model.addConstrs((B[i] >= A[i] for i in V), name="B_dopo_A")

    # 3. TIME WINDOWS - Vincoli base per TUTTI i nodi
    model.addConstrs((B[i] >= e[i] for i in V), name="timewindow_early")
    model.addConstrs((B[i] <= l[i] for i in V), name="timewindow_late")







   
    # Ride time (solo per richieste servite)
    for i in P:
        model.addGenConstrIndicator(y[i], True, L[i] == B[i + n] - (B[i] + s[i]), name=f"ride_time_{i}")


    #Tempo massimo di percorrenza (solo per richieste servite)
    for i in P: 
        model.addGenConstrIndicator(y[i], True, L[i] >= t[i][i + n] + s[i+n] , name=f"tempo_max_percorrenza_1_{i}")
        model.addGenConstrIndicator(y[i], True, L[i] <= T[i] , name=f"tempo_max_percorrenza_2_{i}")



    """# Time window    (QUESTI SONO SUPERFLUI PENSO)
    model.addConstrs((B[i] >= e[i] for i in V), name="timewindow1")
    model.addConstrs((B[i] <= l[i] for i in V), name="timewindow2")"""  




    # Tempo di attesa
    for i in PHOSP:
        model.addGenConstrIndicator(y[i], True,  WP[i] >= A[i] - e[i] , name="tempo_attesa_pickup")
        model.addGenConstrIndicator(y[i], True, WP[i] >= 0, name=f"wp_ind_nonneg_{i}")
        model.addGenConstrIndicator(y[i], False, WP[i] == 0, name=f"no_attesa_pickup_non_servito_{i}")
    for i in DHOSP:
        #model.addGenConstrIndicator( y[i-n], True  ,WP[i] >= A[i] - l[i] , name="tempo_attesa_delivery")  QUI C'ERA QUESTO ERRORE
        model.addGenConstrIndicator( y[i-n], True  ,WP[i] >= l[i]- A[i] , name="tempo_attesa_delivery")
        model.addGenConstrIndicator(y[i-n], False, WP[i] == 0, name=f"no_attesa_delivery_non_servito_{i}")
    model.addConstrs((WP[i] >= 0 for i in HOSP), name="tempo_attesa")


    # Capacità del veicolo
    # Reset della capacità all'inizio
    model.addConstr(Q_var[0] == 0, name="capacità_iniziale")
    
    # capacità durante il percorso
    for i, j in idx:
        if j != 2*n+1:  # Escludi archi da/verso il deposito finale/iniziale
            if i in PD:  # Se i è un pickup (delivery) aggiungi (togli) il carico
                model.addConstr(Q_var[j] >= Q_var[i] + q[i] - Q * (1 - x[i, j]), name=f"cap_update_pickup_{i}_{j}")
            else:  # Deposito iniziale o altri nodi
                model.addConstr(Q_var[j] >= Q_var[i] - Q * (1 - x[i, j]), name=f"cap_update_other_{i}_{j}")
    
    # Limiti di capacità
    model.addConstrs((Q_var[i] >= 0 for i in V), name="capacità_minima")
    model.addConstrs((Q_var[i] <= Q for i in V), name="capacità_massima")
    


    # Eliminazione subtour (# Metodo Miller-Tucker-Zemlin)
    u = model.addVars(V, vtype=GRB.CONTINUOUS, name="u")
    model.addConstrs((u[i] >= 1 for i in V if i != 0 and i != 2*n+1), name="u_lb")
    model.addConstrs((u[i] <= 2*n for i in V if i != 0 and i != 2*n+1), name="u_ub")
    
    model.addConstr(u[0] == 0, name="u_depot_start")
    model.addConstr(u[2*n+1] == 2*n+1, name="u_depot_end")
    
    for i, j in idx:
        if i != 0 and j != 0 and j != 2*n+1 and i != 2*n+1:
            model.addConstr(u[j] >= u[i] + 1 - (2*n+1) * (1 - x[i, j]), name=f"subtour_{i}_{j}")



    #VALID INEQUALITIES

    #aggiunta di nuove valid inequalities
    if use_valid_inequalities:
        variables = {
            'x': x,
            'B': B,
            'Q_var': Q_var
        }
        
        data = {
            'V': V,
            'P': P,
            'idx': idx,
            'T':T,
            'e': e,
            'l': l,
            's': s,
            't': t,
            'q': q,
            'n': n
        }
        
        vi_stats = add_all_valid_inequalities(model, variables, data, vi_config)


    
   
    # APPLICA MIP START SE DISPONIBILE
   
    if euristic_solution is not None:
        print("\n" + "="*60)
        print("APPLICAZIONE MIP START DA EURISTICA")
        print("="*60)
        
        # Converti la soluzione euristica in valori per le variabili
        mip_start_values = euristic_solution_to_mip_start(euristic_solution, n, P, D, PD, V, idx, e, l, s, t, q, Q)
        
        # Applica al modello
        apply_mip_start(model, mip_start_values, x, y, A, B, L, Q_var, P, V, idx)
        
        print("="*60 + "\n")
    else:
        print("Nessun MIP start fornito, il solver parte da zero")


    
    # Risoluzione con timeout aumentato
    model.Params.TimeLimit = 60  # TEMPO LIMITE(in secondi)     1 MIN  
    model.Params.MIPGap = 0.05    # 5% gap di ottimalità
    model.Params.FeasibilityTol = 1e-6  # Tolleranza di feasibility più stringente
    
    # Aggiungi più dettagli nella fase di log
    model.Params.OutputFlag = 1
    model.Params.LogToConsole = 0

    # Risoluzione
    model.optimize()

    if model.status == GRB.INFEASIBLE:
        print("Il modello è infattibile! ")

        #DEBAG
        #model.computeIIS()
        #model.write("model_infeasibleP.ilp")  # Salva i vincoli impossibili in un file

    # Recupero della soluzione 
    if model.status == GRB.OPTIMAL or model.status == GRB.TIME_LIMIT:
        if model.status == GRB.OPTIMAL:
            print('Soluzione ottimale trovata')
            current_gap=0.0
        else:
            current_gap=model.MIPGap
            print(f'Soluzione sub-ottimale trovata con gap {model.MIPGap*100:.2f}%')
            
        solution_x = {}
        for i, j in idx:
            if x[i, j].X > 0.5:  # Solo archi attivi
                solution_x[(i, j)] = 1
                print(f"Arco ({i},{j}) attivo")
        
        solution_y = {i: y[i].X for i in P}  
        solution_A = {i: A[i].X for i in V}
        solution_B = {i: B[i].X for i in V}
        solution_L = {i: L[i].X for i in P}
        solution_WP = {i: WP[i].X for i in HOSP}
        solution_Q = {i: Q_var[i].X for i in V}   

        # Stampa informazioni 
        print(f"\nRichieste servite: {sum(solution_y.values())}/{len(P)}")
        for i in P:
            if solution_y[i] > 0.5:
                print(f"Richiesta {i}: SERVITA")
            else:
                print(f"Richiesta {i}: NON SERVITA")

        print("\nTempi di arrivo:")
        for i in V:
            print(f"Nodo {i}: {solution_A[i]:.2f} (finestra: {e[i]}-{l[i]})")

        print("\nTempi di inizio servizio:")
        for i in V:
            print(f"Nodo {i}: {solution_B[i]:.2f} (finestra: {e[i]}-{l[i]})")


        print(current_gap, model.ObjVal , model.ObjBound)      
        return (solution_x, solution_A, solution_L, solution_B, solution_WP, solution_Q, solution_y), current_gap, model.ObjVal , model.ObjBound 
    else:
        print("No optimal solution found")
        return None, None







"""
Funzioni per convertire la soluzione euristica in MIP start per Gurobi
"""

def euristic_solution_to_mip_start(euristic_route, n, P, D, PD, V, idx, e, l, s, t, q, Q):
    """
    Converte la soluzione euristica in valori iniziali per le variabili del modello.
    PAZIENTI SCARTATI: fornisce valori solo per i nodi effettivamente visitati.
    
    Returns:
    dict : Dizionario con i valori iniziali per le variabili rilevanti
    """
    
    # Inizializza dizionario vuoto 
    mip_start = {}
    
    # Identifica quali richieste sono nella route
    visited_nodes = set(euristic_route)
    
    # 1. Variabili x (archi) 
    for pos in range(len(euristic_route) - 1):
        i = euristic_route[pos]
        j = euristic_route[pos + 1]
        if (i, j) in idx:
            mip_start[('x', i, j)] = 1
    
    
    # 2. Variabili y (richieste servite)
    served_requests = []
    for i in P:
        if i in visited_nodes:
            mip_start[('y', i)] = 1
            served_requests.append(i)
        else:
            mip_start[('y',i)]=0

    '''
    # 3. Calcola tempi A, B, Q_var SOLO per i nodi visitati
    current_time = e[0]  # Parte dal deposito iniziale
    current_load = 0
    
    for pos, node in enumerate(euristic_route):
        if pos == 0:
            # Deposito iniziale
            mip_start[('A', node)] = current_time
            mip_start[('B', node)] = current_time
            mip_start[('Q', node)] = 0
        else:
            prev_node = euristic_route[pos - 1]
            
            # Tempo di arrivo
            arrival_time = current_time + s[prev_node] + t[prev_node][node]
            mip_start[('A', node)] = arrival_time
            
            # Tempo di inizio servizio (rispetta time window)
            start_time = max(arrival_time, e[node])
            mip_start[('B', node)] = start_time
            current_time = start_time
            
            # Aggiorna carico
            if node in PD:
                current_load += q[node]
            mip_start[('Q', node)] = current_load
    
    print(f"   ✓ Calcolati tempi per {len([k for k in mip_start if k[0] == 'A'])} nodi")
    
    # 4. Calcola ride time L SOLO per le richieste servite
    for i in served_requests:
        pickup_node = i
        delivery_node = i + n
        
        if ('B', pickup_node) in mip_start and ('B', delivery_node) in mip_start:
            ride_time = (mip_start[('B', delivery_node)] - 
                       (mip_start[('B', pickup_node)] + s[pickup_node]))
            mip_start[('L', i)] = max(0, ride_time)
    
    print(f"   ✓ Calcolati ride time per {len([k for k in mip_start if k[0] == 'L'])} richieste")
    '''

    
    return mip_start


def apply_mip_start(model, mip_start_values, x, y, A, B, L, Q_var, P, V, idx):
    """
    Applica i valori di MIP start al modello Gurobi
    """
    
    try:
        count = {'x': 0, 'y': 0, 'A': 0, 'B': 0, 'L': 0, 'Q': 0}
        
        # Applica valori per x (archi)
        for i, j in idx:
            if ('x', i, j) in mip_start_values:
                x[i, j].Start = mip_start_values[('x', i, j)]
                count['x'] += 1
        
        # Applica valori per y (richieste servite)
        for i in P:
            if ('y', i) in mip_start_values:
                y[i].Start = mip_start_values[('y', i)]
                count['y'] += 1
        
        '''# Applica valori per A, B, Q (tempi e carico)
        for i in V:
            if ('A', i) in mip_start_values:
                A[i].Start = mip_start_values[('A', i)]
                count['A'] += 1
            
            if ('B', i) in mip_start_values:
                B[i].Start = mip_start_values[('B', i)]
                count['B'] += 1
            
            if ('Q', i) in mip_start_values:
                Q_var[i].Start = mip_start_values[('Q', i)]
                count['Q'] += 1
        
        # Applica valori per L (ride time)
        for i in P:
            if ('L', i) in mip_start_values:
                L[i].Start = mip_start_values[('L', i)]
                count['L'] += 1
        '''
        print(f"  MIP start applicato:")
        print(f"- {count['x']} archi")
        print(f" - {count['y']} richieste")
        print(f" - {count['A']} tempi arrivo")
        print(f" - {count['B']} tempi inizio servizio")
        print(f"- {count['Q']} carichi")
        print(f"- {count['L']} ride times")
        
    except Exception as e:
        print(f" Errore nell'applicazione del MIP start: {e}")
        print(f" Il solver partirà senza soluzione iniziale")



