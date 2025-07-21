from utils import find_original_ids_from_new_indices

exclude_requests = [(2, 12), (7, 17), (6,16), (1,11),(5,15), (10,20)]

#Trovo gl ID originali delle nuove coppie ptoblematiche
original_ids = find_original_ids_from_new_indices("ipdptw-n20-ber.txt", 4, 8, exclude_requests)



print(original_ids)