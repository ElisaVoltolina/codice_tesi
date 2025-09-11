import gurobipy as gb

from gurobipy import Model, GRB, quicksum

def solve_darp(V, PHOSP, DHOSP, HOSP, PHOME, P, D, PD, idx, n, t, s, e, l, T, q, Q,  penalty_weights=None):
    
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

    # DEBUG: Stampa i limiti temporali per verifica
    #print("Time Windows:")
    #for i in V:
        #print(f"Node {i}: [{e[i]} - {l[i]}]")
    
    # DEBUG: Controlla se ci sono incoerenze nei time window
    #for i in P:
        #delivery = i + n
        #min_arrival_delivery = e[i] + s[i] + t[i][delivery]
        #if min_arrival_delivery > l[delivery]:
            #print(f"ATTENZIONE: Time window incoerente per richiesta {i}:")
            #print(f"  Pickup node {i}: [{e[i]}-{l[i]}], service time: {s[i]}")
           # print(f"  Delivery node {delivery}: [{e[delivery]}-{l[delivery]}]")
           # print(f"  Tempo minimo necessario: {min_arrival_delivery} > {l[delivery]}")
            # Aggiusta automaticamente i time window
            #l[delivery] = min_arrival_delivery + 5  # Aggiungi un po' di margine
            #print(f"  AGGIUSTATO a: [{e[delivery]}-{l[delivery]}]")

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
        M[i,j] = max(0, l[i] + s[i] + t[i][j] - e[j]) + 1000  # Aggiungo un margine di sicurezza

   


    # Tempo di arrivo e inizio servizio
    # Tempo tra nodi consecutivi con vincolo Big-M
    model.addConstrs((A[j] >= B[i] + s[i] + t[i][j] - M[i,j] * (1 - x[i, j]) for i,j in idx ), name="tempo_arrivoA") 
     
    '''#in questo modo se xij=1 vale l'uguaglianza 
    for i, j in idx:
        model.addGenConstrIndicator(x[i,j], True, A[j] == B[i] + s[i] + t[i][j], name=f"tempo_arrivo_esatto_{i}_{j}")'''




    # Variabile binaria per determinare se A[i] è all'interno della finestra temporale
    # Se in_window[i] = 1, allora B[i] = A[i]
    # Se in_window[i] = 0, allora B[i] = e[i]
    in_window = model.addVars(V, vtype=GRB.BINARY, name="in_window")

    # Per depositi, in_window è sempre attivo FORSE SUPERFLO SPECIFICARE
    #model.addConstr(in_window[0] == 1, name="deposito_inizio_sempre_attivo")
    #model.addConstr(in_window[2*n+1] == 1, name="deposito_fine_sempre_attivo")

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
    
   #se imposto a zero quando non servita diventa infattibile PERCHè

   

   
    # Ride time (solo per richieste servite)
    for i in P:
        model.addGenConstrIndicator(y[i], True, L[i] == B[i + n] - (B[i] + s[i]), name=f"ride_time_{i}")




    
    #Tempo massimo di percorrenza (solo per richieste servite)
    for i in P: 
        model.addGenConstrIndicator(y[i], True, L[i] >= t[i][i + n] + s[i+n] , name=f"tempo_max_percorrenza_1_{i}")
        model.addGenConstrIndicator(y[i], True, L[i] <= T[i] , name=f"tempo_max_percorrenza_2_{i}")



    # Time window    (qui non serve disattivarli) QUESTI LI POSSO TOGLIERE PENSO
    model.addConstrs((B[i] >= e[i] for i in V), name="timewindow1")
    model.addConstrs((B[i] <= l[i] for i in V), name="timewindow2")  





    # Tempo di attesa
    for i in PHOSP:
        model.addGenConstrIndicator(y[i], True,  WP[i] >= A[i] - e[i] , name="tempo_attesa_pickup")
        model.addGenConstrIndicator(y[i], False, WP[i] == 0, name=f"no_attesa_pickup_non_servito_{i}")
    for i in DHOSP:
        model.addGenConstrIndicator( y[i-n], True  ,WP[i] >= A[i] - l[i] , name="tempo_attesa_delivery")
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
    
    # Risoluzione con timeout aumentato
    model.Params.TimeLimit = 600  # 10 minuti di timeout
    model.Params.MIPGap = 0.05    # 5% gap di ottimalità
    model.Params.FeasibilityTol = 1e-6  # Tolleranza di feasibility più stringente
    
    # Aggiungi più dettagli nella fase di log
    model.Params.OutputFlag = 1
    model.Params.LogToConsole = 0

    # Risoluzione
    model.optimize()

    if model.status == GRB.INFEASIBLE:
        print("Il modello è infattibile! Cerco il conflitto tra i vincoli...")
        model.computeIIS()
        model.write("model_infeasibleP.ilp")  # Salva i vincoli impossibili in un file

    # Recupero della soluzione 
    if model.status == GRB.OPTIMAL or model.status == GRB.TIME_LIMIT:
        if model.status == GRB.OPTIMAL:
            print('Soluzione ottimale trovata')
        else:
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
            
        return solution_x, solution_A, solution_L, solution_B, solution_WP, solution_Q, solution_y  
    else:
        print("No optimal solution found")
        return None