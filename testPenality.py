import csv
import time
import os
from readistance import*
from darpPenality import*

#salvo i risultati in file CVS 
def batch_run(instances_folder="gen_instances", output_csv="risultati/risultati_penality1.csv"):
    #if not os.path.exists("risultati"): #creo la cartella se non esiste già
        #os.makedirs("risultati")

    with open(output_csv, mode='w', newline='') as file:    #evito righe vuote co newline
        writer = csv.writer(file)
        writer.writerow(["istanza", "num_richieste", "richieste_esclusi", "archi_attivi", "tempo_sec", "soluzione_trovata"])  

        for filename in os.listdir(instances_folder): #scorro tutte le istanze nella cartella
            if filename.endswith(".txt"):
                instance_path = os.path.join(instances_folder, filename)
                print(f"\n Risolvendo istanza: {filename}")
                #conversione dei dati (potrei farlo separatamente)
                nodes_data, travel_times, route_time, capacity = parse_pdptw_instance(instance_path)
                darp_data = create_darp_data(nodes_data, travel_times, route_time, capacity)

                start_time = time.time() #faccio partire il tempo prima di avviare la risoluzione del modello
                solution= solve_darp(**darp_data) 
                end_time = time.time() #stop tempo
                timetot = end_time - start_time #calcolo tempo di esecuzione

                if solution: #se la soluzione viene trovata
                    x_solution = {k: v for k, v in solution[0].items() if v is not None and v > 0.5}  #archi attivi
                    solution_y = solution[6]
                    writer.writerow([
                        filename,
                        darp_data['n'],  #n= numero richieste servite  ok
                        sum(solution_y.values()),  #numero richieste escluse
                        len(x_solution),   #archi attivi
                        round(timetot, 2), #con due cifre
                        True
                    ])
                else:  #se non trovo la soluzione 
                    writer.writerow([
                        filename,
                        "-",       # non disponibile
                        "-",       # non disponibile
                        "-",       # non disponibile
                        round(timetot, 2),
                        False
                    ])


def main():
    print("Avvio batch test su tutte le istanze...")
    batch_run("gen_instances", "risultati/risultati_penality1.csv")



if __name__== '__main__':
    main()