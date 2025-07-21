import csv
import time
import os
from autoremove import solve_with_ilp_analysis

#salvo i risultati in file CVS 
def batch_run(instances_folder="new_20", output_csv="risultati/risultati_batch2.csv", max_iter=20):
    if not os.path.exists("risultati"): #creo la cartella se non esiste già
        os.makedirs("risultati")

    # Prepara CSV
    with open(output_csv, mode='w', newline='') as file:    #evito righe vuote co newline
        writer = csv.writer(file)
        writer.writerow(["istanza", "num_richieste", "richieste_esclusi", "archi_attivi", "tempo_sec", "soluzione_trovata"])  

        for filename in os.listdir(instances_folder): #scorro tutte le istanze nella cartella
            if filename.endswith(".txt"):
                instance_path = os.path.join(instances_folder, filename)
                print(f"\n Risolvendo istanza: {filename}")

                start_time = time.time() #faccio partire il tempo prima di avviare la risoluzione
                solution, final_exclude_requests, darp_data = solve_with_ilp_analysis(instance_path, max_iterations=max_iter)   
                end_time = time.time() #stop tempo
                timetot = end_time - start_time #calcolo tempo di esecuzione

                if solution: #se la soluzione viene trovata
                    x_solution = {k: v for k, v in solution[0].items() if v is not None and v > 0.5}  #archi attivi
                    writer.writerow([
                        filename,
                        darp_data['n'],  #n= numero richieste servite  ok
                        len(final_exclude_requests),  #numero richieste escluse
                        len(x_solution),   #archi attivi
                        round(timetot, 2), #con due cifre
                        True
                    ])
                else:  #se non trovo la soluzione COSA SUCCEDE(SECODO ME LA TROVA SEMPRE ANHC ESE BANALE)
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
    batch_run("new_20", "risultati/risultati_batch2.csv", max_iter=20)



if __name__== '__main__':
    main()