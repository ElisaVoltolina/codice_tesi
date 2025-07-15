import random
import numpy as np

# Veicle capacity
Q = 2

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
s = np.array([0, 2,3,2,5,1,4, 5,1,4, 2,3,2,0])

# Tempo massimo per ogni corsa (pickup) 
#T = {i: random.uniform(10, 20) for i in range(1, n + 1)}
T={i: 2000 for i in range(1, n+1)}

# Carichi al pickup e delivery (q_i+n=−q_i)
q_pickup = np.ones(n)  # Rand interi tra 1 e Q/2
q_delivery = -q_pickup  
q = np.concatenate(([0], q_pickup, q_delivery, [0]))


# Generazione della matrice dei tempi
t = np.random.randint(4, 15, size=(14,14))
t = t+t.T 
t = t//2
t*= 1 - np.eye(14, dtype=np.int64)

aa = [0,1,2,8,3,7,5,9,4,10,11,6,12,13]
cc = [5,3,2,1,4,6,3,7,10,3,7,1]

for a_i, b_i, c_i in zip(aa[:-1], aa[1:], cc):
    t[a_i, b_i] = t[b_i, a_i] = c_i

#time windows
e=[0,7,8,3,8,36,70,2,5,15,30,30,90,0 ]
l=[300,10,15,21,55,42,100,30, 25,50,80,80,120,300 ] 