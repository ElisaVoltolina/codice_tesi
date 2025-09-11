import os
from utils import download_indirizzi, get_indirizzi, calcola_distanza, fake_pazienti

NUM_TRASPORTI_LISTA = [10, 15, 20, 5, 12, 17,8]
LISTA_OSPEDALI = [
    {
        'nome': 'Spilimbergo',
        'lat': 46.1555694,
        'lon': 12.805655,
    },
    {
        'nome': 'Pordenone',
        'lat': 46.0113041,
        'lon': 12.5198092,
    },
]
LISTA_COMUNI = ["Arba",
        "Castelnovo del Friuli",
        "Cavasso Nuovo",
        "Clauzetto",
        "Fanna",
        "Maniago",
        "Meduno",
        "Montereale Valcellina",
        "Pinzano al Tagliamento",
        "Sequals",
        "Spilimbergo",
        "Travesio",
        "Vajont",
        "Vito d'Asio",
        "Vivaro"]

# Numero di istanze da creare per ogni numero di trasporti
NUM_ISTANZE_PER_TRASPORTI = 4  
SUFFISSI = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']


os.makedirs('indirizzi', exist_ok=True)
os.makedirs('routes', exist_ok=True)
os.makedirs('data', exist_ok=True)
os.makedirs('addresses', exist_ok=True)

# Scarica gli indirizzi (una sola volta ora)
download_indirizzi(lista_comuni=LISTA_COMUNI)

for NUM_TRASPORTI_OGGI in NUM_TRASPORTI_LISTA:
    for i in range(NUM_ISTANZE_PER_TRASPORTI):
        suff=SUFFISSI[i]
   
        addresses = get_indirizzi(NUM_TRASPORTI_OGGI, suff)
        pazienti = fake_pazienti(addresses, LISTA_OSPEDALI, suff)

# calcolo le distanze tra indirizzo i e 2 (tutte le combinazioni possibili)
for address1 in addresses:
    for address2 in addresses:
        calcola_distanza(address1, address2)