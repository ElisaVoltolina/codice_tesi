import json
import matplotlib.pyplot as plt
import networkx as nx
from readistanceREMOVE import*

#def save_solution(x_solution, filename):
    # with open(filename, "w") as f:
        #json.dump({f"{i}-{j}": val for (i, j), val in x_solution.items()}, f)
        
import json

def save_solution(x_solution, A_sorted, B_sorted, filename):
    
    data_to_save = {
        "x_solution": {f"{i}-{j}": val for (i, j), val in x_solution.items()},
        "A_sorted": [{str(k): v} for k, v in A_sorted],
        "B_sorted": [{str(k):v} for k,v in B_sorted]
    }

    with open(filename, "w") as f:
        json.dump(data_to_save, f, indent=4)


def load_solution(filename):
    with open(filename, "r") as f:
        raw = json.load(f)
    return {tuple(map(int, key.split("-"))): val for key, val in raw.items()}

def plot_darp_path_auto(x_solution, V, P, D):
    # usa networkx per costruire il grafo
    G = nx.DiGraph()
    G.add_nodes_from(V)
    G.add_edges_from(x_solution.keys())

    pos = nx.spring_layout(G, seed=42)  # Se non hai coordinate

    nx.draw(G, pos, with_labels=True, node_color='lightblue', arrows=True)
    plt.title("Percorso DARP")
    plt.show()



def find_original_ids_from_new_indices(instance_filename, new_pickup_idx, new_delivery_idx, exclude_requests=None):
    """
    Trova gli ID originali corrispondenti ai nuovi indici dopo l'esclusione
    
    Args:
        instance_filename: nome del file dell'istanza
        new_pickup_idx: nuovi indici dei nodi pickup (es. 1, 5)
        new_delivery_idx: nuovi indici dei nodi delivery (es. 9, 13)
        exclude_requests: richieste già escluse
    
    Returns:
        tuple: (original_pickup_id, original_delivery_id)
    """
    if exclude_requests is None:
        exclude_requests = []
    
    # Carica l'istanza
    nodes_data, travel_times, route_time, capacity = parse_pdptw_instance(instance_filename)
    
    # Applica le esclusioni
    excluded_node_ids = set()
    for pickup_id, delivery_id in exclude_requests:
        excluded_node_ids.add(pickup_id)
        excluded_node_ids.add(delivery_id)
    
    # Filtra i nodi
    pickup_nodes = [node for node in nodes_data 
                   if node['demand'] > 0 and node['id'] not in excluded_node_ids]
    delivery_nodes = [node for node in nodes_data 
                     if node['demand'] < 0 and node['id'] not in excluded_node_ids]
    
    n = len(pickup_nodes)
    
    # Trova l'ID originale per il pickup
    if 1 <= new_pickup_idx <= n:
        original_pickup_id = pickup_nodes[new_pickup_idx - 1]['id']
    else:
        raise ValueError(f"Indice pickup {new_pickup_idx} non valido (deve essere tra 1 e {n})")
    
    # Trova l'ID originale per il delivery
    if (n + 1) <= new_delivery_idx <= (2 * n):
        delivery_array_idx = new_delivery_idx - n - 1
        original_delivery_id = delivery_nodes[delivery_array_idx]['id']
    else:
        raise ValueError(f"Indice delivery {new_delivery_idx} non valido (deve essere tra {n+1} e {2*n})")
    
    print(f"Nuovi indici ({new_pickup_idx}, {new_delivery_idx}) -> ID originali ({original_pickup_id}, {original_delivery_id})")
    
    return original_pickup_id, original_delivery_id

 



  


