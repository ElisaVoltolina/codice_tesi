import random
import numpy as np

# Veicle capacity
Q = 4

# number of requests (pickup + delivery)
n = 8   

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
s = np.concatenate(([0], np.ones(16, dtype=int), [0]))  #fissato tempo di servizio uguale a 1 per ogni nodo


# Tempo massimo per ogni corsa (pickup) 
#T = {i: random.uniform(10, 20) for i in range(1, n + 1)}
T={i: 2000 for i in range(1, n+1)}

# Carichi al pickup e delivery (q_i+n=−q_i)
q_pickup = np.ones(n)  
q_delivery = -q_pickup  
q = np.concatenate(([0], q_pickup, q_delivery, [0]))


# Generazione della matrice dei tempi
t = np.random.randint(1, 5, size=(18,18))
t = t+t.T 
t = t//2
t*= 1 - np.eye(18, dtype=np.int64)

aa = [0,1,3,4,11,9,2,12,10,6,7,14,5,8,15,13,16,17]
cc = [5,3,4,2,2,3,1,3,0,2,4,8,2,5,3,1,5]

for a_i, b_i, c_i in zip(aa[:-1], aa[1:], cc):
    t[a_i, b_i] = t[b_i, a_i] = c_i

#time windows
e=[0,4,20,5,4,45,12,20, 40,19,31,15,20,55,38,41,58,0]
l=[300,8,30,15,17,55,35,40,55, 30,40,23,35,65,45,65,70,300]