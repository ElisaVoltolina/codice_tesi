
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

    """#tempo totale di percorrenza (tratte+ attesa +servizio)
    last_node=r[-1] #ultimo nodo della sequenza
    last_node_pos=r.index(last_node)
    total_travel_time=t[last_node_pos]"""

    #tempo totale delle tratte
    total_time = 0
    for i in range(len(r) - 1):
        total_time += t_matrix[r[i]][r[i+1]]


    

    #costo totale della sequenza
    total_cost= alpha * total_wating_time + beta* total_time
    return total_cost



"""def f_eur3():
"""



#verifico se soluzione è feasible
def feasible(r, serv, t_matrix,T, n, e , l, P, D, q, Q_max, debug=None):
    """ r è la sequenza che volgiamo verificae se è feasible
    t è la matrice dei tempi
    t_j è l'orario di arrivo al nodo
    T orario massimo
    e, l sono inizio e fine delle finestre temporali
    """
    m=len(r)
    t=np.zeros(m+1)
    Q=np.zeros(m+1)
    ld={}
    #DEBAG
    for node in r:
        if node in D:  # Se è un delivery
            pickup_node = node - n
            if pickup_node not in r:
                if debug:
                    print(f"ERRORE: Delivery {node} senza pickup {pickup_node}")
                return False, None
    # Verifica ordine pickup-delivery per ogni richiesta
    requests_in_route = set()
    for node in r:
        if node in P:
            requests_in_route.add(node)
    
    for req in requests_in_route:
        pickup_pos = r.index(req)
        delivery_pos = r.index(req + n)
        if pickup_pos >= delivery_pos:
            if debug:
                print(f"ERRORE: Pickup {req} (pos {pickup_pos}) non precede delivery {req+n} (pos {delivery_pos})")
            return False, None
#fine debag



    for j in range(m): #su tussi i nodi in r in {0,...,m-1} indici dei nodo nella sequenza r  FORSE QUI DOVREI ESCLUDERE LO ZERO VEDI COSA SUCCEDE
        
        #calcolo tempo di arrivo ai nodi nella sequenza r
        t[0]=0 #se il primo nodo è sempre il depositi faccio partire il tempo da zero (posso no mettere 0 ma tipo le sei del mattino pensando che il pulmino parta a quell)
        prev_node = r[j-1] if j > 1 else 0
        curr_node=r[j]
        
        #if j>0:   qui è senza tempo di servizio
            #t[j]= max(t[j-1], e[prev_node])+t_matrix[prev_node][curr_node] #tempo di arrivo del j-esimo n odo in r
        
        
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
    t è il loro tempo di arrivo
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

    """#tempo totale di percorrenza (tratte+ attesa +servizio)
    last_node=r[-1] #ultimo nodo della sequenza
    last_node_pos=r.index(last_node)
    total_travel_time=t[last_node_pos]"""

    #tempo totale delle tratte
    total_time = 0
    for i in range(len(r) - 1):
        total_time += t_matrix[r[i]][r[i+1]]

    
    penality=2000

    #costo totale della sequenza
    total_cost= alpha * total_wating_time + beta* total_time +penality*len(scart)
    return total_cost



def order_patients_by_flexibility(PHOME,n, e, l, t_matrix):
    """Ordina i pazienti per flessibilità (ampiezza time window)"""
    flexibility = {}
    for i in PHOME:
        # Calcola flessibilità come ampiezza time window
        pickup_flexibility = l[i] - e[i]
        delivery_flexibility = l[i+n] - e[i+n]
        outbound_flexibility = l[i+n//2] - e[i+n//2]
        inbound_flexibility = l[i+3*n//2] - e[i+3*n//2]
        
        # Media delle flessibilità
        avg_flexibility = (pickup_flexibility + delivery_flexibility + 
                         outbound_flexibility + inbound_flexibility) / 4
        flexibility[i] = avg_flexibility
    
    # Ordina per flessibilità decrescente (più flessibili prima)  sorted(PHOME, key=lambda x: flexibility[x], reverse=True)
    #meno flessibili prima
    return sorted(PHOME, key=lambda x: flexibility[x])



def debug_first_patient(paziente_id, n, serv, t_matrix, T, e, l, P, D, q, Q_max):
    """Debug per capire perché il primo paziente non è inseribile"""
    
    print(f"\n{'='*60}")
    print(f"🔍 DEBUG PAZIENTE {paziente_id}")
    print(f"{'='*60}")
    
    # Nodi associati
    pickup_Out = paziente_id
    delivery_Out = paziente_id + n
    pickup_In = paziente_id + n//2
    delivery_In = paziente_id + 3*n//2
    
    print(f"\nNodi della richiesta:")
    print(f"  Pickup outbound:   {pickup_Out}")
    print(f"  Delivery outbound: {delivery_Out}")
    print(f"  Pckup Inbound: {pickup_In}")
    print(f"  Delivery Inbound:  {delivery_In}")
    
    # Time windows
    print(f"\nTime Windows:")
    print(f"  Pickup Outbound:   [{e[pickup_Out]:.2f} - {l[pickup_Out]:.2f}] (ampiezza: {l[pickup_Out]-e[pickup_Out]:.2f})")
    print(f"  Delivery Outbound: [{e[delivery_Out]:.2f} - {l[delivery_Out]:.2f}] (ampiezza: {l[delivery_Out]-e[delivery_Out]:.2f})")
    print(f"  Pickup Inbound: [{e[pickup_In]:.2f} - {l[pickup_In]:.2f}] (ampiezza: {l[pickup_In]-e[pickup_In]:.2f})")
    print(f"  Delivery Inbound:  [{e[delivery_In]:.2f} - {l[delivery_In]:.2f}] (ampiezza: {l[delivery_In]-e[delivery_In]:.2f})")
    
    # Tempi di viaggio
    print(f"\nTempi di viaggio:")
    print(f"  Deposito → Pickup Outbound:     {t_matrix[0][pickup_Out]:.2f}")
    print(f"  Pickup Outbound → Delivery Outbound:     {t_matrix[pickup_Out][delivery_Out]:.2f}")
    print(f"  Delivery Outbound → Pickup Inbound:   {t_matrix[delivery_Out][pickup_In]:.2f}")
    print(f"  Pickup Inbound → Delivery Inbound:    {t_matrix[pickup_In][delivery_In]:.2f}")
    print(f"  Delivery Inbound → Deposito:    {t_matrix[delivery_In][2*n+1]:.2f}")
    
    # Tempi di servizio
    print(f"\nTempi di servizio:")
    print(f"  Pickup Outbound:   {serv[pickup_Out]:.2f}")
    print(f"  Delivery Outbound: {serv[delivery_Out]:.2f}")
    print(f"  Pickup Inbound: {serv[pickup_In]:.2f}")
    print(f"  Delivery Inbound:  {serv[delivery_In]:.2f}")
    
    # Ride time massimo
    print(f"\nRide time massimo: {T[paziente_id]:.2f}")
    
    # Carico
    print(f"\nCarico:")
    print(f"  Pickup Outbound:   {q[pickup_Out]}")
    print(f"  Delivery Outbound: {q[delivery_Out]}")
    print(f"  Pickup Inbound:   {q[pickup_In]}")
    print(f"  Delivery Outbound: {q[delivery_In]}")
    print(f"  Capacità max: {Q_max}")
    
    # Verifica sequenza più semplice
    print(f"\n{'='*60}")
    print(f"TEST: Sequenza più semplice [0, p_o, d_o, p_in, d_in, 2n+1]")
    print(f"{'='*60}")
    
    simple_route = [0, pickup_Out, delivery_Out, pickup_In, delivery_In, 2*n+1]
    print(f"Route: {simple_route}")
    
    # Simula calcolo tempi passo-passo
    t = np.zeros(len(simple_route))
    t[0] = 0
    
    for j in range(1, len(simple_route)):
        prev_node = simple_route[j-1]
        curr_node = simple_route[j]
        
        arrival = max(t[j-1], e[prev_node]) + serv[prev_node] + t_matrix[prev_node][curr_node]
        t[j] = max(arrival, e[curr_node])
        
        print(f"\nNodo {curr_node}:")
        print(f"  Arrivo:        {arrival:.2f}")
        print(f"  Inizio serv:   {t[j]:.2f}")
        print(f"  Time window:   [{e[curr_node]:.2f} - {l[curr_node]:.2f}]")
        
        if arrival > l[curr_node]:
            print(f"  ❌ VIOLAZIONE: arrivo {arrival:.2f} > chiusura {l[curr_node]:.2f}")
            print(f"     Tempo mancante: {arrival - l[curr_node]:.2f}")
            
            # Analizza da dove viene il ritardo
            if j > 1:
                print(f"     Breakdown:")
                print(f"       - Tempo al nodo prec: {t[j-1]:.2f}")
                print(f"       - Apertura nodo prec: {e[prev_node]:.2f}")
                print(f"       - Tempo servizio:     {serv[prev_node]:.2f}")
                print(f"       - Tempo viaggio:      {t_matrix[prev_node][curr_node]:.2f}")
        elif t[j] > l[curr_node]:
            print(f"  ❌ VIOLAZIONE: inizio servizio {t[j]:.2f} > chiusura {l[curr_node]:.2f}")
        else:
            print(f"  ✅ OK")
    
    # Verifica ride time
    print(f"\n{'='*60}")
    print(f"VERIFICA RIDE TIME")
    print(f"{'='*60}")
    
    pickup_idx = simple_route.index(pickup_Out)
    delivery_idx = simple_route.index(delivery_Out)
    
    ride_time = t[delivery_idx] - (max(t[pickup_idx], e[pickup_Out]) + serv[pickup_Out])
    print(f"Ride time: {ride_time:.2f}")
    print(f"Massimo:   {T[paziente_id]:.2f}")
    
    if ride_time > T[paziente_id]:
        print(f"❌ VIOLAZIONE: ride time {ride_time:.2f} > max {T[paziente_id]:.2f}")
        print(f"   Eccesso: {ride_time - T[paziente_id]:.2f}")
    else:
        print(f"✅ OK")
    
    # Verifica capacità
    print(f"\n{'='*60}")
    print(f"VERIFICA CAPACITÀ")
    print(f"{'='*60}")
    
    Q_curr = 0
    for node in simple_route:
        Q_curr += q[node]
        print(f"Dopo nodo {node}: carico = {Q_curr} / {Q_max}")
        if Q_curr < 0 or Q_curr > Q_max:
            print(f"❌ VIOLAZIONE CAPACITÀ")
    
    print(f"\n{'='*60}")
    
    # Testa con feasible()
    is_feas, times = feasible(simple_route, serv, t_matrix, T, n, e, l, P, D, q, Q_max, debug=True)
    print(f"\nRisultato feasible(): {is_feas}")




def order_randomly(PHOME, seed=42):
    """Ordine casuale per esplorare soluzioni diverse"""
    random.seed(seed)
    shuffled = list(PHOME)
    random.shuffle(shuffled)
    return shuffled