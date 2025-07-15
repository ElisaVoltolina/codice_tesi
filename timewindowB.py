import random

def generate_time_windows(num_requests,t, t_start=480, t_end=1080):
    """definisco le time window impostando un intervallo
    generale nella giornata dalle 8:00 alle 18:00"""
    #num_nodes= 2* num_requests +2
    e = {} #le definisco come dizionari
    l = {}

    #Time window per nodo-deposito di partenza
    e[0]= t_start
    l[0]=t_start + random.randint(2, 5) # 2- 5 minuti di ritardi massimo per la partenza dal deposito

    #Time window per il nodo-deposito di ritrorno
    e[2*num_requests+1]=t_start    #torna appena a finito
    l[2*num_requests+1]=t_end

    for i in range(1, num_requests+1):
        # Time window per pickup node i
        #e[i] = t_start + random.randint(0, 300)  # inizio della time window tra le 8:00 e le 13:00
        e[i]= t_start
        l[i] = e[i] + random.randint(5, 15)   # durata tra 5 e 15 minuti

        # Time window per delivery node i+n
        delivery_node = i + num_requests
        #e[delivery_node] = e[i] + random.randint(60, 240)  # almeno 1-4 ORE dopo il pickup NO QUESTO NON HA SENSO
        e[delivery_node]=e[i]+ t[i][delivery_node]
        l[delivery_node] = e[delivery_node] + random.randint(5, 15)

        # coerenza con il tempo limite
        if l[delivery_node] > t_end:
            l[delivery_node] = t_end
        if e[delivery_node] > t_end - 30:
            e[delivery_node] = t_end - 30

    return e, l
