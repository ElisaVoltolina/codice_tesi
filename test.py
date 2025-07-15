from utils import find_original_ids_from_new_indices

exclude_requests = [(2, 12), (7, 17)]

#Trovo gl ID originali delle nuove coppie ptoblematiche
original_ids_1 = find_original_ids_from_new_indices("ipdptw-n20-ber.txt", 1, 9, exclude_requests)
original_ids_2 = find_original_ids_from_new_indices("ipdptw-n20-ber.txt", 5, 13, exclude_requests)
#Aggiungo questi nodi tra quelli da escludere usando i loro ID originali
exclude_requests.extend([original_ids_1, original_ids_2])


print(exclude_requests)