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

os.makedirs('indirizzi', exist_ok=True)
os.makedirs('routes', exist_ok=True)
os.makedirs('data', exist_ok=True)
os.makedirs('addresses', exist_ok=True)

for NUM_TRASPORTI_OGGI in NUM_TRASPORTI_LISTA:
    download_indirizzi(lista_comuni=LISTA_COMUNI)
    addresses = get_indirizzi(NUM_TRASPORTI_OGGI)
    pazienti = fake_pazienti(addresses, LISTA_OSPEDALI)

# calcolo le distanze tra indirizzo i e 2 (tutte le combinazioni possibili)
for address1 in addresses:
    for address2 in addresses:
        calcola_distanza(address1, address2)