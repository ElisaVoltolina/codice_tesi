import numpy as np

def parse_pdptw_instance(filename):
    """
    Legge e parsifica un'istanza PDPTW completa di nodi e archi
    """
    with open(filename, 'r') as file:  #leggo il file riga per riga
        lines = file.readlines()
    
    # Trova le due sezioni (NODES e ADGES)
    nodes_start = None
    edges_start = None
    
    for i, line in enumerate(lines):
        if line.strip() == "NODES":
            nodes_start = i + 1
        elif line.strip() == "EDGES":
            edges_start = i + 1
            break
    
    if nodes_start is None:
        raise ValueError("Sezione NODES non trovata nel file")
    if edges_start is None:
        raise ValueError("Sezione EDGES non trovata nel file")
    
    # Estrai informazioni dall'header (cerco parametri globali)
    route_time = None
    capacity = None
    size = None
    
    for line in lines:
        if line.startswith("ROUTE-TIME:"):
            route_time = int(line.split(":")[1].strip())
        elif line.startswith("CAPACITY:"):
            capacity = int(line.split(":")[1].strip())
        elif line.startswith("SIZE:"):
            size = int(line.split(":")[1].strip())
    
    # Parsifica i nodi  (estraggo le informazioni per ogni nodo)
    nodes_data = []   #dizionario contenente tutte le info sui nodi
    for i in range(nodes_start, edges_start - 1):   #solo le riga nellas ezione nodi
        line = lines[i].strip() #tolgo gli spazi allinizio e alla fine
        if line == "":
            continue
        
        parts = line.split() #ogni riga in una lista
        if len(parts) >= 9:       #mi assicuro che la riga sia completa
            node_id = int(parts[0])
            lat = float(parts[1])
            lon = float(parts[2])
            demand = int(parts[3])
            tw_start = int(parts[4])
            tw_end = int(parts[5])
            service_time = int(parts[6])
            pickup_node = int(parts[7]) if parts[7] != '0' else None
            delivery_node = int(parts[8]) if parts[8] != '0' else None
            
            nodes_data.append({
                'id': node_id,
                'lat': lat,
                'lon': lon,
                'demand': demand,
                'tw_start': tw_start,
                'tw_end': tw_end,
                'service_time': service_time,
                'pickup_node': pickup_node,
                'delivery_node': delivery_node
            })
    
    # Parsifica la matrice dei tempi di viaggio
    travel_times = []  #costriusco la matrice dei tempi
    for i in range(edges_start, len(lines)):
        line = lines[i].strip()
        if line == "EOF" or line == "":
            break
        
        times = list(map(int, line.split()))
        travel_times.append(times)
    
    return nodes_data, travel_times, route_time, capacity

def create_darp_data(nodes_data, travel_times, route_time, capacity):
    """
    Converto i dati dell'istanza nel formato richiesto dal modello DARP
    """
    n_original = len(nodes_data)  
    
    # Trova il deposito (nodo con demand=0 e pickup_node=0)
    depot_node = None
    for node in nodes_data:
        if node['demand'] == 0 and node['pickup_node'] is None:
            depot_node = node
            break
    
    if depot_node is None:
        raise ValueError("Deposito non trovato nell'istanza")
    
    # Separa pickup e delivery nodes   
    pickup_nodes = [node for node in nodes_data if node['demand'] > 0]
    delivery_nodes = [node for node in nodes_data if node['demand'] < 0]
    
    n = len(pickup_nodes)  # Numero di richieste 
    
    # Riordina i nodi: deposito(0), pickup(1...n), delivery(n+1...2n)
    all_nodes = [depot_node] + pickup_nodes + delivery_nodes
    
    # Aggiungo il deposito_finale(2n+1)(copia del deposito iniziale)
    depot_final = depot_node.copy()
    depot_final['id'] = 2*n + 1
    all_nodes.append(depot_final)
    

    #creo i sottoinsiemi di nodi
    V = np.arange(2*n + 2)  # Tutti i nodi: 0, 1...n, n+1...2n, 2n+1
    P = np.arange(1, n + 1)  # Nodi pickup: 1...n
    D = np.arange(n + 1, 2*n + 1)  # Nodi delivery: n+1...2n
    PD = np.concatenate((P,D))
    PHOME = np.arange(1,n//2 +1)    #divisione intera
    PHOSP = np.arange(n//2 +1, n+1)
    DHOME = np.array([i + n for i in PHOSP])  
    DHOSP = np.array([i + n for i in PHOME])  
    HOSP= np.concatenate((PHOSP,DHOSP))

    

    
    # Crea gli archi
    idx=([(0,j) for j in P]+[(i,j) for i in PD for j in PD if i !=j and i!= n+j]+ [(i,2*n+1) for i in D])
    
    # Crea la matrice dei tempi estesa per includere il deposito finale
    print("Costruzione matrice tempi di viaggio...")
    t = {}
    

    #all_node: nodi ordinati 
    #node_data: diszionario contenente tutte le info sui nodi


    # Mappa gli indici originali ai nuovi indici
    original_to_new = {}
    for i, node in enumerate(all_nodes[:-1]):  # Escludi deposito finale temporaneamente (i in all_nodes; node in nodes_data)
        original_to_new[node['id']] = i
    
    # Costruisci la matrice t per tutti i nodi tranne il deposito finale
    for i in range(len(all_nodes) - 1):
        t[i] = {}
        original_i = all_nodes[i]['id']
        for j in range(len(all_nodes) - 1):
            original_j = all_nodes[j]['id']
            t[i][j] = travel_times[original_i][original_j]
    
    #travel_times[original_i][original_j] è la matrice originale (quella nel istanza)
    #t[i][j] è la nuova matrice con indici riassegnati (0=depot, 1=nodo1, ecc.)


    # Aggiungi i tempi per il deposito finale (stesso del deposito iniziale)
    depot_final_idx = 2*n + 1
    t[depot_final_idx] = {}
    
    for i in range(len(all_nodes) - 1):
        # Dal deposito finale agli altri nodi (stesso del deposito iniziale)
        t[depot_final_idx][i] = travel_times[0][all_nodes[i]['id']]
        # Dagli altri nodi al deposito finale (stesso del deposito iniziale)
        if i not in t:
            t[i] = {}
        t[i][depot_final_idx] = travel_times[all_nodes[i]['id']][0]
    
    # Tempo dal deposito finale a se stesso
    t[depot_final_idx][depot_final_idx] = 0
    



    # Estrai i parametri temporali
    e = {}  # Inizio time window
    l = {}  # Fine time window
    s = {}  # Tempo di servizio
    
    for i, node in enumerate(all_nodes):
        e[i] = node['tw_start']
        l[i] = node['tw_end']
        s[i] = node['service_time']
    
    # Estrai le domande
    q = {}
    for i, node in enumerate(all_nodes):
        q[i] = node['demand']
    
    # Tempo massimo di ride per ciascuna richiesta (assumiamo 2 volte il tempo diretto)
    #T = {}
    #for i in P:
        #delivery_node = i + n
        #direct_time = t[i][delivery_node]
        #T[i] = min(direct_time * 2, 60)  # Massimo 60 minuti

    T={i: 2000 for i in range(1, n+1)}    
    
    # Stampa riepilogo
    print(f"\n=== RIEPILOGO ISTANZA ===")
    print(f"Numero richieste: {n}")
    print(f"Nodi totali: {len(all_nodes)}")
    print(f"Capacità veicolo: {capacity}")
    print(f"Orizzonte temporale: {route_time}")
    print(f"Pickup nodes: {P}")
    print(f"Delivery nodes: {D}")
    print(f"Home pickup nodes: {PHOME}")
    print(f"Hospital pickup nodes: {PHOSP}")
    print(f"Hospital delivery nodes: {DHOSP}")
    print(f"Home delivery nodes: {DHOME}")
    print(f"Numero archi: {len(idx)}")
    
    return {
        'V': V,
        'PHOSP': PHOSP,
        'DHOSP': DHOSP,
        'HOSP': HOSP,
        'PHOME': PHOME,
        'P': P,
        'D': D,
        'PD': PD,
        'idx': idx,
        'n': n,
        't': t,
        's': s,
        'e': e,
        'l': l,
        'T': T,
        'q': q,
        'Q': capacity
    }

def save_darp_instance(data, filename):
    """
    Salva l'istanza DARP in formato pickle per riutilizzo
    """
    import pickle
    with open(filename, 'wb') as f:
        pickle.dump(data, f)
    print(f"Istanza salvata in {filename}")

def load_darp_instance(filename):
    """
    Carica un'istanza DARP salvata
    """
    import pickle
    with open(filename, 'rb') as f:
        return pickle.load(f)


