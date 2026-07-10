import os
import requests
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

def setup_ice_breakers():
    token = os.environ.get('WA_ACCESS_TOKEN')
    phone_id = os.environ.get('WA_PHONE_NUMBER_ID')
    
    if not token or not phone_id:
        print("Erreur: Les variables d'environnement WA_ACCESS_TOKEN et WA_PHONE_NUMBER_ID doivent être définies dans votre fichier .env")
        return
        
    # URL de l'API Graph Meta pour le profil WhatsApp Business
    url = f"https://graph.facebook.com/v20.0/{phone_id}/whatsapp_business_profile"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Configuration des Conversational Components (Ice Breakers)
    payload = {
        "messaging_product": "whatsapp",
        "commands": [
            {
                "commands": [
                    {
                        "command": "Je cherche un bien à louer",
                        "description": "Recherche de location"
                    },
                    {
                        "command": "Je cherche à acheter un bien",
                        "description": "Projet d'achat"
                    },
                    {
                        "command": "Je souhaite confier un bien",
                        "description": "Gestion locative"
                    }
                ]
            }
        ]
    }
    
    print("Envoi de la configuration des Ice Breakers à Meta...")
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        print("✅ Succès ! Ice Breakers configurés avec succès sur votre numéro WhatsApp.")
        print("Réponse Meta:", response.json())
    else:
        print(f"❌ Erreur HTTP {response.status_code}: {response.text}")

if __name__ == "__main__":
    setup_ice_breakers()
