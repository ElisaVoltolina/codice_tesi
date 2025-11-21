import csv
import time 
import os

from readREAL import extract_darp_data
from euristica_no_scart import*

""" funzioni per testare la funzione euristica e per stampare il confronto tra esatto e euristica"""


def load_exact_results(exact_csv):
    """
    Carica i risultati del modello esatto in un dizionario.
    La chiave è il nome dell'istanza, il valore è un dizionario con tutti i dati.
    """
    exact_data = {}
    with open(exact_csv, mode='r', newline='') as file:
        reader = csv.DictReader(file)
        for row in reader:
            filename = row['istanza']
            exact_data[filename] = {
                'num_richieste': int(row['num_richieste']),
                'richieste_servite': float(row['richieste_servite']),
                'tempo_sec': float(row['tempo_sec']),
                'soluzione_trovata': row['soluzione_trovata'],
                'gap': float(row['gap']),
                'valore_ottimo': float(row['valore ottimo']),
                'lower_bound': float(row['lower bound'])
            }
    return exact_data


def load_heuristic_results(exact_csv):
    """
    Carica i risultati dell'euristica in un dizionario.
    La chiave è il nome dell'istanza, il valore è un dizionario con tutti i dati.
    """
    heuristic_data = {}
    with open(exact_csv, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            filename = row['istanza']
            heuristic_data[filename] = {
                'num_richieste': int(row['num_richieste']),
                'richieste_servite': float(row['richieste_servite_euristica']),
                'tempo_sec': float(row['tempo_sec_euristica']),
                'valore_ottimo': float(row['valore_ottimo_euristica']),
                'num_run': int(row['num_run'])
            }
    return heuristic_data


def confronto(instances_folder="router_bus_main\DATI", exact_results="risultati/risultati_penality_DATI60.csv", heuristic_result="risultati/risultati_EuristicFast.csv", output_csv="risultati/risultati_confronto.csv"):
    """ Stampa confronto risulattai modello esatto e euristica"""

    # Carico i dati dai CSV
    if isinstance(exact_results, str):
        exact_results = load_exact_results(exact_results)
    if isinstance(heuristic_result, str):
        heuristic_result = load_heuristic_results(heuristic_result)

    #exact_result=load_exact_results(exact_results)
    #heuristic_result=load_heuristic_results(heuristic_result)

    # Leggo le istanze effettivamente presenti nella cartella
    instances_in_folder = set(
        f for f in os.listdir(instances_folder)
        if f.endswith(".json")
    )

   

        # Apro il file di output
    with open(output_csv, mode='w', newline='') as file:
        fieldnames = [
            'istanza',
            'num_richieste',
            'richieste_servite_exact',
            'valore_ottimo_exact',
            'lower_bound',
            'gap_exact',
            'tempo_exact',
            #valori euristica
            'richieste_servite_heuristic',
            'valore_ottimo_heuristic',
            'gap_heuristic',
            'tempo_heuristic',
            'numero_run'
        ]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        # ciclo su tutte le istanze presenti nei risultati esatti
        for filename in instances_in_folder:
            if filename in exact_results and filename in heuristic_result:
                exact = exact_results[filename]
                heuristic = heuristic_result[filename]

                lower_bound=exact['lower_bound']
                valore_ottimo_her=heuristic['valore_ottimo']


                #calcolo gap euristica
                if lower_bound > 0:
                    gap_euristica = ((valore_ottimo_her - lower_bound) / valore_ottimo_her) * 100
                else:
                    gap_euristica = 0.0


                writer.writerow({
                    'istanza': filename,
                    'num_richieste': exact['num_richieste'],
                    'richieste_servite_exact': exact['richieste_servite'],
                    'valore_ottimo_exact': exact['valore_ottimo'],
                    'lower_bound': exact['lower_bound'],
                    'gap_exact': exact['gap'],
                    'tempo_exact': exact['tempo_sec'],
                    #valori euristica
                    'richieste_servite_heuristic': heuristic['richieste_servite'],
                    'valore_ottimo_heuristic': heuristic['valore_ottimo'],
                    'gap_heuristic': gap_euristica,
                    'tempo_heuristic': heuristic['tempo_sec'],
                    'numero_run': heuristic['num_run']})
            else:
                print(f" Attenzione: istanza {filename} non trovata nei risultati euristici")




def test(instances_folder="router_bus_main/DATI", output_csv="risultati_finali/heuristic_60L5.csv"):
     with open(output_csv, mode='w', newline='') as file:    #evito righe vuote co newline
        writer = csv.writer(file)
        writer.writerow(["istanza", "num_richieste", "richieste_servite_euristica", "tempo_sec_euristica","valore_ottimo_euristica"])  
        
        for filename in os.listdir(instances_folder): #scorro tutte le istanze nella cartella in input
            if filename.endswith(".json"):
                instance_path = os.path.join(instances_folder, filename)
                print(f"\n Risolvendo istanza: {filename}")

                #conversione dei dati (potrei farlo separatamente)
                data_darp= extract_darp_data(instance_path) 

                # Estrai i parametri necessari per l'euristica
                t_matrix= data_darp['t']
                T= data_darp['T']
                n=data_darp['n']
                e= data_darp['e']
                l=data_darp['l']
                PHOME=data_darp['PHOME']
                HOSP= data_darp['HOSP']
                P=data_darp['P']
                D=data_darp['D']
                q=data_darp['q']
                Q_max=data_darp['Q']
                serv= data_darp['s']

                #esecuzione euristica
                start_time = time.time() #faccio partire il tempo prima di avviare la risoluzione del modello
                best_Solution, best_cost, best_scart, num_run=heuristic_multirun(n, PHOME, HOSP, D, l, e, serv, t_matrix, T, P, q, Q_max, time_limit=60)
                end_time = time.time() #stop tempo
                timetot = end_time - start_time #calcolo tempo di esecuzione
                


                # Numero di richieste servite
                richieste_servite_euristica = n - 2*len(best_scart)
                

                writer.writerow([
                    # Dati euristica
                    filename, #nome file
                    n,  #numero totale delle richieste (outbound+ inbound)
                    richieste_servite_euristica, #numero richiest eservie euristica
                    round(timetot, 2),  #tempo esecuzione euristica
                    round(best_cost, 2),  #valore ottimo trovato + penalità esclusione pazienti
                    num_run #numero di run eseguite entro il tempo limite
                ])
                


def main():
    print("Avvio test su tutte le istanze...")
    test(instances_folder="router_bus_main/DATI",output_csv="risultati_finali/heuristic_60L5.csv")
    print("\nTest completati!")
    
    #confronto(instances_folder="router_bus_main\DATI", exact_results="risultati/risultati_penality_DATI60.csv", heuristic_result="risultati/Euristic_timelimit_div_60L5.csv", output_csv="risultati/confronto_timelimit_div_60L5.csv")
    #print("Confronto eseguito")




if __name__== '__main__':
    main()