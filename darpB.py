import gurobipy as gb

from gurobipy import Model, GRB, quicksum
#import parameters

def solve_darp(V, PHOSP, DHOSP, HOSP, P, D, PD, idx, n, t, d, s, e, l, T, q, Q):
    
    model = Model("DARP")

    # Variabili
    x = model.addVars(idx, vtype=GRB.BINARY, name="x")
    A = model.addVars(V, vtype=GRB.CONTINUOUS, name="A")
    B = model.addVars(V, vtype=GRB.CONTINUOUS, name="B")
    L = model.addVars(P, vtype=GRB.CONTINUOUS, name="L")
    WP = model.addVars(HOSP, vtype=GRB.CONTINUOUS, name="WP")
    Q_var = model.addVars(V, vtype=GRB.CONTINUOUS, name="Q")

    # Funzione obiettivo
    #model.setObjective(quicksum(t[i][j] * x[i, j] for i,j in idx) + quicksum(WP[i] for i in HOSP), GRB.MINIMIZE)
    obj_travel_time= quicksum(t[i][j] * x[i, j] for i,j in idx)
    obj_waiting_time= quicksum(WP[i] for i in HOSP)

    model.setObjective( obj_travel_time + obj_waiting_time, GRB.MINIMIZE) 


    # Vincoli
    
    # Ogni richiesta deve essere servita esattamente una volta
    model.addConstrs((x.sum(i, '*') == 1 for i in P), name="ogni richiesta 1 volta.1") 
    model.addConstrs((x.sum(i, '*')==x.sum(n+i,'*') for i in P ), name= "ogni richiesta 1 volta.2")

    # Il veicolo inizia e finisce al deposito
    model.addConstr((x.sum(0, '*') == 1), name="inizio deposito")
    model.addConstr((x.sum('*', 2*n+1) == 1), name="fine deposito")

    # Conservazione del flusso
    model.addConstrs((x.sum('*', i) == x.sum(i, '*') for i in PD), name="conservazione flusso")

    # Tempo di arrivo
    model.addConstrs((A[j] >= B[i] + s[i] + t[i][j] - ((e[i] + s[i] + t[i][j]) * (1 - x[i, j])) for i,j in idx ), name="tempo arrivo1") 
    model.addConstrs((A[j] <= B[i] + s[i] + t[i][j] + (l[2*n+1] * (1 - x[i, j])) for i,j in idx ), name="tempo arrivo2") 

    # Ride time
    model.addConstrs((L[i] == B[i + n] + s[i + n] - (B[i] + s[i]) for i in P), name="ride time")

    # Tempo massimo di percorrenza 
    model.addConstrs( (L[i]>= t[i][i + n] + s[i + n] for i in P), name=" tempo max percorrenza 1")
    model.addConstrs((L[i] <= T[i] for i in P), name=" tempo max percorrenza 2")

    # Time window  
    #model.addConstrs((e[i] <= B[i] for i in PD), name="timewindow1")  
    model.addConstrs((B[i]>=e[i] for i in PD), name="timewindow1")
    model.addConstrs((B[i] <= l[i] for i in PD), name="timewindow2")

    # Tempo di attesa
    model.addConstrs((WP[i] >= A[i] - e[i] for i in PHOSP), name="tempo attesa1")
    model.addConstrs((WP[i] >= l[i] - A[i] for i in DHOSP), name="tempo attesa2")
    model.addConstrs((WP[i] >= 0 for i in HOSP), name="tempo attesa3")

    # Capacità del veicolo
    model.addConstrs((Q_var[j] >= (q[j] + Q_var[i]) * x[i, j] for i,j in idx ), name="capacità veivolo1")
    #model.addConstrs( (Q_var[i] >=max(0, q[i]) for i in V), name=" capacità veivolo2")
    model.addConstrs((Q_var[i]>=0 for i in V), name="capacità veicoli2.1")
    model.addConstrs((Q_var[i]>=q[i] for i in V), name="capacità veicoli2.2")
    #model.addConstrs((Q_var[i] <= min(Q, Q + q[i]) for i in V), name="capacità veivolo3")
    model.addConstrs((Q_var[i] <= Q for i in V), name="capacità veivolo3.1")
    model.addConstrs((Q_var[i] <= Q + q[i] for i in V), name="capacità veivolo3.2")
    
    # Risoluzione
    model.optimize()


    if model.status == GRB.INFEASIBLE:
        print("Il modello è infattibile! Cerco il conflitto tra i vincoli...")
        model.computeIIS()
        model.write("model_infeasible.ilp")  # Salva i vincoli impossibili in un file


    # Recupero della soluzione 
    if model.status == GRB.OPTIMAL:
        print('Optimal Solution Found')
        solution_x = model.getAttr('x', x)
        solution_A = model.getAttr('x', A)
        solution_B = model.getAttr('x', B)
        solution_L = model.getAttr('x', L)
        solution_WP = model.getAttr('x', WP)
        solution_Q = model.getAttr('x', Q_var)   

        return solution_x, solution_A, solution_B, solution_L, solution_WP, solution_Q
    else:
        print("No optimal solution found")
