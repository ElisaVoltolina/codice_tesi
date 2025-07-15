import gurobipy as gb

from gurobipy import Model, GRB, quicksum
#import parameters

def solve_darp(V, PHOSP, DHOSP, HOSP, P, D, PD, idx, n, t, d, s, e, l, T, q, Q):
    
    model = Model("DARP")

    # Variabili
    x = model.addVars(idx, vtype=GRB.BINARY, name="x")
    A = model.addVars(V, vtype=GRB.CONTINUOUS, name="A")
    
    L = model.addVars(P, vtype=GRB.CONTINUOUS, name="L")
    WP = model.addVars(HOSP, vtype=GRB.CONTINUOUS, name="WP")
    Q_var = model.addVars(V, vtype=GRB.CONTINUOUS, name="Q")

    # Funzione obiettivo
    
    obj_travel_time= quicksum(t[i][j] * x[i, j] for i,j in idx)
    obj_waiting_time= quicksum(WP[i] for i in HOSP)

    model.setObjective( obj_travel_time + obj_waiting_time, GRB.MINIMIZE) 


# DEBUG: Stampa i limiti temporali per verifica
    print("Time Windows:")
    for i in V:
        print(f"Node {i}: [{e[i]} - {l[i]}]")
    
    # Controlla se ci sono incoerenze nei time window
    for i in P:
        delivery = i + n
        min_arrival_delivery = e[i] + s[i] + t[i][delivery]
        if min_arrival_delivery > l[delivery]:
            print(f"ATTENZIONE: Time window incoerente per richiesta {i}:")
            print(f"  Pickup node {i}: [{e[i]}-{l[i]}], service time: {s[i]}")
            print(f"  Delivery node {delivery}: [{e[delivery]}-{l[delivery]}]")
            print(f"  Tempo minimo necessario: {min_arrival_delivery} > {l[delivery]}")
            # Aggiusta automaticamente i time window
            l[delivery] = min_arrival_delivery + 5  # Aggiungi un po' di margine
            print(f"  AGGIUSTATO a: [{e[delivery]}-{l[delivery]}]")

    # Vincoli
    
    # Ogni richiesta deve essere servita esattamente una volta
    model.addConstrs((x.sum(i, '*') == 1 for i in P), name="ogni richiesta 1 volta.1") 
    model.addConstrs((x.sum(i, '*')==x.sum(n+i,'*') for i in P ), name= "ogni richiesta 1 volta.2")

    # Il veicolo inizia e finisce al deposito
    model.addConstr((x.sum(0, '*') == 1), name="inizio deposito")
    model.addConstr((x.sum('*', 2*n+1) == 1), name="fine deposito")

    # Conservazione del flusso
    model.addConstrs((x.sum('*', i) == x.sum(i, '*') for i in PD), name="conservazione flusso")

    # Assicura che il pickup sia sempre prima del delivery corrispondente

    model.addConstrs((A[i] + s[i]+ t[i][i+n] <= A[i+n] for i in P), name="precedenza pickup-delivery")


    # Tempo di arrivo

    M_lower = {}
    M_upper = {}
    for i, j in idx:
        M_lower[i, j] = max(0, e[i] + s[i] + t[i][j] - e[j])  # Big-M per limite inferiore
        M_upper[i, j] = max(0, l[j] - (e[i] + s[i] + t[i][j]))  # Big-M per limite superiore
    

    model.addConstrs((A[j] >= A[i] + s[i] + t[i][j] -  M_lower[i,j]* (1 - x[i, j]) for i,j in idx ), name="tempo arrivo1") 
    #model.addConstrs((A[j] <= A[i] + s[i] + t[i][j] + M_upper[i,j] * (1 - x[i, j]) for i,j in idx ), name="tempo arrivo2") 

    # Ride time
    model.addConstrs((L[i] == A[i + n] - (A[i] +s[i]) for i in P), name="ride time")

    # Tempo massimo di percorrenza 
    model.addConstrs( (L[i]>= t[i][i + n]  for i in P), name=" tempo max percorrenza 1")
    model.addConstrs((L[i] <= T[i] for i in P), name=" tempo max percorrenza 2")

    # Time window    
    model.addConstrs((A[i]>=e[i] for i in PD), name="timewindow1")
    model.addConstrs((A[i] <= l[i] for i in PD), name="timewindow2")

    # Tempo di attesa
    model.addConstrs((WP[i] >= A[i] - e[i] for i in PHOSP), name="tempo attesa pickup")

    model.addConstrs((WP[i] >= A[i] - (A[i-n] + s[i-n] + t[i-n][i]) for i in DHOSP), name="tempo attesa delivery")
    model.addConstrs((WP[i] >= 0 for i in HOSP), name="tempo attesa")

    # Capacità del veicolo
    # Reset della capacità all'inizio
    model.addConstr(Q_var[0] == 0, name="capacità iniziale")
    
    # capacità durante il percorso
    for i, j in idx:
        if j != 0:  # Escludi archi da/verso il deposito finale/iniziale
            if i in PD:  # Se i è un pickup (delivery) aggiungi (togli) il carico
                model.addConstr(Q_var[j] >= Q_var[i] + q[i] - Q * (1 - x[i, j]), name=f"cap_update_pickup_{i}_{j}")
            else:  # Deposito iniziale o altri nodi
                model.addConstr(Q_var[j] >= Q_var[i] - Q * (1 - x[i, j]), name=f"cap_update_other_{i}_{j}")
    
    # Limiti di capacità
    model.addConstrs((Q_var[i] >= 0 for i in V), name="capacità minima")
    model.addConstrs((Q_var[i] <= Q for i in V), name="capacità massima")
    

    #eliminazione subtour (# Metodo Miller-Tucker-Zemlin)
    u = model.addVars(V, vtype=GRB.CONTINUOUS, name="u")
    model.addConstrs((u[i] >= 1 for i in V if i != 0 and i != 2*n+1), name="u_lb")
    model.addConstrs((u[i] <= 2*n for i in V if i != 0 and i != 2*n+1), name="u_ub")
    
    model.addConstr(u[0] == 0, name="u_depot_start")
    model.addConstr(u[2*n+1] == 2*n+1, name="u_depot_end")
    
    for i, j in idx:
        if i != 0 and j != 0 and j != 2*n+1 and i != 2*n+1:
            model.addConstr(u[j] >= u[i] + 1 - (2*n+1) * (1 - x[i, j]), name=f"subtour_{i}_{j}")
    
    # Risoluzione con timeout aumentato
    model.Params.TimeLimit = 300  # 5 minuti di timeout
    model.Params.MIPGap = 0.05    # 5% gap di ottimalità



    # Risoluzione
    model.optimize()


    if model.status == GRB.INFEASIBLE:
        print("Il modello è infattibile! Cerco il conflitto tra i vincoli...")
        model.computeIIS()
        model.write("model_infeasible.ilp")  # Salva i vincoli impossibili in un file


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
        
        solution_A = {i: A[i].X for i in V}
        solution_L = {i: L[i].X for i in P}
        solution_WP = {i: WP[i].X for i in HOSP}
        solution_Q = {i: Q_var[i].X for i in V}   

        # Stampa informazioni aggiuntive per debug
        print("\nTempi di arrivo:")
        for i in V:
            print(f"Nodo {i}: {solution_A[i]:.2f} (finestra: {e[i]}-{l[i]})")
            
        print("\nRide times per richiesta:")
        for i in P:
            print(f"Richiesta {i}: {solution_L[i]:.2f} (max: {T[i]})")

        return solution_x, solution_A, solution_L, solution_WP, solution_Q
    else:
        print("No optimal solution found")
        return None
