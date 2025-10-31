import gurobipy as gb
from gurobipy import Model, GRB, quicksum


def add_time_bounds_inequalities(model, x, B, V, idx, e, l, s, t, n, active=True): #ok
    """
     Bounds rafforzati su variabili di tempo
      Returns:
        (count_lower, count_upper): Numero vincoli aggiunti
    """
    if not active:
        print("Time bounds inequalities disattivate")
        return 0, 0
    
    count_lb, count_ub = 0, 0   #conteggio dei vincoli aggiunti (lb=lower bound; ub=ubber bound)
    
    #  Lower Bound 
    for i in V:
        if i == 0 or i == 2*n + 1:
            continue
        
        coeffs = {}
        for j in V:
            if i != j and (j, i) in idx:
                coeff = max(0, e[j] - e[i] + s[j] + t[j][i])
                if coeff > 1e-6: #PERCHè FACCIO QUESTO CONTROLLO?? POTEI TOGLIERLO penso serva ad avere dei vingoli aggiuntivi anhc equando il guadagno è veramnte poco
                    coeffs[j] = coeff
        
        if coeffs:
            model.addConstr(
                B[i] >= e[i] + quicksum(coeffs[j] * x[j, i] for j in coeffs),
                name=f"VI_time_lb_{i}"
            )
            count_lb += 1
    
    #  Upper Bound 
    for i in V:
        if i == 0 or i == 2*n + 1:
            continue
        
        coeffs = {}
        for j in V:
            if i != j and (i, j) in idx:
                coeff = max(0, l[i] - l[j] + s[i] + t[i][j])
                if coeff > 1e-6:
                    coeffs[j] = coeff
        
        if coeffs:
            model.addConstr(
                B[i] <= l[i] - quicksum(coeffs[j] * x[i, j] for j in coeffs),
                name=f"VI_time_ub_{i}"
            )
            count_ub += 1
    
    print(f" Lower bounds: {count_lb}, Upper bounds: {count_ub}")
    return count_lb, count_ub


def add_load_bounds_inequalities(model, x, Q_var, V, idx, q, n, active=True):  #questa per ora mi da problemi, risulta troppo restringente e peggiora il risultato
    """
     lower Bounds rafforzati su variabili di carico
    
    Returns:
        count: Numero vincoli aggiunti
    """
    if not active:
        print("  Load bounds inequalities disattivate")
        return 0
    
    count = 0
    
    for i in V:
        if i == 0 or i == 2*n + 1:
            continue
        
        coeffs = {}
        for j in V:
            if i != j and (j, i) in idx:
                coeff = max(0, q[j])
                if coeff > 1e-6:
                    coeffs[j] = coeff
        
        if coeffs:
            base_load = max(0, q[i])
            model.addConstr(
                Q_var[i] >= base_load + quicksum(coeffs[j] * x[j, i] for j in coeffs),
                name=f"VI_load_lb_{i}"
            )
            count += 1
    
    print(f" Load lower bounds: {count}")
    return count




def add_precedence_inequalities(model, x, P, idx, n, active=True, use_conservative=True):
    """
    Precedence Constraints 
    Returns:
        (count_var1, count_var2): Numero vincoli aggiunti
    """
    if not active:
        print("  Precedence inequalities disattivate")
        return 0, 0
    
    print("  Precedence inequalities (Ruland & Rodin) - CONSERVATIVE MODE...")
    
    count_var1, count_var2 = 0, 0
    #Solo sottoinsiemi minimali
    if use_conservative:
        
        for i in P:
            delivery = n + i
            
            
            # VARIANTE 1: S = {0, delivery}
            # Condizione: deposito iniziale + delivery
           
            S_var1 = {0, delivery}
            
            # Archi uscenti da S
            outgoing = [(u, v) for u, v in idx if u in S_var1 and v not in S_var1]
            
            # Aggiungi vincolo solo se ci sono almeno 3 archi uscenti possibili
            if len(outgoing) >= 3:
                model.addConstr(
                    quicksum(x[u, v] for u, v in outgoing) >= 3,
                    name=f"VI_prec_cons1_req{i}"
                )
                count_var1 += 1
            
        
            # VARIANTE 2: S = {pickup, 2n+1}
            # Condizione: pickup + deposito finale, ma NO deposito iniziale e NO delivery
           
            S_var2 = {i, 2*n + 1}
            
            # Archi entranti in S
            incoming = [(u, v) for u, v in idx if u not in S_var2 and v in S_var2]
            
            # Aggiungi vincolo solo se ci sono almeno 3 archi entranti possibili
            if len(incoming) >= 3:
                model.addConstr(
                    quicksum(x[u, v] for u, v in incoming) >= 3,
                    name=f"VI_prec_cons2_req{i}"
                )
                count_var2 += 1
        
        print(f"    → Variante 1 (S = {{0, n+i}}): {count_var1}")
        print(f"    → Variante 2 (S = {{i, 2n+1}}): {count_var2}")
        print(f"    → Totale: {count_var1 + count_var2} vincoli (modalità conservativa)")
    
    else:
    
        
        # [Implementazione originale qui se necessario in futuro]
        # Per ora, non implementata per evitare problemi
        
        pass
    
    return count_var1, count_var2



def add_infeasible_path_constraints(model, x, P, idx, t, s, T, n, 
                                     max_path_length=3, active=True):
    """
    Infeasible Path Constraints 
    
    Returns:
        (count_paths, count_constraints): Numero percorsi infeasibili trovati e vincoli aggiunti
    """
    if not active:
        print("  Infeasible path constraints disattivate")
        return 0, 0
    
    print(f"  Infeasible path constraints (max intermediate nodes: {max_path_length})...")
    
    from itertools import permutations, product
    
    count_paths = 0
    count_constraints = 0
    
    # Nodi disponibili come intermedi (esclusi depositi)
    intermediate_nodes = list(range(1, 2*n+1))
    
    for i in P:
        delivery = n + i
        max_ride_time = T[i]
        
       
        # CASO p=1: Arco diretto (i → n+i)
       
        # Questa è la situazione più semplice: percorso diretto
        # Se troppo lungo, andrebbe eliminato in preprocessing
        # Ma per completezza, aggiungiamo inequality
        
        if (i, delivery) in idx:
            direct_duration = t[i][delivery] + s[i]
            
            if direct_duration > max_ride_time:
                # x[i, n+i] ≤ 0  (equivalente a eliminare l'arco)
                model.addConstr(
                    x[i, delivery] == 0,
                    name=f"VI_infeas_direct_{i}_{delivery}"
                )
                count_paths += 1
                count_constraints += 1
        
      
        # CASO p≥2: Percorsi con nodi intermedi

        # Enumera percorsi con 1, 2, ..., max_path_length nodi intermedi
        
        for num_intermediate in range(1, max_path_length + 1):
            # Nodi intermedi disponibili (escludi i e n+i)
            available = [node for node in intermediate_nodes 
                        if node != i and node != delivery]
            
            if len(available) < num_intermediate:
                continue
            
            # Genera tutte le permutazioni di lunghezza num_intermediate
            for intermediate_sequence in permutations(available, num_intermediate):
                # Costruisci il percorso: i → k₁ → k₂ → ... → kₚ → n+i
                path = [i] + list(intermediate_sequence) + [delivery]
                
                # Verifica che tutti gli archi esistano
                path_arcs = [(path[j], path[j+1]) for j in range(len(path)-1)]
                if not all(arc in idx for arc in path_arcs):
                    continue  # Salta se qualche arco non esiste
                
                # Calcola durata totale del percorso
                total_duration = 0
                for j in range(len(path)-1):
                    total_duration += t[path[j]][path[j+1]]
                    if j < len(path)-1:  # Aggiungi service time ai nodi intermedi
                        total_duration += s[path[j+1]] if path[j+1] != delivery else 0
                
                # Se il percorso viola il max ride time
                if total_duration > max_ride_time:
                    # Aggiungi inequality: Σ x[arc] ≤ p-1
                    p = len(path_arcs)  # Numero di archi
                    
                    model.addConstr(
                        quicksum(x[arc] for arc in path_arcs) <= p - 1,
                        name=f"VI_infeas_path_{i}_{num_intermediate}_{count_paths}"
                    )
                    count_paths += 1
                    count_constraints += 1
    
    print(f"  Percorsi infeasibili identificati: {count_paths}")
    print(f"Vincoli aggiunti: {count_constraints}")
    
    if count_constraints > 5000:
        print(f"  Molti vincoli generati ({count_constraints})")
        print(f" Considera di ridurre max_path_length (attuale: {max_path_length})")
    
    return count_paths, count_constraints



# FUNZIONE MASTER


def add_all_valid_inequalities(model, variables, data, config=None):
    """
    Aggiunge tutte le famiglie di valid inequalities al modello.
    
    Returns:
        stats: Dict con statistiche sui vincoli aggiunti
    """
    if config is None:
        config = {
            'time_bounds': False,
            'load_bounds': False,
            'precedence': False, #{'max_subset_size': 5}  # Regola se necessario
            'infeasible_paths':False # {'max_path_length': 2}
            # Aggiungerai qui altre famiglie in futuro
        }
    
    print("\n" + "="*70)
    print("AGGIUNTA VALID INEQUALITIES")
    print("="*70)
    
    stats = {}
    
    # Famiglia 1: Time Bounds (25)-(26)
    if config.get('time_bounds', True):
        lb, ub = add_time_bounds_inequalities(
            model=model,
            x=variables['x'],
            B=variables['B'],
            V=data['V'],
            idx=data['idx'],
            e=data['e'],
            l=data['l'],
            s=data['s'],
            t=data['t'],
            n=data['n'],
            active=True
        )
        stats['time_bounds'] = {'lower': lb, 'upper': ub}
    
    # Famiglia 2: Load Bounds 
    if config.get('load_bounds', True):
        count = add_load_bounds_inequalities(
            model=model,
            x=variables['x'],
            Q_var=variables['Q_var'],
            V=data['V'],
            idx=data['idx'],
            q=data['q'],
            n=data['n'],
            active=True
        )
        stats['load_bounds'] = {'count': count}
    

    # Famiglia 4: Infeasible Path Constraints (
    if config.get('infeasible_paths', True):
        # Parametro configurabile
        path_config = config.get('infeasible_paths')
        if isinstance(path_config, dict):
            max_len = path_config.get('max_path_length', 2)  # Default: 2 nodi intermedi
        else:
            max_len = 2
        
        paths, constrs = add_infeasible_path_constraints(
            model=model,
            x=variables['x'],
            P=data['P'],
            idx=data['idx'],
            t=data['t'],
            s=data['s'],
            T=data['T'],  # <-- AGGIUNGI T al data dict
            n=data['n'],
            max_path_length=max_len,
            active=True
        )
        stats['infeasible_paths'] = {'paths': paths, 'constraints': constrs}


    # 
    
    total = sum(
        sum(v.values()) if isinstance(v, dict) else v 
        for v in stats.values()
    )
    
    print("="*70)
    print(f"TOTALE VALID INEQUALITIES AGGIUNTE: {total}")
    print("="*70 + "\n")
    
    return stats
