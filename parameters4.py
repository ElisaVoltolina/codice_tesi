import random
import numpy as np

# Veicle capacity
Q = 4

# number of requests (pickup + delivery)
n = 10 

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
s = np.array([0,3,1,2,1,1,3,2,1,1,4,6,2,5,2,4,3,2,1,2,1,0])

# Tempo massimo per ogni corsa (pickup) 
#T = {i: random.uniform(10, 20) for i in range(1, n + 1)}
T={i: 2000 for i in range(1, n+1)}

# Carichi al pickup e delivery (q_i+n=−q_i)
q_pickup = np.ones(n)  
q_delivery = -q_pickup  
q = np.concatenate(([0], q_pickup, q_delivery, [0]))


# Generazione della matrice dei tempi
t = np.random.randint(1, 5, size=(22,22))
t = t+t.T 
t = t//2
t*= 1 - np.eye(22, dtype=np.int64)

aa = [0,2,3,1,5,13,4,12,15,8,11,14,6,18,9,16,10,7,19,20,17,21]
cc = [3,8,2,5,4,6,5,4,2,1,5,7,9,3,6,2,4,5,2,3,5]

for a_i, b_i, c_i in zip(aa[:-1], aa[1:], cc):
    t[a_i, b_i] = t[b_i, a_i] = c_i

#time windows
e=[0,     14,2,10,40,22,84,117,59,95,   110,60,45,30,70,55,102,130,95,  125,129,0]
l=[300,   20,5,16,45,27,90,125,65,105,  118,70,50,36,77,60,112,139,100, 130,135,300]