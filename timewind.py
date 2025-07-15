def generate_time_windows(num_requests, t, t_start=480, t_end=1080, max_ride_time_factor=1.5):
    """
    Versione migliorata che genera time window coerenti con i tempi di viaggio.
    Garantisce che ci sia tempo sufficiente tra pickup e delivery.
    """
    e = {}  # earliest time
    l = {}  # latest time
    T = {}  # maximum ride time
    
    service_time = 5  # tempo di servizio medio

    # Time window per nodo-deposito di partenza
    e[0] = t_start
    l[0] = t_start + 5  # 5 minuti di ritardo massimo per la partenza

    # Time window per il nodo-deposito di ritorno
    e[2*num_requests+1] = t_start  # può tornare appena finito
    l[2*num_requests+1] = t_end    # deve tornare entro la fine

    # Calcolo preliminare dei tempi minimi di viaggio diretto per ogni richiesta
    direct_travel_times = {i: t[i][i+num_requests] for i in range(1, num_requests+1)}
    
    # Calcola span temporale disponibile
    available_time = t_end - t_start - 30  # 30 minuti di buffer
    avg_time_per_request = available_time / (2 * num_requests)  # tempo medio per pickup e delivery
    
    # VERIFICA: Calcola se c'è abbastanza tempo per servire tutte le richieste
    total_min_travel_time = sum(direct_travel_times.values()) + num_requests * service_time * 2
    if total_min_travel_time > available_time:
        print(f"ATTENZIONE: Tempo totale minimo necessario ({total_min_travel_time}) > tempo disponibile ({available_time})")
        print("Le finestre temporali potrebbero essere infattibili!")
    
    # Calcoliamo un intervallo ragionevole per distribuire i pickup
    interval = min(30, max(5, avg_time_per_request / 2))
    
    for i in range(1, num_requests+1):
        
        pickup_earliest = t_start + (i - 1) * interval # distribuisco l'inizio delle time window
        
        # Assicuriamo che ci sia abbastanza tempo per completare la consegna
        latest_possible_pickup = t_end - direct_travel_times[i] - service_time * 2 - 15
        
        # Se il pickup più tardi possibile è prima del pickup più presto, abbiamo un problema
        if latest_possible_pickup < pickup_earliest:
            print(f"ATTENZIONE: Per richiesta {i}, non c'è abbastanza tempo!")
            pickup_earliest = latest_possible_pickup - 15  # Aggiustamento
        
        e[i] = pickup_earliest
        l[i] = min(pickup_earliest + 30, latest_possible_pickup)  # Finestra di max 30 min
        
        # Calcolo orario per il delivery
        delivery_node = i + num_requests
        
        # Earliest time per delivery: non può essere prima di e[i] + service + travel
        e[delivery_node] = e[i] + service_time + direct_travel_times[i]
        
        # Latest time: deve essere dopo l[i] + service + travel, ma prima di t_end
        l[delivery_node] = min(t_end, l[i] + service_time + direct_travel_times[i] + 30)
        
        # Verifica coerenza
        if e[delivery_node] > l[delivery_node]:
            print(f"ERRORE: Finestra temporale incoerente per delivery {delivery_node}!")
            print(f"  Earliest: {e[delivery_node]}, Latest: {l[delivery_node]}")
            # Aggiustamento
            l[delivery_node] = e[delivery_node] + 15
        
        # Maximum ride time con limiti ragionevoli
        min_ride_time = direct_travel_times[i]
        #T[i] = max(min_ride_time * max_ride_time_factor, min_ride_time + 20)
        
        # Verifica finale
        if l[i] + service_time + min_ride_time > l[delivery_node]:
            # Aggiusta la finestra di delivery se necessario
            l[delivery_node] = min(t_end, l[i] + service_time + min_ride_time + 5)

    # Stampa di debug
    #print("Time Windows generate:")
    #for i in range(0, 2*num_requests+2):
        #if i in e and i in l:
            #time_info = f"Node {i}: [{e[i]:.1f} - {l[i]:.1f}]"
            i#f i <= num_requests and i > 0:
                #time_info += f", Max ride time: {T[i]:.1f}"
            #print(time_info)
    
    return e, l