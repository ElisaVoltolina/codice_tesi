import gurobipy as gb

from gurobipy import Model, GRB, quicksum
#import parameters

def solve_darp(V, PHOSP, DHOSP, HOSP, PHOME, P, D, PD, idx, n, t, s, e, l, T, q, Q):
    
    model = Model("DARP")

    # Variabili
    x = model.addVars(idx, vtype=GRB.BINARY, name="x")
    A = model.addVars(V, vtype=GRB.CONTINUOUS, name="A")
    B = model.addVars(V, vtype=GRB.CONTINUOUS, name="B")
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
    model.addConstrs((B[i] + s[i]+ t[i][i+n] <= B[i+n] for i in P), name="precedenza pickup-delivery")


    #Precedenza richiesta outbound- inbound
    model.addConstrs((B[i+n]+s[i+n]+t[i+n][i+n//2]<= B[i+n//2] for i in PHOME), name="precedenza outbound-inbound")
    #model.addConstrs((B[i+n]+s[i+n]<= B[i+n//2] for i in PHOME), name="precedenza outbound-inbound")





    # Tempo di arrivo

    # Big-M calculation
    M = {}
    for i, j in idx:
        M[i,j] = max(0, l[i] + s[i] + t[i][j] - e[j]) + 1000  # Aggiungo un margine di sicurezza

    # Tempo tra nodi consecutivi con vincolo Big-M
    #model.addConstrs((B[j] >= B[i] + s[i] + t[i][j] - M[i,j] * (1 - x[i, j]) for i, j in idx), name="tempo_arrivo_B")
    model.addConstrs((A[j] >= B[i] + s[i] + t[i][j] -  M[i,j]* (1 - x[i, j]) for i,j in idx ), name="tempo arrivoA") 
    
    #model.addConstrs(B[i]>= A[i] for i in V) 


    
    # Variabile binaria per determinare se A[i] è all'interno della finestra temporale
    in_window = model.addVars(V, vtype=GRB.BINARY, name="in_window")

# Big-M per i vincoli
    big_M = max(l[i] for i in V) + 1000  # Un valore sufficientemente grande
    
# Se A[i] >= e[i], allora in_window[i] = 1
    model.addConstrs((A[i] >= e[i] - big_M * (1 - in_window[i]) for i in V), name="in_window_check1")
    model.addConstrs((A[i] <= e[i] + big_M * in_window[i] for i in V), name="in_window_check2")
    
# Se in_window[i] = 1, allora B[i] = A[i]
# Se in_window[i] = 0, allora B[i] = e[i]
    model.addConstrs((B[i] >= A[i] - big_M * (1 - in_window[i]) for i in V), name="set_B_if_in_window1")
    model.addConstrs((B[i] <= A[i] + big_M * (1 - in_window[i]) for i in V), name="set_B_if_in_window2")
    
    model.addConstrs((B[i] >= e[i] - big_M * in_window[i] for i in V), name="set_B_if_not_in_window1")
    model.addConstrs((B[i] <= e[i] + big_M * in_window[i] for i in V), name="set_B_if_not_in_window2")







    # Ride time
    model.addConstrs((L[i] == B[i + n] - (B[i] +s[i]) for i in P), name="ride time")

    # Tempo massimo di percorrenza 
    model.addConstrs( (L[i]>= t[i][i + n] + s[i+n]  for i in P), name=" tempo max percorrenza 1") #L[i] comprende tempo servizio delivery
    model.addConstrs((L[i] <= T[i] for i in P), name=" tempo max percorrenza 2")

    # Time window    
    model.addConstrs((B[i]>=e[i] for i in V), name="timewindow1")
    model.addConstrs((B[i] <= l[i] for i in V), name="timewindow2")  

    # Tempo di attesa
    #model.addConstrs((WP[i] >= B[i] - e[i] for i in PHOSP), name="tempo attesa pickup")
    model.addConstrs((WP[i] >= A[i] - e[i] for i in PHOSP), name="tempo attesa pickup")

    model.addConstrs((WP[i] >= A[i] - l[i] for i in DHOSP), name="tempo attesa delivery")
    #model.addConstrs((WP[i] >= A[i] - (B[i-n] + s[i-n] + t[i-n][i]) for i in DHOSP), name="tempo attesa delivery")
    model.addConstrs((WP[i] >= 0 for i in HOSP), name="tempo attesa")

    # Capacità del veicolo

    # Reset della capacità all'inizio
    model.addConstr(Q_var[0] == 0, name="capacità iniziale")
    
    # capacità durante il percorso
    for i, j in idx:
        if j != 2*n+1:  # Escludi archi da/verso il deposito finale/iniziale
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
    model.Params.TimeLimit = 600  # 10 minuti di timeout
    model.Params.MIPGap = 0.05    # 5% gap di ottimalità
    model.Params.FeasibilityTol = 1e-6  # Tolleranza di feasibility più stringente
    
    # Aggiungi più dettagli nella fase di log
    model.Params.OutputFlag = 1
    model.Params.LogToConsole = 1


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
        solution_B ={i: B[i].X for i in V}
        solution_L = {i: L[i].X for i in P}
        solution_WP = {i: WP[i].X for i in HOSP}
        solution_Q = {i: Q_var[i].X for i in V}   

        # Stampa informazioni aggiuntive per debug
        print("\nTempi di arrivo:")
        for i in V:
            print(f"Nodo {i}: {solution_A[i]:.2f} (finestra: {e[i]}-{l[i]})")

        print("\nTempi di inizio servizio:")
        for i in V:
            print(f"Nodo {i}: {solution_B[i]:.2f} (finestra: {e[i]}-{l[i]})")
            
        

        return solution_x, solution_A, solution_L, solution_B, solution_WP, solution_Q
    else:
        print("No optimal solution found")
        return None
