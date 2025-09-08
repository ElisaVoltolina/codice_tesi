import json
import os

def extract_darp_data(json_file_path):
    """
    Estrae i dati necessari per il modello solve_darp dal file JSON.
    
    Args:
        json_file_path (str): Percorso del file JSON
        
    Returns:
        dict: Dizionario contenente tutti i parametri estratti
    """
    
    # Legge il file JSON
    with open(json_file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    # Estrae i valori 
    extracted_data = {
        'V': data['V'],                 # Nodi del grafo
        'PHOSP': data['PHOSP'],         # Nodi pickup ospedale
        'DHOSP': data['DHOSP'],         # Nodi delivery ospedale
        'HOSP': data['HOSP'],           # Nodi ospedale (pickup + delivery)
        'PHOME': data['PHOME'],         # Nodi pickup casa
        'P': data['P'],                 # Tutti i nodi pickup
        'D': data['D'],                 # Tutti i nodi delivery
        'PD': data['PD'],               # Tutti i nodi pickup + delivery
        'idx': [tuple(pair) for pair in data['idx']],             # Indici delle coppie di nodi (riconverto gli elementi in tuple)
        'n': data['n'],                 # Numero delle richieste
        't': data['t'],                 # Matrice dei tempi di viaggio
        's': data['s'],                 # Durate dei servizi ai nodi
        'e': data['e'],                 # Earliest time windows
        'l': data['l'],                 # Latest time windows
        'T': {i: data['T'][i-1] for i in range(1, data['n']+1)},        # Tempo passimo (aggiusto la numerazione delgi indici)
        'q': data['q'],                 # Domande ai nodi
        'Q': data['Q']                  # Capacità del veicolo
    }
    
    return extracted_data
