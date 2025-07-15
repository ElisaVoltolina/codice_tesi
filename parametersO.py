import random
import numpy as np

# Veicle capacity
Q = 9

# number of requests (pickup + delivery)
n = 6   

num_nodes = 2 * n + 2 #number of node of the graph 
#Set of nodes
V = np.arange(num_nodes) #all nodes (including depot) 
P = np.arange(1, n+1)  # pickup node
D = np.arange(n+1,2*n+1) #delivery node
PHOME = np.arange(1,n//2 +1)
PHOSP = np.arange(n//2, n+1)
DHOME = np.array([i + n for i in PHOSP])  
DHOSP = np.array([i + n for i in PHOME])  


PD = np.concatenate((P,D))
HOSP= np.concatenate((PHOSP,DHOSP))

#arcs
idx=([(0,j) for j in P]+[(i,j) for i in PD for j in PD if i !=j and i!= n+j]+ [(i,2*n+1) for i in D])

# Tempi di servizio casuali (0 per il deposito)
s = np.concatenate(([0], np.random.uniform(0.5, 5, size=2 * n), [0]))

# Tempo massimo per ogni corsa (pickup) 
#T = {i: random.uniform(10, 20) for i in range(1, n + 1)}
T={i: 2000 for i in range(1, n+1)}

# Carichi al pickup e delivery (q_i+n=−q_i)
q_pickup = np.random.randint(1, Q // 2 + 1, size=n)  # Rand interi tra 1 e Q/2
q_delivery = -q_pickup  
q = np.concatenate(([0], q_pickup, q_delivery, [0]))

v_avg = 30  # Velocità media in km/h

# Generazione della matrice delle distanze casuali (simmetrica) 
d = np.random.randint(1, 40, size=(num_nodes, num_nodes))  # Numeri casuali tra 1 e 40 (distanze massime di 40 km)
np.fill_diagonal(d, 0)  # Imposta la diagonale a 0

# Rende la matrice simmetrica
d = np.triu(d) + np.triu(d, 1).T

# Generazione della matrice dei tempi
t = (d / v_avg) * 60 #in minuti

from timewind import generate_time_windows
e,l = generate_time_windows(n,t)