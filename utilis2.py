
import numpy as np
import copy
import random

def insert_two(xs: list[int], val: int, i: int = 0):
    """inserisce un nuovo valore in una strinaga"""
    if len(xs) == 0:
        xs.append(val)
        return xs
    ls : list[int] = xs[:i]
    rs : list[int] = xs[i:]
    return ls + [val] + rs

def Insert(xs: list[int], n: int, val: int, h: int, k: int, v: int, w: int):
    """inserisce quattro nuovi vaori nella stringa
    mantenedno indici originali"""
    start, end = xs[0], xs[-1] # considero i due depositi che sono in prima e ultima posizione 
    middle= xs[1:-1]

    middle = insert_two(middle, val , h)
    middle = insert_two(middle, val + int(n), k+1)
    middle = insert_two(middle, val + int(n / 2), v+2)
    middle = insert_two(middle, val + int(3*n / 2), w+3)
    return  [start] + middle + [end]


#seleziono le L soluzioni più promettenti
def select_best(S, L, f_eur):
    S_sorted= sorted(S, key=f_eur) #gli ordina dal più gtade al più piccoli
    return  S_sorted[:L]   #prendo quelli con valore minore




#definizione delle funzioni euristiche
def f_eur1PRIMA(s, Time,i):
    """s è la sequenza di nodi valuatat
    i è il paziente
    Time[i] è il dizionario con i tempi relativi alle sequenze del paziente i
    calcolo orario fine del percorso(quando arrivo al deposito finale)
    """
    # last_node =s[-1] #ultimo nodo della sequenza  ORA HO INSERITOI DEPOSITI =ULTIMO PERò IL TEMPO NON DOVREBBE CAMBIARE  i tempi sono zero per i depositi 
    #last_node_pos=s.index(last_node)
    last_node_pos= len(s)-1
    t= Time[i][tuple(s)] 
    total_travel_time=t[last_node_pos]  
    return total_travel_time


def f_eur1(r,t_matrix):
    """modificata per essere più coerente con la funzione obbiettivo
    somma dei tempi delle tratte"""
    total_time = 0
    for i in range(len(r) - 1):
        total_time += t_matrix[r[i]][r[i+1]]
    return total_time

def f_eur2(n,r,Time,iteration,t_matrix, HOSP, D, l, e, alpha=1.0, beta=1.0):
    """proviamo a definirla uguale alla funzione obbiettivo"""
    #estraggo la sequenza dei tempi
    t=Time[iteration][tuple(r)]


# tempo di attesa ai nodi ospedali
    
    WP=np.zeros(2*n+1)
    total_wating_time=0
    hospital_node_seq=[node for node in r if node in HOSP]  #seleziono i nodi ospedali che sono in r (non i loro indici)
    for node in hospital_node_seq:
        node_pos=r.index(node)
        if node in D:
            WP[node]= max(0, l[node]- t[node_pos])
        else:
            WP[node]=max(0, t[node_pos]- e[node])
        total_wating_time+= WP[node]


    #tempo totale delle tratte
    total_time = 0
    for i in range(len(r) - 1):
        total_time += t_matrix[r[i]][r[i+1]]

    #costo totale della sequenza
    total_cost= alpha * total_wating_time + beta* total_time
    return total_cost




#verifico se soluzione è feasible
def feasible(r, serv, t_matrix,T, n, e , l, P, D, q, Q_max, debug=None):
    """ r è la sequenza che volgiamo verificae se è feasible
    t_matrix è la matrice dei tempi
    t_j è l'orario di arrivo al nodo
    T orario massimo
    e, l sono inizio e fine delle finestre temporali
    serv tempi di servizio a ogni nodo
    q carico per ogni nodo
    """
    m=len(r)
    t=np.zeros(m+1)
    Q=np.zeros(m+1)
    ld={}
    
    for j in range(m): #su tussi i nodi in r in {0,...,m-1} indici dei nodo nella sequenza r  FORSE QUI DOVREI ESCLUDERE LO ZERO VEDI COSA SUCCEDE
        
        #calcolo tempo di arrivo ai nodi nella sequenza r
        t[0]=0 #se il primo nodo è sempre il depositi faccio partire il tempo da zero (posso no mettere 0 ma tipo le sei del mattino pensando che il pulmino parta a quell)
        prev_node = r[j-1] if j > 1 else 0
        curr_node=r[j]
       
        
        if j>0:
            t[j]= max(t[j-1] , e[prev_node])+ serv[prev_node]+t_matrix[prev_node][curr_node]  #PROVO AGGIUNGERE TEMPO DI SERVIZIO 
        if t[j]> l[curr_node]: #violazione finestra temporale
            if debug:
                print(f"ERRORE: Violazione time window al nodo {curr_node}")
                print(f"  Arrivo: {t[j]:.2f}, Chiusura: {l[curr_node]}")
            return False, None  #l'inserimento non è feasible

        #tempo massimo di percorrenza
        pickup_node_seq=[node for node in r if node in P] #seleziono i nodi in r che sono nodi pickup ({1,...,n})
        for p_node in pickup_node_seq:
            d_node= p_node+n #corrispondente delivery {n+1,...,2n}
    
            # Trova le posizioni nella sequenza
            pickup_pos = r.index(p_node)  # corrispettiva posizione occupata in r 
            delivery_pos = r.index(d_node)  # posizione in r 
            
            ld[d_node]= min (l[d_node], max(t[pickup_pos], e[p_node])+ serv[p_node]+ T[p_node]) #last possible delivery time of costumers r_j (def solo per i delivery node)
    
            if t[delivery_pos] > ld[d_node]:
                if debug:
                    print(f"ERRORE: Violazione ride time per richiesta {p_node}")
                return False, None #violazione del tempo mmassimo di percorrenza
   
        #verifichiamo la capacità del veicolo
        Q[0]=0
        Q[j]=Q[j-1]+ q[curr_node] 
        if Q[j]<0 or Q[j]>Q_max:
            if debug:
                print(f"ERRORE: Violazione capacità al nodo {curr_node}")
                print(f"  Carico: {Q[j]}, Max: {Q_max}")
            return False, None
    return True, t


#definisco la funzione costo finale
def C(n,r,t,t_matrix, HOSP, D, l, e, scart, alpha=1.0, beta=1.0):
    """r è la sequenza che volgio valutare
    t è il tempo di arrivo ai nodi
    scart: insieme pazienti scartati
    """
    #calcolo la somam del tempo di attesa ai nodi ospedali
    
    WP=np.zeros(2*n+1)
    total_wating_time=0
    hospital_node_seq=[node for node in r if node in HOSP]  #seleziono i nodi ospedali che sono in r (non i loro indici)
    for node in hospital_node_seq:
        node_pos=r.index(node)
        if node in D:
            WP[node]= max(0, l[node]- t[node_pos])
        else:
            WP[node]=max(0, t[node_pos]- e[node])
        total_wating_time+= WP[node]

    

    #tempo totale delle tratte
    total_time = 0
    for i in range(len(r) - 1):
        total_time += t_matrix[r[i]][r[i+1]]

    
    penality=2000

    #costo totale della sequenza
    total_cost= alpha * total_wating_time + beta* total_time +penality*len(scart)
    return total_cost



def order_patients_by_flexibility(PHOME, n, e, l, t_matrix):
    """Ordina i pazienti per flessibilità delle time window dei nodi casa"""
    flexibility = {}
    for i in PHOME:
        # Solo nodi casa
        pickup_home_flex = l[i] - e[i]
        delivery_home_flex = l[i+3*n//2] - e[i+3*n//2]
        
        avg_flexibility = (pickup_home_flex + delivery_home_flex) / 2
        flexibility[i] = avg_flexibility
    
    # Ordina: meno flessibili prima /con vederse->dopo
    return sorted(PHOME, key=lambda x: flexibility[x], reverse= True)



def order_randomly(PHOME, seed=42):
    """Ordine casuale """
    random.seed(seed)
    shuffled = list(PHOME)
    random.shuffle(shuffled)
    return shuffled


def feasible_fast(r, serv, t_matrix, T, n, e, l, P, D, q, Q_max):
    """
    Versione di feasible con EARLY EXIT (si ferma appena trova una violazione)
    """
    m = len(r)

    pickup_positions = {}
    delivery_positions = {}
    
    for idx, node in enumerate(r):
        if node in P:
            pickup_positions[node] = idx
        elif node in D:
            delivery_positions[node] = idx
    
    # CONTROLLO 2: Capacità e tempi (insieme, un solo loop)
    t = np.zeros(m)   #t[j] tempod i arrivo al nodo j
    Q = np.zeros(m)   #Q[j] carico dopo aver visitato nodo j
    ld = {}
    
    Q[0] = 0 
    t[0] = 0
    
    for j in range(1, m):
        prev_node = r[j-1]
        curr_node = r[j]
        
        # Calcola tempo arrivo
        t[j] = max(t[j-1], e[prev_node]) + serv[prev_node] + t_matrix[prev_node][curr_node]
        
        # EARLY EXIT: Violazione time window
        if t[j] > l[curr_node]:
            return False, None
        
        # Calcola carico
        Q[j] = Q[j-1] + q[curr_node]
        
        # EARLY EXIT: Violazione capacità
        if Q[j] < 0 or Q[j] > Q_max:
            return False, None
    
    # CONTROLLO 3: Ride time (solo per delivery nodes)
    for p_node in pickup_positions.keys():
        d_node = p_node + n
        
        pickup_pos = pickup_positions[p_node]
        delivery_pos = delivery_positions[d_node]
        
        ld[d_node] = min(l[d_node], max(t[pickup_pos], e[p_node]) + serv[p_node] + T[p_node]) #ultimo orario possibile per il delivery
        
        # EARLY EXIT: Violazione ride time
        if t[delivery_pos] > ld[d_node]:
            return False, None
    
    return True, t





def order_biased_random(PHOME, n, e, l, t_matrix, seed=42):
    """
    Ordinamento casuale pesato dalla flessibilità:
    - solo nodi casa (gli ospedali hanno sempre 60 min)
    - Pazienti con time window strette nei rispettivi nodi casa sono più critici
    """
    import random
    random.seed(seed)
    
    # Calcola flessibilità SOLO per nodi casa
    flexibility = {}
    for i in PHOME:
        # PICKUP OUTBOUND (casa-ospedale)
        pickup_home_flex = l[i] - e[i]  
        
        # DELIVERY INBOUND (ospedale-casa)  
        delivery_home_flex = l[i+3*n//2] - e[i+3*n//2]  
        
        # non considero i nodi ospedale (i+n e i+n//2) perché sempre 60 min
        
        # Media 
        avg_flexibility = (pickup_home_flex + delivery_home_flex) / 2
        flexibility[i] = avg_flexibility
    
    # Calcola "peso" per ogni paziente
    max_flex = max(flexibility.values())
    weights = {}
    for i in PHOME:
        # Meno flessibile → peso alto
        weights[i] = max_flex - flexibility[i] + 1
    
    # Estrai pazienti uno alla volta con probabilità proporzionale al peso
    ordered = []
    remaining = list(PHOME)
    
    while remaining:
        current_weights = [weights[p] for p in remaining]
        chosen = random.choices(remaining, weights=current_weights, k=1)[0]
        ordered.append(chosen)
        remaining.remove(chosen)
    #con reverse meno flessiili dopo
    return ordered.reverse()