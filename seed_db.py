import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatproject.settings')
django.setup()

from chat.models import District, PropertyType

property_types = [
    "Appartement",
    "Chambre salle de bain",
    "Maison",
    "Mini studio",
    "Terrain",
    "Immeuble",
    "Chambre simple",
    "Célibataire",
    "Colocation",
    "Magasin",
    "Salon",
    "Duplex",
    "Studio entré salon",
    "Studio séparé",
    "Appartement F3",
    "Appartement F4",
    "Appartement F5",
    "Usage professionnel",
    "TRIPLEX",
    "VIDE",
    "MEUBLE",
    "VENTE"
]

districts = [
    "Dakar", "ouagou niaye", "Saly", "New York", "Mbour", "Thies", "Diourbel",
    "Almadies", "Almadies 2", "Amitié", "Avenue Bourguiba", "Bambilor", "Bargny",
    "Bayakh", "Bel air", "Biscuiterie", "Cambérène", "Castor", "Cité mixta",
    "Cité Damel", "Cité asecna", "Cité assemblée", "Cité biagui", "Cité avion",
    "Cité keur gorgui", "Colobane", "Comico", "Dalifort", "Derkle", "Diamaguene",
    "Diamniadio", "Dieuppeul", "Djidah thiaroye kaw", "Djily mbaye", "Fann",
    "Fann hock", "Fass", "Fenêtre Mermoz", "Gibraltar", "Golf", "Gorom", "Gorée",
    "Grand-Daka", "Grand-yoff", "Guediawaye", "Gueule-tapée", "Guinaw rail", "Hann",
    "Hann bel air", "Hann mariste", "Hann marinas", "HLM", "HLM grand yoff",
    "Karack", "Keur massar", "Keur Ndiaye lo", "Kounoune", "Lac rose", "Liberté 1",
    "Liberté 2", "Liberté 3", "Liberté 4", "Liberté 5", "Liberté 6",
    "Liberté 6 extension", "Malika", "Mamelle", "Mbao", "Mermoz", "Medina",
    "Ndiakhirate", "Ngor", "Niague", "Niakoul rap", "Noflaye", "Nord foire",
    "Ouakam", "Ouest foire", "Parcelles assainies", "Patte d'oie", "Pikine",
    "Plateau", "Point E", "Rufisque", "Sacré cœur 1", "Sacré cœur 2", "Sacré cœur 3",
    "Sangalkam", "Sebikotane", "Sendou", "Sicap liberté", "Sicap sacré cœur",
    "Sicap baobab", "Sicap mbao", "Sicap foire", "Sud foire", "Thiaroye", "Thongor",
    "Tivaouane peulh", "Toubab dialo", "VDN", "Virage", "Yene", "Yeumbeul", "Yoff",
    "Zac mbao", "Zone de captage", "Zone industrielle", "Bambey", "Mbacke", "Touba",
    "Fatick", "Diofior", "Djilor", "Foundiougne", "Gossas", "Karrang poste", "Passi",
    "Sokone", "Soum", "Toubacouta", "Kaolack", "Fass Kaolack", "Gandiaye", "Guinguineo",
    "Kahone", "Keur madiabel", "Mboss", "Ndoffane", "Nioro du rip", "Sibassor",
    "Kolda", "Louga", "Diass", "Diender", "Fandene", "Fissel", "Gandigal", "Guereo",
    "Joal fadiouth", "Kayar", "Keur Moussa", "Khonbole", "Malicound", "Mbodiene",
    "Mboro", "Meckhe", "Ndayane", "Ndiagniao", "Ngaparou", "Ngoundiane", "Nguekhokh",
    "Ngueniene", "Nguering", "Nianing", "Noto", "Panbal", "Pointe sarene", "Popenguine",
    "Pout", "Saly portudal", "Sandiara", "Sessene", "Sindia", "Somone", "Tassette",
    "Thiadiaye", "Thienaba", "Tivaouane thies", "Touba toul", "Toubab dialaw",
    "Warang", "Ziguinchor", "Sedhiou", "Kaffrine", "Kedougou", "Sine Saloum",
    "Cité Batrain", "Cité Mbakiyou Faye", "Cité Check Amar", "Khar yalla",
    "Grand yoff", "Ouagou niaye", "DAKAR", "Monument renaissance", "Scat urbam",
    "Foire", "Sipres", "Mariste", "Ouakam brioche dorée", "Mariste 2", "Zone A",
    "Zone b", "Grand mbao", "Cité littoral", "Gadaye", "HLM GRAND MEDINE", "Bopp",
    "Diaxay", "MALIBU", "Diamalaye", "Rufisque, Sénégal", "Saly, Sénégal",
    "Point E, Dakar, Sénégal", "Sicap Liberté, Dakar, Sénégal", "Yoff, Dakar, Sénégal",
    "Thies, Sénégal", "Almadies, Dakar, Sénégal", "Fann, Dakar, Sénégal",
    "Sacré-Coeur, Dakar, Sénégal", "Ngor, Dakar, Sénégal", "Mamelles, Dakar, Sénégal",
    "Patte d'oie, Dakar, Sénégal", "Sipres, Dakar, Sénégal", "Fass, Dakar, Sénégal",
    "Mermoz-Sacré Coeur, Dakar, Sénégal", "Cambérène, Dakar, Sénégal",
    "Grand Yoff, Dakar, Sénégal", "Dakar, Sénégal", "Mbour, Sénégal",
    "Dakar Plateau, Dakar, Sénégal", "Sicap foire, Dakar, Sénégal", "Niary taly",
    "Ben Taly", "Oukam Corniche", "CITE MOURTADA", "OUAKAM MONPRIX", "centenaire"
]

def run():
    print("Seeding Property Types...")
    for pt in set(property_types):
        obj, created = PropertyType.objects.get_or_create(name=pt.strip())
        if created:
            print(f"Created PropertyType: {pt}")

    print("\nSeeding Districts...")
    for d in set(districts):
        obj, created = District.objects.get_or_create(name=d.strip())
        if created:
            print(f"Created District: {d}")
            
    print("\nDone!")

if __name__ == '__main__':
    run()
