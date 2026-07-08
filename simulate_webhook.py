import sys
import json
import requests

def send_mock_message(phone, name, text, msg_type="text", media_url=None):
    # Detect active port by trying 8001 first, then fallback to 8000
    active_url = None
    for port in [8001, 8000]:
        test_url = f"http://127.0.0.1:{port}/api/webhook/"
        try:
            # Check if server is listening and contains our brand "Loger"
            r = requests.get(f"http://127.0.0.1:{port}/login/", timeout=0.5)
            if r.status_code == 200 and "Loger" in r.text:
                active_url = test_url
                break
        except requests.RequestException:
            continue
            
    if not active_url:
        active_url = "http://127.0.0.1:8001/api/webhook/" # fallback default

    # Standard Meta WhatsApp Cloud API Payload Structure
    message_obj = {
        "from": phone,
        "id": "wamid.HBgLMjI4OTA5MDkwOTAVAgIGE0E1RDY2REQ0RjhD",
        "timestamp": "1720392000",
        "type": msg_type
    }
    
    if msg_type == "text":
        message_obj["text"] = {"body": text}
    elif msg_type == "audio":
        message_obj["audio"] = {"id": media_url or "mock_voice_note_media_id_123"}
    elif msg_type == "image":
        message_obj["image"] = {
            "id": media_url or "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1200&q=80",
            "caption": text
        }
    elif msg_type == "video":
        message_obj["video"] = {
            "id": media_url or "https://player.vimeo.com/external/371433846.sd.mp4?s=236da2f3c05d00db07450a1b2289ecc3d434914c&profile_id=164&oauth2_token_id=57447761",
            "caption": text
        }

    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "1234567890",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "123456789",
                                "phone_number_id": "987654321"
                            },
                            "contacts": [
                                {
                                    "profile": {
                                        "name": name
                                    },
                                    "wa_id": phone
                                }
                            ],
                            "messages": [message_obj]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }
    
    print(f"Envoi du message fictif ({msg_type}) de {name} ({phone}) :")
    print(f"Contenu/Caption : \"{text}\"")
    print(f"Lien média : {media_url or 'Par défaut'}")
    print(f"Cible : {active_url}")
    print("-" * 50)
    
    try:
        response = requests.post(active_url, json=payload, timeout=5)
        print(f"Status Code : {response.status_code}")
        print(f"Réponse du serveur : {response.text}")
    except requests.exceptions.ConnectionError:
        print(f"Erreur de connexion : Assurez-vous que le serveur Django tourne sur {active_url}")
    except Exception as e:
        print(f"Erreur inattendue : {e}")

if __name__ == "__main__":
    print("=== Simulateur de Webhook WhatsApp (Loger Sénégal) ===")
    print("1. Envoyer un message d'accueil simple (Amadou Diop)")
    print("2. Envoyer un message contenant un lien de propriété (Mariama Diallo)")
    print("3. Envoyer une Note Vocale WhatsApp (Amadou Diop)")
    print("4. Envoyer une photo de villa HD (Amadou Diop)")
    print("5. Envoyer une vidéo de visite HD (Mariama Diallo)")
    print("6. Quitter")
    
    choice = input("\nChoisissez une option (1-6) : ").strip()
    
    if choice == '1':
        send_mock_message("221771234567", "Amadou Diop", "Bonjour ! Je cherche un logement à Dakar.")
    elif choice == '2':
        send_mock_message("221778901234", "Mariama Diallo", "Bonjour, je souhaite visiter ce studio meublé s'il vous plaît : https://logersn.com/bien/studio-almadies")
    elif choice == '3':
        send_mock_message("221771234567", "Amadou Diop", "[Note Vocale WhatsApp]", msg_type="audio")
    elif choice == '4':
        send_mock_message("221771234567", "Amadou Diop", "Voici les photos de la villa F6 aux Almadies comme convenu.", msg_type="image")
    elif choice == '5':
        send_mock_message("221778901234", "Mariama Diallo", "Regardez la vidéo de visite de l'appartement à Ouakam.", msg_type="video")
    elif choice == '6':
        sys.exit(0)
    else:
        print("Option invalide.")
