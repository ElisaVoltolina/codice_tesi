from darp import*
from parameters import*
from utils import save_solution


solution= solve_darp(
    V=V,
    PHOSP=PHOSP,  # Pickup nodes
    DHOSP=DHOSP,  # Delivery nodes
    HOSP=HOSP,  #tutti gli ospedali!! 
    PHOME=PHOME, #pickup home
    P=P,  # Pickup nodes
    D=D,  # Delivery nodes
    PD=PD,  #unione di P e D
    idx=idx, #archi esistenti
    n=n, # numero richieste
    t=t,  # Matrice tempi
    s=s,  # Tempi di servizio
    e=e,  # Time window inizio
    l=l,  # Time window fine
    T=T,  # Tempo massimo corsa
    q=q,  # Capacità occupata/rilasciata
    Q=Q  # Capacità totale veicolo
)


x=solution[0]
#estraggo la soluzione (solo gli archi percorsi)
x_solution = {k: v for k, v in solution[0].items() if v is not None and v > 0.5}

A= solution[1]
A_sorted = sorted(A.items(), key=lambda x: x[1])

B= solution[2]    #QUI C'è QUALCOSA DI SBAGLIATO
B_sorted= sorted(B.items(), key= lambda x: x[1] )

# Salva su file
save_solution(x_solution, A_sorted, B_sorted, "soluzione_darp.json")
print("Soluzione salvata!")

print(t)