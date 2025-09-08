from utils import calculate_pair_difficulty

def create_penalty_weights_priority_groups(P, high_priority_nodes, medium_priority_nodes):
    """Esempio 1: Gruppi di priorità
    - high_priority_nodes: lista dei nodi ad alta priorità
    - medium_priority_nodes: lista dei nodi a media priorità  
    - tutti gli altri: bassa priorità
    """
    penalty_weights = {}
    
    for i in P:
        if i in high_priority_nodes:
            penalty_weights[i] = 10000  # Penalità molto alta = massima priorità
        elif i in medium_priority_nodes:
            penalty_weights[i] = 5000   # Penalità media
        else:
            penalty_weights[i] = 1000   # Penalità bassa = minima priorità
            
    return penalty_weights

def create_penalty_weights_by_type(P, PHOME, PHOSP):  
    """Esempio 2: Priorità basata sul tipo di richiesta (do maggiore
    priorità al pickup dall'ospedale)
    """
    penalty_weights = {}
    
    for i in P:
        if i in PHOSP:
            penalty_weights[i] = 15000  # Priorità massima per pickup ospedale
        else:
            penalty_weights[i] = 8000   # Priorità alta per pickup casa
            
    return penalty_weights





def create_penalty_weights_distance_priority(P, distances_from_depot, strategy="far_first", #questa non ha più senso perchè ho messo le distanze zero dal deposito
                                           min_penalty=3000, max_penalty=15000):
    """
    Strategia 1: Priorità basata su distanza dal deposito
    
    Args:
        strategy: "far_first" (lontani prima) o "near_first" (vicini prima)
    """
    penalty_weights = {}
    pickup_distances = {i: distances_from_depot[i] for i in P}
    
    min_dist = min(pickup_distances.values())
    max_dist = max(pickup_distances.values())
    
    print(f"=== STRATEGIA DISTANZA DAL DEPOSITO ({strategy}) ===")
    print(f"Distanza minima: {min_dist:.2f}")
    print(f"Distanza massima: {max_dist:.2f}")
    
    for i in P:
        distance = pickup_distances[i]
        if strategy == "far_first":
                # Più lontano = priorità più alta
                normalized = (distance - min_dist) / (max_dist - min_dist)
        else:  # "near_first"
                # Più vicino = priorità più alta  
                normalized = (max_dist - distance) / (max_dist - min_dist)
            
        penalty_weights[i] = min_penalty + int(normalized * (max_penalty - min_penalty))
    
    return penalty_weights





def create_penalty_weights_pair_difficulty(P, PHOME, n, t, e, l, s, 
                                         min_penalty=3000, max_penalty=15000):  #questa mi sembra la più utile
    """
    Strategia 3: Priorità basata su difficoltà delle coppie outbound-inbound
    Coppie più facili = priorità più alta (più probabilità di essere servite)
    """
    penalty_weights = {}
    
    print(f"=== STRATEGIA DIFFICOLTÀ COPPIE OUTBOUND-INBOUND ===")
    
    # Calcola difficoltà per ogni coppia outbound-inbound
    pair_difficulties = {}
    for i in PHOME:
        difficulty, details = calculate_pair_difficulty(i, n, t, e, l, s)
        pair_difficulties[i] = difficulty
        
        print(f"Coppia {i}-{i+n//2}: difficoltà={difficulty:.1f} "
              f"(dist={details['total_distance']:.1f}, slack={details['time_slack']:.1f})")
    
    # Normalizza e assegna penalty (coppie facili = penalty alta = priorità alta)
    if len(pair_difficulties) > 1:
        min_diff = min(pair_difficulties.values())
        max_diff = max(pair_difficulties.values())
        
        if max_diff > min_diff:
            for i in P:
                if i in PHOME:
                    difficulty = pair_difficulties[i]
                    # Inverti: difficoltà bassa = penalty alta
                    normalized = (max_diff - difficulty) / (max_diff - min_diff)
                    penalty_weights[i] = min_penalty + int(normalized * (max_penalty - min_penalty))
                    # Stessa penalty per il corrispondente inbound
                    penalty_weights[i + n//2] = penalty_weights[i]
                else:
                    # Per nodi che no sono in PHOME ma sono in P
                    penalty_weights[i] = (min_penalty + max_penalty) // 2
        else:
            # Tutte le coppie hanno stessa difficoltà
            penalty_weights = {i: (min_penalty + max_penalty) // 2 for i in P}
    else:
        penalty_weights = {i: (min_penalty + max_penalty) // 2 for i in P}
    
    return penalty_weights





def create_penalty_weights_time_window_based(P, e, l):   #QUESTA SE IN FUTUTO USO TIME WINDOW DIVERISIFICATE
    """
    Esempio 4: 
     Priorità basata sulla rigidità della finestra temporale
    Finestra più stretta = priorità più alta
    """
    penalty_weights = {}
    
    for i in P:
        window_size = l[i] - e[i]
        if window_size <= 30:  # Finestra molto stretta
            penalty_weights[i] = 12000
        elif window_size <= 60:  # Finestra media
            penalty_weights[i] = 8000
        else:  # Finestra ampia
            penalty_weights[i] = 4000
            
    return penalty_weights


def create_penalty_weights_mixed_strategy(P, critical_patients, urgent_appointments, PHOSP):
    """
    Esempio 5: Strategia mista con più criteri
    """
    penalty_weights = {}
    
    for i in P:
        base_penalty = 3000
        
        # Fattore 1: Pazienti critici
        if i in critical_patients:
            base_penalty += 8000
            
        # Fattore 2: Appuntamenti urgenti  
        if i in urgent_appointments:
            base_penalty += 5000
            
        # Fattore 3: Pickup da ospedale
        if i in PHOSP:
            base_penalty += 3000
            
        penalty_weights[i] = base_penalty
        
    return penalty_weights


def esempio_utilizzo():
    
    #QUESTE RIGHE LE DEVO METTERE NEL MAIN2
    # Supponiamo tu abbia questi nodi speciali
    high_priority_requests = [1, 3, 7]  # Richieste ad alta priorità
    medium_priority_requests = [2, 5]   # Richieste a media priorità
    
    # Crea il dizionario di penalità personalizzato
    custom_penalty_weights = create_penalty_weights_priority_groups(
        P, high_priority_requests, medium_priority_requests
    )
    
    return custom_penalty_weights

#solution = solve_darp(V, PHOSP, DHOSP, HOSP, PHOME, P, D, PD, idx, n, t, s, e, l, T, q, Q, 
    #                      penalty_weights=custom_penalty_weights)