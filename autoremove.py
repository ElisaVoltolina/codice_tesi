from darp import*
from utils import save_solution, find_original_ids_from_new_indices
from readistanceREMOVE import*
import gurobipy as GRB
import re
import os

def parse_ilp_file(ilp_filename="model_infeasible.ilp", P=None , D=None, n=None): 
    """
    Legge e analizza il file ILP generato da Gurobi per identificare
    i nodi problematici che causano l'infattibilità e identifica le coppie di nodi
    
    Args:
        ilp_filename: Nome del file ILP generato da Gurobi
        P: array dei nodi pickup
        D: array nodi delivery
        n: numero richieste
    
    Returns:
        list: Lista di tuple (pickup_id, delivery_id) dei nodi problematici
    """
    problematic_pairs = []
    
    if not os.path.exists(ilp_filename): #quando non trova il file
        print(f"File {ilp_filename} non trovato!")
        return problematic_pairs
    
    print(f"Analizzando il file ILP: {ilp_filename}")
    
    with open(ilp_filename, 'r') as f: #apro il file in un a stringa
        content = f.read()

    #if P is None or D is None or n is None:
        #print("!!!!!!!!! Parametri P, D, n non forniti alla funzione parse_ilp_file")
        #return problematic_pairs

    # insieme delle richieste problematiche
    problematic_requests = set()
    
    
    #in teoria non dovrei avere altri vinvoli infattibili oltre a questi

    # Pattern per trovare i nodi nelle variabili B[x] e L[x] (creo due espressioni regolari)
    b_pattern = r'B\[(\d+)\]'
    l_pattern = r'L\[(\d+)\]'
    
    # Trova tutti i nodi nelle variabili B e L(trovo i numeri)
    b_matches = re.findall(b_pattern, content)
    l_matches = re.findall(l_pattern, content)
    

    

    all_nodes = set()  #insieme con tutti i numeri dei nodi che leggo
    for match in b_matches + l_matches:
        node_id= int(match)
        all_nodes.add(node_id)
        # creo le coppie di nodi da escludere (questi hanno la "nuova" numerazione)
        if node_id in P:
            pickup_id = node_id
            delivery_id = pickup_id + n
            problematic_requests.add((pickup_id, delivery_id))
            print(f"Nodo pickup {pickup_id} trovato -> richiesta ({pickup_id}, {delivery_id})")
        if node_id in D:
            delivery_id = node_id
            pickup_id = delivery_id - n
            problematic_requests.add((pickup_id, delivery_id))
            print(f"Nodo delivery {delivery_id} trovato -> richiesta ({pickup_id}, {delivery_id})")


   
    print(f"Nodi coinvolti nei vincoli in conflitto: {sorted(all_nodes)}") #li restituisco ordinati
    
   # Converto il set in lista rimuovendo duplicati
    problematic_pairs = list(problematic_requests)
    
    # Rimuovi duplicati
    problematic_pairs = list(set(problematic_pairs))
    
    print(f"Coppie problematiche identificate: {problematic_pairs}")
    return problematic_pairs #nuova numerazione

def solve_with_ilp_analysis(instance_filename, max_iterations=10):
    """
    Risolve il problema DARP usando l'analisi del file ILP per identificare
    i nodi problematici in modo preciso.
    
    Args:
        instance_filename: Nome del file dell'istanza
        max_iterations: Numero massimo di iterazioni
    
    Returns:
        tuple: (solution, final_exclude_requests, darp_data)
    """
    
    # Inizializza la lista dei nodi da escludere
    exclude_requests = []
    
    # Carica l'istanza originale
    nodes_data, travel_times, route_time, capacity = parse_pdptw_instance(instance_filename)  #legge l'stanza (qui potrei calcolarla in precedenza e caricare un file)
    
    iteration = 0
    while iteration < max_iterations:
        print(f"\n{'='*60}")
        print(f"ITERAZIONE {iteration + 1}")
        print(f"{'='*60}")
        
        print(f"Nodi attualmente esclusi: {exclude_requests}")
        
        # Crea i dati DARP con le esclusioni attuali
        darp_data = create_darp_data(nodes_data, travel_times, route_time, capacity, exclude_requests)
        #P = darp_data['P']
        
        # Risolvi il problema
        try:
            solution_result = solve_darp(**darp_data)
            
            # Controlla se la soluzione è stata trovata
            if solution_result is not None and len(solution_result) > 0:
                solution = solution_result[0] #valori della variabile decisionale x
                
                #estraggo solo archi attivi 
                x_solution = {k: v for k, v in solution.items() if v is not None and v > 0.5}
                
                if x_solution:
                    print(f"\n SOLUZIONE TROVATA dopo {iteration + 1} iterazioni!")
                    print(f"Nodi esclusi finali: {exclude_requests}")
                    print(f"Numero di archi nella soluzione: {len(x_solution)}")
                    
                    # Pulisci il file ILP se esiste (lo rimuovo perchè ho trovato una soluzione)
                    if os.path.exists("model_infeasible.ilp"):
                        os.remove("model_infeasible.ilp")
                        print("File ILP temporaneo rimosso")
                    
                    return solution_result, exclude_requests, darp_data
                else:
                    print(" Soluzione vuota - modello probabilmente infattibile")
            else:
                print(" Nessuna soluzione trovata - modello infattibile")
                
        except Exception as e:
            print(f" Errore durante la risoluzione: {e}")
            
        # Se arriviamo qui, il modello è infattibile
        print(" Modello infattibile - Analisi del file ILP...")
        
        # Aspetta che il file ILP sia stato generato
        ilp_file = "model_infeasible.ilp" #file generato del modello con i vincoli che rendono infattibile il modello
        if not os.path.exists(ilp_file): # controllo che il file venga generato (se no esco del ciclo)
            print(f"File ILP {ilp_file} non trovato!")
            print("Assicurati che il modello generi il file ILP quando è infattibile")
            break
        



        # Analizza il file ILP per identificare i nodi problematici
        problematic_pairs = parse_ilp_file(ilp_file, P= darp_data['P'], D= darp_data['D'], n= darp_data['n']) # chiamo qui la funzione precedente che mi restituisci le coppie di nodi problematiche (nella nuova numerazione)
        
        if not problematic_pairs:
            print(" Nessun nodo problematico identificato dal file ILP")
            break
           

        # Converti i nodi problematici agli indici originali (nell prima iterazione non è necessario)
        new_exclusions = []
        for pickup_idx, delivery_idx in problematic_pairs:  #per ogni coppia da escludere
            if iteration == 0:
                # Prima iterazione: gli indici sono già quelli originali
                print(f" Prima iterazione - Nodo problematico: {pickup_idx}->{delivery_idx} (già indici originali)")
                new_exclusions.append((pickup_idx, delivery_idx))
            else:
                # Iterazioni successive: serve la conversione agli indici originali
                try:
                    original_ids = find_original_ids_from_new_indices(
                        instance_filename, pickup_idx, delivery_idx, exclude_requests
                    )
                    new_exclusions.append(original_ids)
                    print(f" Nodo problematico: {pickup_idx}->{delivery_idx} (originale: {original_ids})")
                except Exception as e:
                    print(f" Errore nella conversione degli indici: {e}")
                    # Fallback: usa gli indici attuali se la conversione fallisce
                    print(f"  Usando indici attuali come fallback: ({pickup_idx}, {delivery_idx})")
                    new_exclusions.append((pickup_idx, delivery_idx))
        
        if not new_exclusions:
            print(" Impossibile identificare nodi da escludere - interruzione")
            break
        
        # Aggiungi i nuovi nodi da escludere
        exclude_requests.extend(new_exclusions)
        
        # Rimuovi duplicati mantenendo l'ordine
        seen = set()
        unique_exclude_requests = []
        for item in exclude_requests:
            if item not in seen:
                seen.add(item)
                unique_exclude_requests.append(item)
        exclude_requests = unique_exclude_requests
        
        print(f" Nodi aggiunti alla lista esclusioni: {new_exclusions}")
        
        iteration += 1
    
    print(f"\n Raggiunto il limite massimo di iterazioni ({max_iterations})")
    print(f"Nodi esclusi: {exclude_requests}")
    return None, exclude_requests, None

def main():
    """
    Funzione principale per eseguire la risoluzione automatica
    usando l'analisi del file ILP.
    Specificando manualmente l'istanza da analizzare
    """
    instance_filename = "ipdptw-n20-ber.txt"
    
    print(" Inizio risoluzione automatica con analisi ILP...")
    print(" Questo metodo usa il file ILP generato da Gurobi per identificare")
    print("    i nodi problematici in modo preciso e deterministico.")
    
    # Esegui la risoluzione con analisi ILP
    solution, final_exclude_requests, darp_data = solve_with_ilp_analysis(instance_filename)
    
    if solution is not None:
        print(f"\n SUCCESSO!")
        print(f" Soluzione trovata con {len(final_exclude_requests)} richieste escluse")
        
        # Estrai la soluzione
        x_solution = {k: v for k, v in solution[0].items() if v is not None and v > 0.5}
        final_exclude_patient=  int(len(final_exclude_requests)) // 2 #numero di pazienti esclusi dal percorso
        served_patients= int(darp_data['n']) // 2    #numero dei pazienti presi in carico


        print(f" Statistiche finali:")
        print(f"   - Numero di archi nella soluzione: {len(x_solution)}")
        print(f"   - Richieste escluse: {final_exclude_requests}")    
        print(f"   - Numero di richieste servite: {darp_data['n']}")    
        
        print(f"   -Numero pazienti escusi del percorso {final_exclude_patient}")
        print(f"   -Numero pazienti presi in carico: {served_patients}")
        
        # Posso salvare la soluzione se necessario
        # save_solution(x_solution, darp_data, "solution_automatic_ilp.txt")
        
        return solution, darp_data
    else:
        print(" Impossibile trovare una soluzione fattibile")
        return None, None

if __name__ == "__main__":
    main()