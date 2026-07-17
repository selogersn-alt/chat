import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatproject.settings')
django.setup()

from chat.models import District, PropertyType

districts = [
    "Dakar", "ouagou niaye", "Saly", "New York", "Mbour", "Thies", "Diourbel",
    "Almadies", "Almadies 2", "Amitié", "Avenue Bourguiba", "Bambilor", "Bargny",
    "Bayakh", "Bel air", "Biscuiterie", "Cambérène", "Castor", "Cité mixta",
    "Cité Damel", "Cité asecna", "Cité assemblée", "Cité biagui", "Cité avion",
    "Cité keur gorgui", "Colobane", "Comico", "Dalifort", "Derkle", "Diamaguene",
    "Diamniadio", "Dieuppeul", "Djidah thiaroye kaw", "Djily mbaye", "Fann",
    "Fann hock", "Fass", "Fenêtre Mermoz", "Gibraltar", "Golf", "Gorom", "Gorée",
    "Grand-Dakar", "Grand-yoff", "Guediawaye", "Gueule-tapée", "Guinaw rail",
    "Hann", "Hann bel air", "Hann mariste", "Hann marinas", "HLM", "HLM grand yoff",
    "Karack", "Keur massar", "Keur Ndiaye lo", "Kounoune", "Lac rose", "Liberté 1",
    "Liberté 2", "Liberté 3", "Liberté 4", "Liberté 5", "Liberté 6", "Liberté 6 extension",
    "Malika", "Mamelle", "Mbao", "Mermoz", "Medina", "Ndiakhirate", "Ngor", "Niague",
    "Niakoul rap", "Noflaye", "Nord foire", "Ouest foire", "Ouakam", "Parcelles assainies",
    "Patte d'oie", "Petit Mbao", "Pikine", "Plateau", "Point E", "Point E", "Rufisque",
    "Sacre coeur 1", "Sacre coeur 2", "Sacre coeur 3", "Sacre coeur pyrotechnique",
    "Sangalkam", "Sebikotane", "Sendou", "Sicap baobab", "Sicap foir", "Sipres",
    "Somone", "Sud foire", "Thiaroye", "Tivaouane peulh", "Toubab dialaw", "VDN",
    "Yene", "Yoff", "Yoff aéroport", "Yoff virage", "Yoff tonghor", "Yoff Ndeungagne",
    "Zone A", "Zone B", "Zone de captage"
]

property_types = [
    "Appartement", "Chambre salle de bain", "Maison", "Mini studio", "Terrain",
    "Immeuble", "Chambre simple", "Célibataire", "Colocation"
]

print("Populating districts...")
for d in districts:
    District.objects.get_or_create(name=d)

print("Populating property types...")
for pt in property_types:
    PropertyType.objects.get_or_create(name=pt)

print("✅ Data successfully populated!")
