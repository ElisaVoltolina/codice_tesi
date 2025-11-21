import csv
import time 
import os

from readREAL import extract_darp_data
from euristica_no_scart import*
from darpPenalityStart import*

"""avvio i primi test: modello CON AIUTI+ MULTI RUN con tempo limite UN MINUTO per ogni istanza (anche quele nuove appena generate)
SENZA I VINCOLI IN WINDOW
input folder: DATI
outpunt Folder: risulatati_finali
dati salvati nel fine output:  filename
                        numero richieste totale
                        numero richieste servite in totale (ne conta due per ogni paziente preso in carico)
                        tempo due cifre
                        True se trova la soluzione 
                        gap in percenutale
                        val_ottimo trovato della funzione obbiettivo
                        lower_bound
                     """

def test(instances_folder="router_bus_main/DATI", output_csv="risultati_finali/darpStart60.csv"):
    """ il valore ottimo, il lower bound"""
    if not os.path.exists("risultati_finali"): #creo la cartella se non esiste già
        os.makedirs("risultati_finali")

    with open(output_csv, mode='w', newline='') as file:    #evito righe vuote co newline
        writer = csv.writer(file)
        writer.writerow(["istanza", "num_richieste", "richieste_servite", "tempo_sec", "soluzione_trovata", "gap","valore ottimo", "lower bound"])  

        for filename in os.listdir(instances_folder): #scorro tutte le istanze nella cartella in input
            if filename.endswith(".json"):
                instance_path = os.path.join(instances_folder, filename)
                print(f"\n Risolvendo istanza: {filename}")
                #conversione dei dati (potrei farlo separatamente)
                darp_data= extract_darp_data(instance_path)  #come penalità sto usando valore costanete per ogni nodo

                n=darp_data['n']
                serv=darp_data['s']
                t_matrix=darp_data['t']
                Q_max= darp_data['Q']
                e=darp_data['e']
                l=darp_data['l']
                s=darp_data['s']
                PHOME=darp_data['PHOME']
                P=darp_data['P']
                q=darp_data['q'] 
                HOSP=['HOSP']
                D=darp_data['D']
                T=darp_data['T']

                start_time = time.time() #faccio partire il tempo prima di avviare la risoluzione del modello
                euristic_route,_,_,_= heuristic_multirun(n, PHOME, HOSP, D, l, e, serv, t_matrix,T, P, q, Q_max, time_limit=60)
                solution, gap, val_ottimo, lower_bound= solve_darp(**darp_data,  euristic_solution= euristic_route) 
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
                        round( gap *100, 2) if gap is not None else 0.0, #gap in percenutale
                        val_ottimo,
                        lower_bound
                    ])
                else:  #se non trovo la soluzione 
                    writer.writerow([
                        filename,
                        "-",       # non disponibile
                        "-",       # non disponibile
                        round(timetot, 2),
                        False,
                        round( gap *100, 2) if gap is not None else "-",
                        "-",
                        "-"
                    ])


def main():
    print("Avvio test su tutte le istanze...")
    test("router_bus_main/DATI", "risultati_finali/darpStart60.csv")



if __name__== '__main__':
    main()