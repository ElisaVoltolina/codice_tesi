import json
import os
import requests
import random
import datetime
from faker import Faker

def download_indirizzi(lista_comuni):
    # Scarico gli indirizzi del comune del comune
    for comune in lista_comuni:
        
        if not os.path.isfile(f'indirizzi/{comune}.json'):
            url = f'http://nominatim.openstreetmap.org/search?q={comune}&format=json'
            response = requests.get(url, headers={'User-Agent': 'router-bus'})
            data = response.json()[0]['osm_id']
            city_id = response.json()[0]['osm_id']
            area_id = int(city_id) + 3600000000 # 3600179210 travesio

            overpass_query = f'''[out:json][timeout:600];
                area(id:{area_id})->.searchArea;
                ( 
                node(area.searchArea)["addr:housenumber"]["addr:street"];    
                );
                out;
                out count;'''
            overpass_url = "http://overpass-api.de/api/interpreter"
            response = requests.get(overpass_url, params={'data': overpass_query})
            data = response.json()
            
            with open(f'indirizzi/{comune}.json', 'w') as f:
                json.dump(data, f)

def get_indirizzi(NUM_TRASPORTI_OGGI):
    
    path = f'addresses/{NUM_TRASPORTI_OGGI}.json'
    if not os.path.isfile(path):
        all_addresses = []
        for comune in os.listdir('indirizzi'):
            with open(f'indirizzi/{comune}') as f:
                data = json.load(f)
                for d in data['elements']:
                    all_addresses.append(d)

        # Tiro fuori indirizzi a caso
        address = []
        for i in range(NUM_TRASPORTI_OGGI):
            address.append(random.choice(all_addresses))

        with open(path, 'w') as f:
            json.dump(address, f)
    else:
        with open(path) as f:
            address = json.load(f)
            
    return address

def calcola_distanza(address1, address2):
    path = f'routes/{address1["lat"]},{address1["lon"]};{address2["lat"]},{address2["lon"]}.json'
    if not os.path.isfile(path):
        url = f'https://routing.openstreetmap.de/routed-car/route/v1/driving/{address1["lat"]},{address1["lon"]};{address2["lat"]},{address2["lon"]}?overview=full&geometries=geojson'
        full_address1 = f"{address1['tags']['addr:street']} {address1['tags']['addr:housenumber']}, {address1['tags']['addr:postcode']}, {address1['tags']['addr:city']}"
        full_address2 = f"{address2['tags']['addr:street']} {address2['tags']['addr:housenumber']}, {address2['tags']['addr:postcode']}, {address2['tags']['addr:city']}"

        data = requests.get(url).json()
        with open(f'routes/{address1["lat"]},{address1["lon"]};{address2["lat"]},{address2["lon"]}.json', 'w') as f:
            data['minutes'] = int(data['routes'][0]['duration'])/60
            data['distance_km'] = int(data['routes'][0]['distance'])/1000
            json.dump(data, f)
            #print('distanza in metri', data['routes'][0]['distance'])
            #print('tempo minuti', (int(data['routes'][0]['duration']))/60)
            
    else:
        with open(path) as f:
            data = json.load(f)
    return data
    
def fake_pazienti(addresses, LISTA_OSPEDALI):
    path = f'data/{len(addresses)}.json'
    if not os.path.isfile(path):
        pazienti = []
        fake = Faker('it_IT')
        Faker.seed(4321)
        
        start = datetime.datetime.now().replace(hour=9, minute=0)
        end = datetime.datetime.now().replace(hour=17, minute=0)

        for address in addresses:
            d0 = fake.date_time_between(start, end)
            print(d0)
            d1 = d0 + datetime.timedelta(minutes=random.randint(30, 90))
            
            pazienti.append({
                "nome_paziente": fake.name(),
                "contatti": [
                    {
                        "tipo": "mail",
                        "valore": fake.email(),
                        "note": ""
                    },
                    {
                        "tipo": "telefono",
                        "valore": fake.phone_number(),
                        "note": "Telefono figlo Luigi"
                    }
                ],
                "domicilio_andata": {
                    "indirizzo": address['tags']['addr:street'],
                    "cap": address['tags']['addr:postcode'],
                    "n_civico": address['tags']['addr:housenumber'],
                    "citta": address['tags']['addr:city'],
                    "nazione": "IT",
                    "lat": address['lat'],
                    "lon": address['lon'],
                },
                "domicilio_ritorno": {
                    "indirizzo": address['tags']['addr:street'],
                    "cap": address['tags']['addr:postcode'],
                    "n_civico": address['tags']['addr:housenumber'],
                    "citta": address['tags']['addr:city'],
                    "nazione": "IT"
                },
                "destinazione": random.choice(LISTA_OSPEDALI),
                "anticipo_prenotazione_minuti": random.randint(0, 30),
                "inizio_visita": d0.strftime( '%Y-%m-%dT%H:%M:%S%Z.%f'),
                "fine_visita": d1.strftime( '%Y-%m-%dT%H:%M:%S%Z.%f'),
                "esigenze": {
                    "sedia_rotelle": random.randrange(100) < 11, # 10% di possbilità che sia True
                    "bombola_ossigeno": random.randrange(100) < 11, # 10% di possbilità che sia True
                },
                "note": "Altre informazioni utili"
            })
        with open(path, 'w') as f:
            print(pazienti)
            json.dump(pazienti, f)
    else:
        print(path)
        with open(path) as f:
            pazienti = json.load(f)

    return pazienti
