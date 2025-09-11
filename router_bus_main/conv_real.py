import json
import numpy as np
from utils import calcola_distanza 
from datetime import datetime
import os, io
import random
import copy

def converti_json_per_modello(file_pazienti, Q=7):
    """
    Converte il file JSON dei pazienti nel formato richiesto dal modello.
    
    Args:
        file_pazienti (str): Path del file JSON con i dati dei pazienti
        Q (int): Capacità massima del pulmino (default 7)
    
    Returns:
        dict: Dizionario con tutti gli input necessari per il modello
    """
    
    # Carica i dati dei pazienti 
    with open(file_pazienti, 'r') as f:
        pazienti = json.load(f)  #lista di tutti i pazienti (ogni elemento della lista è il diszionario del pazinete con tutte le info)
    
    num_pazienti = len(pazienti)
    n = 2 * num_pazienti  # Numero totale di richieste (andata + ritorno per ogni paziente)
    
    #print(f"Numero pazienti: {num_pazienti}")
    print(f"Numero richieste totali (n): {n}")
    
    #creo i sottoinsiemi di nodi
    V = np.arange(2*n + 2)  # Tutti i nodi: 0, 1...n, n+1...2n, 2n+1
    P = np.arange(1, n + 1)  # Nodi pickup: 1...n
    D = np.arange(n + 1, 2*n + 1)  # Nodi delivery: n+1...2n
    PD = np.concatenate((P,D))
    PHOME = np.arange(1,n//2 +1)    #divisione intera
    PHOSP = np.arange(n//2 +1, n+1)
    DHOME = np.array([i + n for i in PHOSP])  
    DHOSP = np.array([i + n for i in PHOME])  
    HOSP= np.concatenate((PHOSP,DHOSP))

    HOME=np.concatenate((PHOME,DHOME))  #AGGIUNTO ANCHE QUESTOOOO

   

   
    
    
    # Creiamo la lista di tutti i nodi con le loro informazioni
    nodi = {} #lista di dizionari
    
    # Depositi (nodo 0 e nodo 2n+1)
    nodi[0] = {
        'tipo': 'deposito_inizio',
        'lat': 0,  # Coordinate fittizie per i depositi  (DISTANZA POI IMPOSTATE A ZERO)
        'lon': 0,
        'indirizzo': 'Deposito',
        'paziente_id': None
    }
    nodi[2*n + 1] = {
        'tipo': 'deposito_fine', 
        'lat': 0,
        'lon': 0,
        'indirizzo': 'Deposito',
        'paziente_id': None
    }
    

    # Costruzione nodi pickup e delivery seguendo la logica del modello
    for i, paziente in enumerate(pazienti):   #i indice del elemento paziente e il valore  (per 5.json i va da 0 a 4)
        paziente_idx = i + 1  # valore nel nodo corrispondente (sommo uno Perchè l'indice della lista pazienti parte da 0 ma i nodi corrispondenti da 1)
                              #vado da 1 a 5 (corrisponde ai nodi PHOME ok)

        # outbound request: pickup casa -> delivery ospedale
        pickup_casa_idx = paziente_idx  # i in PHOME
        delivery_ospedale_idx = paziente_idx + n  # i + n in DHOSP
        
        # inbound request: pickup ospedale -> delivery casa  
        # Seguendo la corrispondenza: i = i + n + n/2 = j + n
        pickup_ospedale_idx = paziente_idx + n//2  # j in PHOSP
        delivery_casa_idx = paziente_idx + n + n//2  # j + n in DHOME
        
        # Nodo pickup casa (outbound) i 
        nodi[pickup_casa_idx] = {
            'tipo': 'pickup_casa',
            'lat': paziente['domicilio_andata']['lat'],
            'lon': paziente['domicilio_andata']['lon'],
            'indirizzo': f"{paziente['domicilio_andata']['indirizzo']} {paziente['domicilio_andata']['n_civico']}, {paziente['domicilio_andata']['citta']}",
            'paziente_id': i,
            'paziente_nome': paziente['nome_paziente']
        }
        
        # Nodo delivery ospedale (outbound) i+n
        nodi[delivery_ospedale_idx] = {
            'tipo': 'delivery_ospedale',
            'lat': paziente['destinazione']['lat'],
            'lon': paziente['destinazione']['lon'],
            'indirizzo': paziente['destinazione']['nome'],
            'paziente_id': i,
            'paziente_nome': paziente['nome_paziente']
        }
        
        # Nodo pickup ospedale (inbound) j (uguale alla destinazione)
        nodi[pickup_ospedale_idx] = {
            'tipo': 'pickup_ospedale',
            'lat': paziente['destinazione']['lat'],
            'lon': paziente['destinazione']['lon'],
            'indirizzo': paziente['destinazione']['nome'],
            'paziente_id': i,
            'paziente_nome': paziente['nome_paziente']
        }
        
        # Nodo delivery casa (inbound) j+n (in questo modo può anche essere diversa dal pickup casa)
        nodi[delivery_casa_idx] = {
            'tipo': 'delivery_casa',
            'lat': paziente['domicilio_ritorno']['lat'] if 'lat' in paziente['domicilio_ritorno'] else paziente['domicilio_andata']['lat'],
            'lon': paziente['domicilio_ritorno']['lon'] if 'lon' in paziente['domicilio_ritorno'] else paziente['domicilio_andata']['lon'],
            'indirizzo': f"{paziente['domicilio_ritorno']['indirizzo']} {paziente['domicilio_ritorno']['n_civico']}, {paziente['domicilio_ritorno']['citta']}",
            'paziente_id': i,
            'paziente_nome': paziente['nome_paziente']
        } #questo perchp se sono uguali nel file json nel domicilio_ritorno non osno nuovamente ripostate lat e lon

    
    


    # Vettore q: domanda per ogni nodo
    # q_i = -q_{i+n} per ogni richiesta
    # Per pickup: +1, per delivery: -1
    q = np.zeros(2*n + 2)  # Dimensione 2n+2 per includere i depositi
    
    #va bene così (non è necessario che legga il file)
    if i in P:
        q[i]=1
    elif i in D:
        q[i]=q[i-n]
    else: #se i =0 o 2n+1
        q[i]=0
        
    
    
    
    # Vettori T e s 
    T = np.full(n, 190)  # Tempo massimo percorrenza per ogni richiesta (QUESTO DA MODIFICARE)
    #T={i: 2000 for i in range(1, n+1)}
    s = np.full(2*n + 2, 1)  # Tempo di servizio per ogni nodo (1 minuto)
    s[0] = 0  # Depositi hanno tempo servizio 0
    s[2*n + 1] = 0
    
    # Matrice dei tempi t
    print("Calcolo matrice dei tempi...")
    t = calcola_matrice_tempi(nodi, 2*n + 2)




    
   

    #TIME WINDOWS

    e = np.zeros(2*n + 2)  # Inizio time window per ogni nodo
    l = np.full(2*n + 2, 1440)  # Fine time window (1440 min = 24h) O METTO LE 18 DI SERA TIPO
    
    e[0]=360 #inizio impostato alle 6:00

    for i in range(len(PHOME)): #CAMBIA PER NON DOVER SCRIVERE +1!!!!!
        #estraggo dal dizionario pazienti ora di inizio e fine visita (solo ora in minuti)
        inizio_min = datetime.fromisoformat(pazienti[i]["inizio_visita"]).hour * 60 + datetime.fromisoformat(pazienti[i]["inizio_visita"]).minute
        fine_min= datetime.fromisoformat(pazienti[i]["fine_visita"]).hour * 60 + datetime.fromisoformat(pazienti[i]["fine_visita"]).minute

        #+1 per corrispondenza indici
        #outbound request
        l[i+n +1 ]= inizio_min - pazienti[i]['anticipo_prenotazione_minuti']-s[i+n +1]
        e[i+n +1]=l[i+n +1]-60

        #e[i+1]= max(0, e[i+n+1]-180-s[i])
        l[i+1]= min (l[i+n +1]-s[i +1]-t[i +1][i+n +1], 1440)
        e[i+1]= max(0, min( e[i+n+1]-180-s[i], l[i+1]-60))
        


        #inbound request
        e[i+ n//2 +1]= fine_min
        l[i + n//2+1]= e[i+n//2 +1] +60

        
        #e[i +n//2 +n+1]= max(e[i+n//2 +1]+ s[i+ n//2 +1]+ t[i+ n//2 +1][i+ n//2 +n +1],0)
        l[i +n//2 +n +1]= min(l[i + n//2+1]+s[i+n//2 +1]+ 180 , 1440)
        e[i +n//2 +n+1]= max(0, min( e[i+n//2 +1]+ s[i+ n//2 +1]+ t[i+ n//2 +1][i+ n//2 +n +1], l[i+n//2+n+1]-60))
        

        #definizione multi time window per i nodi casa

    a=np.empty(2*n+2, dtype= object)
    b=np.empty(2*n+2, dtype= object)
    p=np.empty(2*n+2, dtype= object)   #questo è il vettore dei pesi DIMENSIONED A MODIFICARE ma forse posso anche lasciare così

    """la dimensione deve essere coem quella di e, ogni emento ha dimensione Ni"""
    
    for i in PHOME:
        """ costruisco i sottointrevalli per i nodi pickup-casa
        ne scelgo uno in modo casuale e assegno i pesi"""

        Ai=l[i]-e[i]
        Ni=int(Ai//15)  #Ai è flot quindi lo era anche il risultato
        a[i]=np.zeros(Ni)
        b[i]=np.zeros(Ni)
        p[i]=np.zeros(Ni) 
        for j in range(Ni-1, -1, -1): #voligo che pata da NI e 0
            if j == Ni-1:
                b[i][j]=l[i]
                a[i][j]=b[i][j]-15
            else:
                b[i][j]=a[i][j+1]
                a[i][j]=b[i][j]-15
            
            #print(f"gli intervalli per il nodo {i} sono: [{a[i][j]} , {b[i][j]}]")

        #print(f"per il nodo {i} l'intervallo originale era: [{e[i], l[i]}]")
        S= random.randrange(Ni)
        s1=copy.deepcopy(S)
        s2=copy.deepcopy(S)
        p[i][s]=0
        while s1+1 <= Ni-1:
            p[i][s1+1]=p[i][s1]+1
            s1=s1+1
        while s2-1 >= 0:
            p[i][s2-1]=p[i][s2]+1
            s2=s2-1

        #print(f"l'intervallo selezionato per il nodo {i} è",s)   
        #for j in range(Ni-1, -1, -1):
            #print(f" per il nodo {i} i pesi sono: per l'intervallo {j} = {p[i][j]} ")


    for i in DHOME:
        """ costruisco i sottointrevalli per i nodi DELIVERY-casa
        ne scelgo uno in modo casuale e assegno i pesi"""

        Ai=l[i]-e[i]
        Ni=int(Ai//15)  #Ai è flot quindi lo era anche il risultato
        a[i]=np.zeros(Ni)
        b[i]=np.zeros(Ni)
        p[i]=np.zeros(Ni) 
        for j in range(Ni-1, -1, -1): #voligo che pata da NI e 0 
            if j == Ni-1:
                b[i][j]=l[i]
                a[i][j]=b[i][j]-15
            else:
                b[i][j]=a[i][j+1]
                a[i][j]=b[i][j]-15
            
            #print(f"gli intervalli per il nodo {i} sono: [{a[i][j]} , {b[i][j]}]")

        #print(f"per il nodo {i} l'intervallo originale era: [{e[i], l[i]}]")
        S= random.randrange(Ni)
        s1=copy.deepcopy(S)
        s2=copy.deepcopy(S)
        p[i][s]=0
        while s1+1 <= Ni-1:
            p[i][s1+1]=p[i][s1]+1
            s1=s1+1
        while s2-1 >= 0:
            p[i][s2-1]=p[i][s2]+1
            s2=s2-1

        #print(f"l'intervallo selezionato per il nodo {i} è",s)   
        #for j in range(Ni-1, -1, -1):
            #print(f" per il nodo {i} i pesi sono: per l'intervallo {j} = {p[i][j]} ")
        




    # Crea gli archi
    idx=([(0,j) for j in P]+[(i,j) for i in PD for j in PD if i !=j and i!= n+j]+ [(i,2*n+1) for i in D])

   
    


   
    risultato = {
        'V': V,
        'PHOSP': PHOSP,
        'DHOSP': DHOSP,
        'HOSP': HOSP,
        'PHOME': PHOME,
        'DHOME': DHOME,  #MANCAVA QUESTO
        'HOME': HOME,
        'P': P,
        'D': D,
        'PD': PD,
        'n': n,
        'Q': Q,
        'q': q.tolist(),   #liste
        't': t.tolist(),
        'T': T.tolist(),
        's': s.tolist(),
        'e': e.tolist(),
        'a': convert_object_array_to_list(a),
        'b': convert_object_array_to_list(b),
        #'S': S,
        'p': convert_object_array_to_list(p),
        'idx': idx,
        'l': l.tolist(),
        'nodi': nodi,  #questo non mi serve come input del modello in realtà
        'pazienti_originali': pazienti #nemmeno questo.. ma può essere utile

    }
    
    return risultato


def convert_object_array_to_list(obj_array):
    """Converte un array NumPy di dtype=object contenente array NumPy in liste annidate"""
    result = []
    for i in range(len(obj_array)):
        if obj_array[i] is not None and hasattr(obj_array[i], 'tolist'):
            result.append(obj_array[i].tolist())
        else:
            result.append(obj_array[i])  # None o altri tipi
    return result


def calcola_matrice_tempi(nodi, num_nodi):
    """
    Calcola la matrice dei tempi tra tutti i nodi utilizzando la funzione calcola_distanza.
    num_nodi=2n+2
    """
    t = np.zeros((num_nodi, num_nodi))
    
    for i in range(num_nodi): 
        for j in range(num_nodi):
            if i == j:
                t[i][j] = 0 
            elif i == 0 or j == 0 or i == num_nodi-1 or j == num_nodi-1:  
                # Depositi hanno distanza 0 da tutti i nodi (così non dovrebbero influenzare la soluzione)
                t[i][j] = 0
            else:
                # Controlla se i nodi rappresentano lo stesso posto fisico
                nodo_i = nodi[i]
                nodo_j = nodi[j]
                
                if abs(nodo_i['lat'])==abs(nodo_j['lat']) and abs(nodo_i['lon'])==abs(nodo_j['lon']):
                    t[i][j] = 0  # Stesso posto fisico -> distanza 0
                else:
                    # Calcola distanza reale usando la funzione esistente
                    address1 = {
                        'lat': nodo_i['lat'],
                        'lon': nodo_i['lon'],
                        'tags': {'addr:street': '', 'addr:housenumber': '', 
                                'addr:postcode': '', 'addr:city': nodo_i['indirizzo']}
                    }
                    address2 = {
                        'lat': nodo_j['lat'], 
                        'lon': nodo_j['lon'],
                        'tags': {'addr:street': '', 'addr:housenumber': '',
                                'addr:postcode': '', 'addr:city': nodo_j['indirizzo']}
                    }
                    
                    
                    routing_data = calcola_distanza(address1, address2)   
                    t[i][j] = routing_data['minutes']      #QUI SEGNALARE ERRORE NEL CALCOLO DEI TEMPI
    return t






def salva_input_modello(dati_modello, nome_file):
    """
    Salva i dati del modello in un file JSON.
    """
    for k, v in dati_modello.items():
        if type(v).__name__ == "ndarray":
            dati_modello[k] = v.tolist()
        elif k == "idx":  #idx lista di tuple (non supporato da json.dump)
            dati_modello[k] = [[int(x)for x in t] for t in v]

    try:
        with open(nome_file, 'w', encoding='utf-8') as f:
            f.write(json.dumps(dati_modello, ensure_ascii=False))
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"An error occurred: {e}")


    print(f"Dati modello salvati in: {nome_file}")






if __name__ == "__main__":
    # Converte il file 
    dati_modello = converti_json_per_modello(r'data\20.json', Q=7)
    for k in dati_modello.keys():
        print(k)
    # Salva il risultato 
    salva_input_modello(dati_modello, 'dati_conv\input_modello_20.json')
    
    # Stampa informazioni di debug
    print(f"\nRiepilogo conversione:")
    print(f"Numero pazienti: {len(dati_modello['pazienti_originali'])}")
    print(f"Numero richieste (n): {dati_modello['n']}")
    print(f"Capacità pulmino (Q): {dati_modello['Q']}")
    print(f"Numero nodi totali: {len(dati_modello['nodi'])}")
    print(f"Dimensione matrice tempi: {len(dati_modello['t'])}x{len(dati_modello['t'][0])}")
    #print(dati_modello['t'][1][1])
    print(f"il vettore dei tempi di servizio= {dati_modello['s']}")
    print(f"il vettore dei e={dati_modello['e']}")
    print(f"il vettore dei tempi l={dati_modello['l']}")
    #print(f"archi= {dati_modello['idx']}")
    #print(f"il vettore dei q={dati_modello['q']}")
    #print(f"i nodi={dati_modello['nodi']}")