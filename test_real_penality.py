import csv
import time 
import os

from readREAL import extract_darp_data
from darpMulti_TW import*

def test(instances_folder="router_bus_main/dati_conv", output_csv="risultati/risultati_real_TW_GAP"):
    with open(output_csv, mode='w', newline='') as file:    #evito righe vuote co newline
        writer = csv.writer(file)
        writer.writerow(["istanza", "num_richieste", "richieste_servite", "tempo_sec", "soluzione_trovata", "gap"])  

        for filename in os.listdir(instances_folder): #scorro tutte le istanze nella cartella in input
            if filename.endswith(".json"):
                instance_path = os.path.join(instances_folder, filename)
                print(f"\n Risolvendo istanza: {filename}")
                #conversione dei dati (potrei farlo separatamente)
                darp_data= extract_darp_data(instance_path)  #come penalità sto usando valore costanete per ogni nodo


                start_time = time.time() #faccio partire il tempo prima di avviare la risoluzione del modello
                solution, gap= solve_darp(**darp_data) 
                end_time = time.time() #stop tempo
                timetot = end_time - start_time #calcolo tempo di esecuzione

                if solution: #se la soluzione viene trovata
                    x_solution = {k: v for k, v in solution[0].items() if v is not None and v > 0.5}  #archi attivi (questo poi eliminato)
                    solution_y = solution[6]
                    writer.writerow([
                        filename,
                        darp_data['n'],  #n= numero richieste 
                        sum(solution_y.values()),  #numero richieste servite
                        round(timetot, 2), #con due cifre
                        True,
                        round( gap *100, 2) if gap is not None else 0.0 #gap in percenutale
                    ])
                else:  #se non trovo la soluzione 
                    writer.writerow([
                        filename,
                        "-",       # non disponibile
                        "-",       # non disponibile
                        round(timetot, 2),
                        False,
                        round( gap *100, 2) if gap is not None else "-"
                    ])


def main():
    print("Avvio test su tutte le istanze...")
    test("router_bus_main/dati_conv", "risultati/risultati_real_TW_GAP.csv")



if __name__== '__main__':
    main()