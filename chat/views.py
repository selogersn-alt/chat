import os
import re
import csv
import json
import logging
import requests
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from datetime import timedelta
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.db import models
from django.db.models import Q, Count, Max, Prefetch
from django.core.cache import cache
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from .models import User, Conversation, Message, Property, QuickTemplate, Reminder, Partner, PartnerMatch, Visit, District, PropertyType

logger = logging.getLogger(__name__)

def format_time_short(dt):
    if not dt: return ""
    now = timezone.localtime(timezone.now())
    msg_time = timezone.localtime(dt)
    if msg_time.date() == now.date():
        return msg_time.strftime("%H:%M")
    elif msg_time.date() == (now - timezone.timedelta(days=1)).date():
        return "Hier"
    else:
        return msg_time.strftime("%d/%m/%y")

def format_time_long(dt):
    if not dt: return ""
    now = timezone.localtime(timezone.now())
    msg_time = timezone.localtime(dt)
    if msg_time.date() == now.date():
        return "Aujourd'hui à " + msg_time.strftime("%H:%M")
    elif msg_time.date() == (now - timezone.timedelta(days=1)).date():
        return "Hier à " + msg_time.strftime("%H:%M")
    else:
        return msg_time.strftime("%d/%m/%Y %H:%M")

def get_live_properties():
    """Fetch live properties from the main site API with 5 min caching to avoid API limits during 3s polling."""
    cached = cache.get('live_properties_v2')
    if cached:
        return cached
    try:
        resp = requests.get('https://logersenegal.com/api/properties/', timeout=3)
        if resp.status_code == 200:
            data = resp.json()
            results = data.get('results', data) if isinstance(data, dict) else data
            
            formatted = []
            for item in results:
                prop_id = item.get('id', '')
                title = item.get('title', '') or item.get('name', 'Propriété')
                price = item.get('price', 0)
                desc = item.get('description', '')
                
                # Image extraction logic
                image_url = 'https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=800&q=80'
                
                # Check root level image fields
                if item.get('image_url'):
                    image_url = item['image_url']
                elif item.get('image'):
                    image_url = item['image']
                    
                # Check nested images array
                if item.get('images') and isinstance(item['images'], list) and len(item['images']) > 0:
                    first_img = item['images'][0]
                    if isinstance(first_img, dict):
                        image_url = first_img.get('image_url', first_img.get('image', image_url))
                    elif isinstance(first_img, str):
                        image_url = first_img
                
                # Ensure the URL is absolute
                if image_url.startswith('/'):
                    image_url = f"https://logersenegal.com{image_url}"
                    
                formatted.append({
                    'id': str(prop_id),
                    'title': title,
                    'price': float(price) if price else 0.0,
                    'description': desc,
                    'image_url': image_url,
                    'url': f'https://logersenegal.com/annonces/{prop_id}/'
                })
            
            cache.set('live_properties_v2', formatted, 300) # Cache for 5 minutes
            return formatted
    except Exception as e:
        logger.error(f"Error fetching live properties: {e}")
    
    # Fallback to local DB if API is unreachable
    return list(Property.objects.all().values('id', 'title', 'price', 'description', 'image_url', 'url'))

def global_landing_view(request):
    """Global landing page (Terminal Hub) shown before login."""
    return render(request, 'chat/landing.html')

def custom_login_view(request):
    """Simple login view for agents and managers."""
    if request.user.is_authenticated:
        return redirect('select_portal')
        

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('select_portal')
    else:
        form = AuthenticationForm()

    return render(request, 'chat/login.html', {'form': form})

@login_required(login_url='login')
def select_portal_view(request):
    """View to choose between Agent Console and Manager Dashboard."""
    return render(request, 'chat/select_portal.html', {'user': request.user})

def custom_logout_view(request):
    """Logout view."""
    logout(request)
    return redirect('login')

@login_required(login_url='login')
def dashboard_view(request):
    """Main Agent Chat Dashboard. Réservé aux agents uniquement."""
    # Refuser l'accès si l'utilisateur n'est pas un AGENT
    # (ne jamais modifier le rôle silencieusement en base de données)
    if request.user.role != User.RoleEnum.AGENT and not request.user.is_superuser:
        return redirect('login')
        
    # Ensure some mock data exists for testing if properties/templates are empty
    if not Property.objects.exists():
        Property.objects.create(
            title="Appartement F4 Haut Standing - Ouakam",
            price=450000.00,
            description="Superbe appartement de 4 pièces avec vue sur mer, cuisine équipée, parking sécurisé et climatisation.",
            image_url="https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=400&q=80",
            url="https://logersn.com/bien/apt-ouakam-f4"
        )
        Property.objects.create(
            title="Studio meublé - Almadies",
            price=35000.00,
            description="Studio chic meublé avec toutes charges comprises (électricité, eau, wifi haut débit). Ménage inclus.",
            image_url="https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=400&q=80",
            url="https://logersn.com/bien/studio-almadies"
        )
        Property.objects.create(
            title="Villa avec piscine - Saly",
            price=1200000.00,
            description="Grande villa contemporaine de 4 chambres, grand jardin avec piscine privative. Quartier calme et résidentiel.",
            image_url="https://images.unsplash.com/photo-1613977257363-707ba9348227?auto=format&fit=crop&w=400&q=80",
            url="https://logersn.com/bien/villa-saly-piscine"
        )

    if not QuickTemplate.objects.exists():
        QuickTemplate.objects.create(
            title="Accueil Client",
            content="Bonjour ! Je suis ravi de vous aider. Quel type de bien recherchez-vous aujourd'hui et dans quel quartier ?",
            category="UTILITY"
        )
        QuickTemplate.objects.create(
            title="Confirmation Visite",
            content="Votre visite pour le bien [Nom du bien] est confirmée pour demain à [Heure]. Un agent vous attendra sur place.",
            category="UTILITY"
        )
        QuickTemplate.objects.create(
            title="Relance Prospect",
            content="Bonjour ! Avez-vous pu regarder les photos du logement que je vous ai envoyé hier ? N'hésitez pas si vous avez des questions.",
            category="MARKETING"
        )

    return render(request, 'chat/dashboard.html', {
        'user': request.user,
        'districts': District.objects.all(),
        'property_types': PropertyType.objects.all(),
    })

def download_whatsapp_media_async(media_id, message_id):
    """
    Downloads media from WhatsApp asynchronously and saves it locally.
    Updates the Message.attachment_url once downloaded.
    """
    from django.core.files.base import ContentFile
    try:
        wa_token = os.getenv('WA_ACCESS_TOKEN')
        if not wa_token:
            logger.error("No WA_ACCESS_TOKEN found for media download")
            return
            
        headers = {'Authorization': f'Bearer {wa_token}'}
        resp = requests.get(f'https://graph.facebook.com/v17.0/{media_id}/', headers=headers, timeout=10)
        
        if resp.status_code == 200:
            media_info = resp.json()
            media_url = media_info.get('url')
            mime_type = media_info.get('mime_type', 'application/octet-stream')
            
            # Simple extension mapping
            ext = mime_type.split('/')[-1] if '/' in mime_type else 'bin'
            if ext == 'jpeg': ext = 'jpg'
            elif ';' in ext: ext = ext.split(';')[0]
            
            if media_url:
                media_resp = requests.get(media_url, headers=headers, timeout=20)
                if media_resp.status_code == 200:
                    msg = Message.objects.get(id=message_id)
                    fs = FileSystemStorage(location=settings.MEDIA_ROOT)
                    filename = fs.save(f"wa_media_{media_id}.{ext}", ContentFile(media_resp.content))
                    # URL without the full domain to match standard relative media paths
                    file_url = f"/media/{filename}"
                    msg.attachment_url = file_url
                    msg.save()
                    logger.info(f"Successfully downloaded and saved media for message {message_id}")
                else:
                    logger.error(f"Failed to download media bits for {media_id}: HTTP {media_resp.status_code}")
        else:
            logger.error(f"Failed to fetch media url for {media_id}: HTTP {resp.status_code}")
    except Exception as e:
        logger.error(f"Exception during async media download: {str(e)}")

@csrf_exempt
def whatsapp_webhook(request):
    """
    Webhook receiver for Meta WhatsApp Cloud API.
    GET: Token verification challenge from Meta.
    POST: Receiving messages and logging them.
    """
    if request.method == 'GET':
        verify_token = os.getenv('WA_VERIFY_TOKEN')
        mode = request.GET.get('hub.mode')
        token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')
        
        if mode and token:
            if mode == 'subscribe' and token == verify_token:
                logger.info("Webhook WhatsApp vérifié avec succès.")
                return HttpResponse(challenge)
            else:
                logger.warning("Vérification webhook échouée : token invalide.")
                return HttpResponse('Forbidden', status=403)
        return HttpResponse('Bad Request', status=400)
        
    elif request.method == 'POST':
        try:
            body = json.loads(request.body.decode('utf-8'))
            logger.info(f"Webhook Payload: {json.dumps(body)}")
            
            # Check if it is a WhatsApp message status change or incoming message
            entry = body.get('entry', [])
            if not entry:
                return JsonResponse({'status': 'no_entries'}, status=200)
                
            changes = entry[0].get('changes', [])
            if not changes:
                return JsonResponse({'status': 'no_changes'}, status=200)
                
            value = changes[0].get('value', {})
            statuses_list = value.get('statuses', [])
            
            # 1. Handle WhatsApp Status Updates (sent, delivered, read)
            if statuses_list:
                status_data = statuses_list[0]
                msg_id = status_data.get('id')
                status_str = status_data.get('status', '').upper()
                
                new_status = None
                if status_str == 'SENT':
                    new_status = Message.StatusEnum.SENT
                elif status_str == 'DELIVERED':
                    new_status = Message.StatusEnum.DELIVERED
                elif status_str == 'READ':
                    new_status = Message.StatusEnum.READ
                
                if new_status:
                    Message.objects.filter(msg_id=msg_id).update(status=new_status)
                    logger.info(f"WhatsApp Message Status updated: {msg_id} -> {status_str}")
                    
                    # Broadcast status update to all connected agents
                    channel_layer = get_channel_layer()
                    async_to_sync(channel_layer.group_send)(
                        'agents_group',
                        {
                            'type': 'chat_update',
                            'event_type': 'status_update',
                            'msg_id': msg_id,
                            'status': status_str
                        }
                    )
                    
                return JsonResponse({'status': 'status_updated'}, status=200)
            
            messages_list = value.get('messages', [])
            if not messages_list:
                return JsonResponse({'status': 'no_message_data'}, status=200)
                
            message_data = messages_list[0]
            contact_data = value.get('contacts', [{}])[0]
            
            sender_phone = message_data.get('from')
            sender_name = contact_data.get('profile', {}).get('name', 'Client WhatsApp')
            message_type = message_data.get('type')
            
            content = ""
            attachment_url = None
            
            # Extract content based on message type
            if message_type == 'text':
                content = message_data.get('text', {}).get('body', '')
            elif message_type == 'image':
                media_id = message_data.get('image', {}).get('id')
                content = message_data.get('image', {}).get('caption', '[Image WhatsApp]')
                attachment_url = f"/api/media/{media_id}/" if media_id else None
            elif message_type == 'document':
                media_id = message_data.get('document', {}).get('id')
                content = message_data.get('document', {}).get('filename', '[Document WhatsApp]')
                attachment_url = f"/api/media/{media_id}/" if media_id else None
            elif message_type == 'audio':
                media_id = message_data.get('audio', {}).get('id')
                content = "[Note Vocale WhatsApp]"
                attachment_url = f"/api/media/{media_id}/" if media_id else None
            elif message_type == 'video':
                media_id = message_data.get('video', {}).get('id')
                content = message_data.get('video', {}).get('caption', '[Vidéo WhatsApp]')
                attachment_url = f"/api/media/{media_id}/" if media_id else None
            elif message_type == 'location':
                loc = message_data.get('location', {})
                content = f"Localisation : Lat {loc.get('latitude')}, Lng {loc.get('longitude')}"
            elif message_type == 'interactive':
                interactive_data = message_data.get('interactive', {})
                if interactive_data.get('type') == 'button_reply':
                    content = interactive_data.get('button_reply', {}).get('title', '')
                    interactive_id = interactive_data.get('button_reply', {}).get('id', '')
                elif interactive_data.get('type') == 'list_reply':
                    content = interactive_data.get('list_reply', {}).get('title', '')
                    interactive_id = interactive_data.get('list_reply', {}).get('id', '')
                else:
                    content = "[Message Interactif]"
                    interactive_id = None
            else:
                content = f"[{message_type.capitalize()} Message]"
                
            if message_type != 'interactive':
                interactive_id = None

            # 1. Get or Create user
            username = f"wa_{sender_phone}"
            client_user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'phone_number': sender_phone,
                    'first_name': sender_name,
                    'role': User.RoleEnum.CLIENT
                }
            )
            if not created and not client_user.phone_number:
                client_user.phone_number = sender_phone
                client_user.save()
                
            # 2. Get or Create conversation
            conversation = Conversation.objects.filter(
                participants=client_user,
                is_whatsapp=True
            ).order_by('-created_at').first()
            
            if not conversation:
                conversation = Conversation.objects.create(
                    topic=f"WhatsApp de {sender_name}",
                    is_whatsapp=True,
                    status=Conversation.StatusEnum.PENDING
                )
                conversation.participants.add(client_user)
                agents = User.objects.filter(role=User.RoleEnum.AGENT)
                conversation.participants.add(*agents)
                
                # --- NOUVEAU FLUX INTERACTIF WHATSAPP ---
                interactive_payload = {
                    "type": "button",
                    "body": {
                        "text": "Bienvenue chez Loger Sénégal ! 🏡\nQuel est votre projet immobilier aujourd'hui ?"
                    },
                    "action": {
                        "buttons": [
                            {
                                "type": "reply",
                                "reply": {
                                    "id": "PROJET_ACHETER",
                                    "title": "Acheter"
                                }
                            },
                            {
                                "type": "reply",
                                "reply": {
                                    "id": "PROJET_LOUER",
                                    "title": "Louer"
                                }
                            }
                        ]
                    }
                }
                
                if not client_user.is_blacklisted:
                    welcome_text = "Menu de bienvenue envoyé."
                    
                    # Send welcome interactive message
                    success, msg_id = trigger_meta_whatsapp_api(sender_phone, interactive_payload=interactive_payload)
                    
                    # Save it in DB
                    system_user = User.objects.filter(is_superuser=True).first()
                    if not system_user and agents.exists():
                        system_user = agents.first()
                        
                    Message.objects.create(
                        conversation=conversation,
                        sender=system_user if system_user else client_user,
                        content=welcome_text,
                        status=Message.StatusEnum.SENT if success else Message.StatusEnum.SENT,
                        msg_id=msg_id if msg_id else ""
                    )
            elif conversation.status == Conversation.StatusEnum.CLOSED:
                conversation.status = Conversation.StatusEnum.PENDING
                conversation.save()
            
            conversation.last_message_at = timezone.now()
            conversation.save()

            # --- FLUX INTERACTIF CONTINUATION ---
            if interactive_id and not client_user.is_blacklisted:
                # Etape 1: Projet
                if interactive_id in ['PROJET_ACHETER', 'PROJET_LOUER']:
                    conversation.client_project = content
                    conversation.save()
                    
                    if interactive_id == 'PROJET_ACHETER':
                        interactive_payload = {
                            "type": "list",
                            "header": {"type": "text", "text": "Acheter un bien"},
                            "body": {"text": "Quel type de bien souhaitez-vous acheter ?"},
                            "footer": {"text": "Loger Sénégal"},
                            "action": {
                                "button": "Choisir le type",
                                "sections": [{
                                    "title": "Types de biens",
                                    "rows": [
                                        {"id": "ACHAT_APPARTEMENT", "title": "Appartement"},
                                        {"id": "ACHAT_STUDIO", "title": "Studio"},
                                        {"id": "ACHAT_VILLA", "title": "Villa"},
                                        {"id": "ACHAT_TERRAIN", "title": "Terrain"}
                                    ]
                                }]
                            }
                        }
                        trigger_meta_whatsapp_api(sender_phone, interactive_payload=interactive_payload)
                        
                    elif interactive_id == 'PROJET_LOUER':
                        interactive_payload = {
                            "type": "button",
                            "body": {"text": "Quel type de location recherchez-vous ?"},
                            "action": {
                                "buttons": [
                                    {"type": "reply", "reply": {"id": "LOUER_LONGUE", "title": "Longue durée"}},
                                    {"type": "reply", "reply": {"id": "LOUER_MEUBLE", "title": "Logement meublé"}}
                                ]
                            }
                        }
                        trigger_meta_whatsapp_api(sender_phone, interactive_payload=interactive_payload)

                # Etape 2 (Louer) : Choix Longue durée ou Meublé
                elif interactive_id == 'LOUER_MEUBLE':
                    final_msg = "Excellent choix ! 🛋️\nUn de nos conseillers spécialisés en logements meublés va prendre le relais dans un instant pour vous proposer nos meilleures offres."
                    success, final_msg_id = trigger_meta_whatsapp_api(sender_phone, final_msg)
                    system_agent = User.objects.filter(is_superuser=True).first()
                    Message.objects.create(
                        conversation=conversation,
                        sender=system_agent if system_agent else client_user,
                        content=final_msg,
                        status=Message.StatusEnum.SENT if success else Message.StatusEnum.SENT,
                        msg_id=final_msg_id if final_msg_id else ""
                    )

                elif interactive_id == 'LOUER_LONGUE':
                    interactive_payload = {
                        "type": "list",
                        "header": {"type": "text", "text": "Location Longue Durée"},
                        "body": {"text": "Quel type de bien recherchez-vous ?"},
                        "footer": {"text": "Loger Sénégal"},
                        "action": {
                            "button": "Choisir le type",
                            "sections": [{
                                "title": "Types de biens",
                                "rows": [
                                    {"id": "LTYPE_CHAMBRE", "title": "Chambre"},
                                    {"id": "LTYPE_STUDIO", "title": "Studio"},
                                    {"id": "LTYPE_APPARTEMENT", "title": "Appartement"},
                                    {"id": "LTYPE_VILLA", "title": "Villa"}
                                ]
                            }]
                        }
                    }
                    trigger_meta_whatsapp_api(sender_phone, interactive_payload=interactive_payload)

                # Etape 3 (Location Longue Durée) : Sous-types
                elif interactive_id == 'LTYPE_CHAMBRE':
                    interactive_payload = {
                        "type": "button",
                        "body": {"text": "Quel type de chambre recherchez-vous ?"},
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "CAT_CHAMBRE_SDB", "title": "Avec salle de bain"}},
                                {"type": "reply", "reply": {"id": "CAT_CHAMBRE_SIMPLE", "title": "Simple"}}
                            ]
                        }
                    }
                    trigger_meta_whatsapp_api(sender_phone, interactive_payload=interactive_payload)

                elif interactive_id == 'LTYPE_STUDIO':
                    interactive_payload = {
                        "type": "button",
                        "body": {"text": "Quel type de studio recherchez-vous ?"},
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "CAT_STUDIO_MINI", "title": "Mini studio"}},
                                {"type": "reply", "reply": {"id": "CAT_STUDIO_ENTRE", "title": "Studio entre salon"}},
                                {"type": "reply", "reply": {"id": "CAT_STUDIO_SEPARE", "title": "Studio séparé"}}
                            ]
                        }
                    }
                    trigger_meta_whatsapp_api(sender_phone, interactive_payload=interactive_payload)

                elif interactive_id == 'LTYPE_APPARTEMENT':
                    interactive_payload = {
                        "type": "button",
                        "body": {"text": "Combien de pièces pour votre appartement ?"},
                        "action": {
                            "buttons": [
                                {"type": "reply", "reply": {"id": "CAT_APPART_2CH", "title": "2 ch. + salon"}},
                                {"type": "reply", "reply": {"id": "CAT_APPART_3CH", "title": "3 ch. + salon"}},
                                {"type": "reply", "reply": {"id": "CAT_APPART_4CH", "title": "4 ch. + salon"}}
                            ]
                        }
                    }
                    trigger_meta_whatsapp_api(sender_phone, interactive_payload=interactive_payload)

                # Etape 4 : Choix du budget (Déclenché par Villa ou Sous-types de location)
                elif interactive_id.startswith('CAT_') or interactive_id == 'LTYPE_VILLA':
                    interactive_payload = {
                        "type": "list",
                        "header": {"type": "text", "text": "Budget"},
                        "body": {"text": "Quel est votre budget mensuel (en FCFA) ?"},
                        "footer": {"text": "Loger Sénégal"},
                        "action": {
                            "button": "Choisir le budget",
                            "sections": [{
                                "title": "Fourchettes de budget",
                                "rows": [
                                    {"id": "BUDGET_50_100", "title": "50k - 100k"},
                                    {"id": "BUDGET_100_200", "title": "100k - 200k"},
                                    {"id": "BUDGET_200_300", "title": "200k - 300k"},
                                    {"id": "BUDGET_300_400", "title": "300k - 400k"},
                                    {"id": "BUDGET_500_PLUS", "title": "Supérieur à 500k"}
                                ]
                            }]
                        }
                    }
                    trigger_meta_whatsapp_api(sender_phone, interactive_payload=interactive_payload)

                # Fin de parcours (Budget location sélectionné OU Type achat sélectionné)
                elif interactive_id.startswith('BUDGET_') or interactive_id.startswith('ACHAT_'):
                    final_msg = "Parfait ! 🚀 Vos critères ont été enregistrés.\nUn de nos conseillers va prendre le relais dans un instant pour vous accompagner de manière personnalisée et conviviale."
                    success, final_msg_id = trigger_meta_whatsapp_api(sender_phone, final_msg)
                    system_agent = User.objects.filter(is_superuser=True).first()
                    Message.objects.create(
                        conversation=conversation,
                        sender=system_agent if system_agent else client_user,
                        content=final_msg,
                        status=Message.StatusEnum.SENT if success else Message.StatusEnum.SENT,
                        msg_id=final_msg_id if final_msg_id else ""
                    )

            # 3. Parse URLs for properties
            urls = re.findall(r'(https?://\S+)', content)
            for url in urls:
                matched_property = Property.objects.filter(url__icontains=url.split('?')[0]).first()
                if matched_property:
                    conversation.topic = f"{sender_name} - {matched_property.title}"
                    conversation.save()
                    
                    system_agent = User.objects.filter(is_superuser=True).first()
                    if system_agent:
                        Message.objects.create(
                            conversation=conversation,
                            sender=system_agent,
                            content=f"[SYSTEME] Le client a partagé le bien : {matched_property.title} ({matched_property.price:,.0f} FCFA)"
                        )

            # 3.5 Intercept Satisfaction Rating
            rating_intercepted = False
            if conversation.survey_sent and conversation.satisfaction_rating is None and message_type == 'text':
                # Robust extraction: looks for a digit between 1 and 5 that is not part of a larger number
                rating_match = re.search(r'(?<!\d)([1-5])(?!\d)', content)
                if rating_match:
                    conversation.satisfaction_rating = int(rating_match.group(1))
                    conversation.save()
                    rating_intercepted = True
                    
                    # Send thank you message
                    thank_you_msg = "Merci beaucoup pour votre retour ! Excellente journée. 😊"
                    success, msg_id = trigger_meta_whatsapp_api(sender_phone, thank_you_msg)
                    
                    system_agent = User.objects.filter(is_superuser=True).first()
                    Message.objects.create(
                        conversation=conversation,
                        sender=system_agent if system_agent else client_user,
                        content=thank_you_msg,
                        status=Message.StatusEnum.SENT if success else Message.StatusEnum.SENT,
                        msg_id=msg_id if msg_id else ""
                    )

            # 4. Save the actual message (with msg_id and READ status since it is incoming)
            msg = Message.objects.create(
                conversation=conversation,
                sender=client_user,
                content=content,
                attachment_url=attachment_url,
                msg_id=message_data.get('id'),
                status=Message.StatusEnum.READ
            )
            
            if media_id:
                import threading
                threading.Thread(target=download_whatsapp_media_async, args=(media_id, msg.id)).start()
            
            # 5. Update last message time and restart SLA countdown (only if not blacklisted)
            conversation.last_message_at = timezone.now()
            if not client_user.is_blacklisted:
                conversation.sla_started_at = timezone.now()
                conversation.sla_enabled = True
            conversation.save()
            
            # Broadcast new message to all connected agents
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'agents_group',
                {
                    'type': 'chat_update',
                    'event_type': 'new_message',
                    'conversation_id': str(conversation.id)
                }
            )
            
            return JsonResponse({'status': 'message_received'}, status=200)
            
        except Exception as e:
            logger.error(f"Error handling webhook: {str(e)}", exc_info=True)
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required(login_url='login')
def sync_messages(request):
    """
    Polled endpoint to get:
    1. List of conversations for the current agent.
    2. Active messages for the selected conversation.
    """
    agent = request.user
    active_conv_id = request.GET.get('conversation_id')
    
    # Handle search query
    query = request.GET.get('q', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    
    # Get all conversations the agent has access to
    if agent.is_superuser or agent.role == User.RoleEnum.MANAGER:
        conversations = Conversation.objects.all()
    else:
        conversations = Conversation.objects.filter(
            Q(assigned_to=agent) | Q(participants=agent) | Q(status=Conversation.StatusEnum.PENDING)
        )
        
    if query:
        conversations = conversations.filter(
            Q(participants__first_name__icontains=query) |
            Q(participants__phone_number__icontains=query) |
            Q(messages__content__icontains=query)
        ).distinct()
        
    if date_from:
        conversations = conversations.filter(created_at__gte=date_from)
    if date_to:
        from datetime import datetime, timedelta
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
            conversations = conversations.filter(created_at__lt=date_to_obj)
        except ValueError:
            pass
            
    conversations = conversations.annotate(
        client_unread_count=Count(
            'messages',
            filter=Q(messages__sender__role=User.RoleEnum.CLIENT, messages__is_read=False)
        ),
        client_last_message_at_annotated=Max(
            'messages__created_at',
            filter=Q(messages__sender__role=User.RoleEnum.CLIENT),
            output_field=models.DateTimeField()
        )
    ).prefetch_related(
        'participants',
        Prefetch('messages', queryset=Message.objects.order_by('-created_at'), to_attr='cached_messages')
    ).order_by('-last_message_at', '-created_at')
    
    conv_data = []
    for conv in conversations:
        # Find client in participants
        client = next((p for p in conv.participants.all() if p.role == User.RoleEnum.CLIENT), None)
        client_name = client.first_name if client else "Client Inconnu"
        client_phone = client.phone_number if client else "N/A"
        is_blacklisted = client.is_blacklisted if client else False
        
        last_msg = conv.cached_messages[0] if conv.cached_messages else None
        last_msg_content = last_msg.content if last_msg else "Aucun message"
        last_msg_time = format_time_short(last_msg.created_at) if last_msg else ""
        
        if isinstance(conv.client_last_message_at_annotated, str):
            from django.utils.dateparse import parse_datetime
            parsed_dt = parse_datetime(conv.client_last_message_at_annotated)
            last_client_msg_at = parsed_dt.isoformat() if parsed_dt else None
        else:
            last_client_msg_at = conv.client_last_message_at_annotated.isoformat() if conv.client_last_message_at_annotated else None
        
        assigned_to_name = conv.assigned_to.get_full_name() or conv.assigned_to.username if conv.assigned_to else None
        
        # Check if last message is from client for SLA tracking
        is_last_msg_from_client = (last_msg.sender.role == User.RoleEnum.CLIENT) if last_msg else False
        
        # Count unread messages from client
        unread_count = conv.client_unread_count
        
        conv_data.append({
            'id': str(conv.id),
            'topic': conv.topic,
            'client_name': client_name,
            'client_phone': client_phone,
            'status': conv.status,
            'is_whatsapp': conv.is_whatsapp,
            'assigned_to': assigned_to_name,
            'assigned_to_username': conv.assigned_to.username if conv.assigned_to else None,
            'last_message': last_msg_content[:50] + ("..." if len(last_msg_content) > 50 else ""),
            'last_message_time': last_msg_time,
            'updated_at': conv.updated_at.isoformat(),
            'tags': [t.strip() for t in conv.tags.split(',') if t.strip()] if conv.tags else [],
            'pipeline_stage': conv.pipeline_stage,
            'pipeline_stage_display': conv.get_pipeline_stage_display(),
            'client_last_message_at': last_client_msg_at,
            'is_last_msg_from_client': is_last_msg_from_client,
            'sla_limit_minutes': conv.sla_limit_minutes,
            'sla_started_at': conv.sla_started_at.isoformat() if conv.sla_started_at else None,
            'sla_enabled': conv.sla_enabled,
            'unread_count': unread_count,
            'is_blacklisted': is_blacklisted,
            'is_assistance_paid': client.is_assistance_paid if client else False,
        })
        
    messages_data = []
    active_conv_info = None
    suggested_properties_data = []
    active_reminders_data = []
    
    if active_conv_id:
        try:
            if agent.is_superuser or agent.role == User.RoleEnum.MANAGER:
                active_conv = Conversation.objects.get(id=active_conv_id)
            else:
                queryset = Conversation.objects.filter(
                    Q(participants=agent) | Q(status=Conversation.StatusEnum.PENDING)
                ).distinct()
                active_conv = get_object_or_404(queryset, id=active_conv_id)
            
            # Fetch active client
            client = active_conv.participants.filter(role=User.RoleEnum.CLIENT).first()
            
            # Locate last message sent by client
            last_client_msg = active_conv.messages.filter(sender__role=User.RoleEnum.CLIENT).order_by('-created_at').first()
            client_last_message_at = last_client_msg.created_at.isoformat() if last_client_msg else active_conv.created_at.isoformat()
            
            # Mark incoming messages as read
            active_conv.messages.filter(sender__role=User.RoleEnum.CLIENT, is_read=False).update(is_read=True)
            
            active_last_msg = active_conv.messages.all().order_by('-created_at').first()
            active_is_last_msg_from_client = (active_last_msg.sender.role == User.RoleEnum.CLIENT) if active_last_msg else False
            
            active_conv_info = {
                'id': str(active_conv.id),
                'topic': active_conv.topic,
                'client_name': client.first_name if client else "Client",
                'client_phone': client.phone_number if client else "N/A",
                'is_blacklisted': client.is_blacklisted if client else False,
                'is_assistance_paid': client.is_assistance_paid if client else False,
                'is_whatsapp': active_conv.is_whatsapp,
                'status': active_conv.status,
                'assigned_to': active_conv.assigned_to.get_full_name() or active_conv.assigned_to.username if active_conv.assigned_to else None,
                'assigned_to_id': str(active_conv.assigned_to.id) if active_conv.assigned_to else None,
                'client_last_message_at': client_last_message_at,
                'tags': [t.strip() for t in active_conv.tags.split(',') if t.strip()] if active_conv.tags else [],
                'notes': active_conv.notes,
                'pipeline_stage': active_conv.pipeline_stage,
                'pipeline_stage_display': active_conv.get_pipeline_stage_display(),
                'is_last_msg_from_client': active_is_last_msg_from_client,
                'sla_limit_minutes': active_conv.sla_limit_minutes,
                'sla_started_at': active_conv.sla_started_at.isoformat() if active_conv.sla_started_at else None,
                'survey_sent': active_conv.survey_sent,
                'satisfaction_rating': active_conv.satisfaction_rating,
                'client_project': active_conv.client_project,
                'client_property_type': active_conv.client_property_type,
                'client_zone': active_conv.client_zone,
            }
            
            # Fetch messages
            msgs = active_conv.messages.all().order_by('created_at')
            for msg in msgs:
                messages_data.append({
                    'id': str(msg.id),
                    'sender_name': msg.sender.first_name or msg.sender.username,
                    'sender_role': msg.sender.role,
                    'sender_is_self': msg.sender == agent,
                    'content': msg.content or "",
                    'attachment_url': msg.attachment_url,
                    'status': msg.status,
                    'created_at': format_time_long(msg.created_at)
                })
                
            # Fetch real properties from API
            live_properties = get_live_properties()
                
            # Smart AI Property Recommendation Engine
            client_msgs = msgs.filter(sender__role=User.RoleEnum.CLIENT)
            combined_text = " ".join([m.content.lower() for m in client_msgs])
            
            if combined_text:
                for prop in live_properties:
                    keywords = ['studio', 'meublé', 'villa', 'piscine', 'terrain', 'appartement', 'almadies', 'ouakam', 'saly', 'diamniadio']
                    matched = False
                    for kw in keywords:
                        if kw in combined_text and (kw in prop['title'].lower() or kw in prop['description'].lower()):
                            matched = True
                            break
                    if matched:
                        suggested_properties_data.append(prop)
            suggested_properties_data = suggested_properties_data[:2]
            
            # Fetch reminders for active conversation
            active_reminders = active_conv.reminders.filter(is_done=False).order_by('remind_at')
            active_reminders_data = [{
                'id': str(r.id),
                'title': r.title,
                'remind_at': r.remind_at.isoformat(),
                'is_done': r.is_done
            } for r in active_reminders]
            
        except Conversation.DoesNotExist:
            pass

    # Load all active reminders for current agent to trigger alerts
    agent_reminders = Reminder.objects.filter(agent=agent, is_done=False).order_by('remind_at')
    agent_reminders_data = [{
        'id': str(r.id),
        'conversation_id': str(r.conversation.id),
        'client_name': r.conversation.participants.filter(role=User.RoleEnum.CLIENT).first().first_name if r.conversation.participants.filter(role=User.RoleEnum.CLIENT).first() else "Client",
        'title': r.title,
        'remind_at': r.remind_at.isoformat()
    } for r in agent_reminders]

    # Load templates and properties for UI helper
    properties = get_live_properties()
    templates = list(QuickTemplate.objects.all().values('id', 'title', 'content', 'category'))

    return JsonResponse({
        'conversations': conv_data,
        'messages': messages_data,
        'active_conversation': active_conv_info,
        'suggested_properties': suggested_properties_data,
        'properties': properties,
        'templates': templates,
        'active_reminders': active_reminders_data,
        'agent_reminders': agent_reminders_data,
        'server_now': timezone.now().isoformat()
    })

@login_required(login_url='login')
@require_POST
def toggle_blacklist(request):
    import json
    try:
        data = json.loads(request.body)
        conversation_id = data.get('conversation_id')
        if not conversation_id:
            return JsonResponse({'status': 'error', 'message': 'Missing conversation_id'}, status=400)
            
        conversation = get_object_or_404(Conversation, id=conversation_id)
        client = conversation.participants.filter(role=User.RoleEnum.CLIENT).first()
        if not client:
            return JsonResponse({'status': 'error', 'message': 'No client found in conversation'}, status=404)
            
        client.is_blacklisted = not client.is_blacklisted
        client.save()
        
        # If blacklisted, disable SLA
        if client.is_blacklisted:
            conversation.sla_enabled = False
            conversation.save()
            
        return JsonResponse({
            'status': 'success', 
            'is_blacklisted': client.is_blacklisted,
            'message': f"Le client a été {'blacklisté' if client.is_blacklisted else 'retiré de la blacklist'}."
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required(login_url='login')
def send_message(request):
    """
    Endpoint to send message from the agent.
    If is_whatsapp=True, calls Meta Cloud API to send the WhatsApp text.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    try:
        data = json.loads(request.body)
        conversation_id = data.get('conversation_id')
        content = data.get('content', '')
        attachment_url = data.get('attachment_url', None)
        
        if not conversation_id or (not content and not attachment_url):
            return JsonResponse({'error': 'Missing conversation_id or content/attachment'}, status=400)
            
        if request.user.is_superuser or request.user.role == User.RoleEnum.MANAGER:
            conversation = get_object_or_404(Conversation, id=conversation_id)
        else:
            conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
        
        # Save the message in our DB
        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=content,
            attachment_url=attachment_url
        )
        
        conversation.last_message_at = timezone.now()
        conversation.sla_started_at = None
        conversation.sla_enabled = False # Agent replied, disable SLA warning until client replies
        conversation.save()
        
        # If it is a WhatsApp conversation, invoke Meta Cloud API
        if conversation.is_whatsapp:
            client = conversation.participants.filter(role=User.RoleEnum.CLIENT).first()
            if client and client.phone_number:
                # Trigger the webhook request to Meta
                success, msg_id = trigger_meta_whatsapp_api(client.phone_number, content, attachment_url)
                if success and msg_id:
                    message.msg_id = msg_id
                    message.status = Message.StatusEnum.SENT
                    message.save()
                else:
                    logger.warning("WhatsApp API call failed or in Mock Mode (credentials missing in .env).")
                    
                    # Create an automatic mockup system message
                    Message.objects.create(
                        conversation=conversation,
                        sender=User.objects.filter(is_superuser=True).first() or request.user,
                        content=f"[SYSTEME] Échec de l'envoi WhatsApp en direct. Simulation locale active."
                    )
            
        return JsonResponse({
            'status': 'sent',
            'message': {
                'id': str(message.id),
                'sender_name': request.user.first_name or request.user.username,
                'content': message.content,
                'created_at': format_time_long(message.created_at)
            }
        })
        
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)

def trigger_meta_whatsapp_api(to_phone, message_text=None, attachment_url=None, interactive_payload=None):
    """
    Wrapper to call Meta's Cloud API endpoint.
    Returns (success, msg_id) tuple.
    """
    token = os.getenv('WA_ACCESS_TOKEN')
    phone_id = os.getenv('WA_PHONE_NUMBER_ID')
    version = os.getenv('WA_API_VERSION', 'v19.0')
    
    # If credentials are not set, simulate successful delivery (Mock Mode for local tests)
    if not token or token == "your_permanent_access_token_here" or not phone_id:
        import uuid
        mock_id = f"mock_wamid_{uuid.uuid4().hex}"
        logger.info(f"MOCK API WhatsApp ➔ To: {to_phone} | Msg: {message_text} | Interactive: {interactive_payload is not None} | ID: {mock_id}")
        return True, mock_id
        
    url = f"https://graph.facebook.com/{version}/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_phone,
    }
    
    if interactive_payload:
        payload["type"] = "interactive"
        payload["interactive"] = interactive_payload
    elif attachment_url:
        # Detect the type from extension
        ext = attachment_url.split('?')[0].split('.')[-1].lower() if '.' in attachment_url else ''
        
        image_exts = {'jpg', 'jpeg', 'png', 'webp', 'gif'}
        video_exts = {'mp4', '3gp', 'mov'}
        audio_exts = {'mp3', 'ogg', 'm4a', 'wav', 'aac'}
        
        if ext in image_exts:
            payload["type"] = "image"
            payload["image"] = {
                "link": attachment_url
            }
            if message_text:
                payload["image"]["caption"] = message_text
        elif ext in video_exts:
            payload["type"] = "video"
            payload["video"] = {
                "link": attachment_url
            }
            if message_text:
                payload["video"]["caption"] = message_text
        elif ext in audio_exts:
            payload["type"] = "audio"
            payload["audio"] = {
                "link": attachment_url
            }
        else:
            # Default to document
            filename = attachment_url.split('/')[-1].split('?')[0] or "document.pdf"
            payload["type"] = "document"
            payload["document"] = {
                "link": attachment_url,
                "filename": filename
            }
            if message_text:
                payload["document"]["caption"] = message_text
    else:
        payload["type"] = "text"
        payload["text"] = {
            "preview_url": True,
            "body": message_text or ""
        }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        logger.info(f"Meta response Status: {response.status_code} | Payload: {response.text}")
        if response.status_code in [200, 201]:
            res_json = response.json()
            msg_id = res_json.get('messages', [{}])[0].get('id')
            return True, msg_id
        return False, None
    except Exception as e:
        logger.error(f"Error calling Meta Cloud API: {str(e)}")
        return False, None

@login_required(login_url='login')
def claim_conversation(request):
    """
    Endpoint for an agent to claim an unassigned conversation.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    try:
        data = json.loads(request.body)
        conversation_id = data.get('conversation_id')
        
        if not conversation_id:
            return JsonResponse({'error': 'Missing conversation_id'}, status=400)
            
        if request.user.is_superuser or request.user.role == User.RoleEnum.MANAGER:
            conversation = get_object_or_404(Conversation, id=conversation_id)
        else:
            queryset = Conversation.objects.filter(
                Q(participants=request.user) | Q(status=Conversation.StatusEnum.PENDING)
            ).distinct()
            conversation = get_object_or_404(queryset, id=conversation_id)
        
        # Claim
        conversation.assigned_to = request.user
        conversation.status = Conversation.StatusEnum.ACTIVE
        conversation.save()
        
        # Log a system message notifying agents
        Message.objects.create(
            conversation=conversation,
            sender=User.objects.filter(is_superuser=True).first() or request.user,
            content=f"[SYSTEME] La conversation est maintenant gérée par l'agent {request.user.get_full_name() or request.user.username}."
        )
        
        return JsonResponse({'status': 'claimed'})
    except Exception as e:
        logger.error(f"Error claiming conversation: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)


@login_required(login_url='login')
def update_conversation_notes(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    try:
        data = json.loads(request.body)
        conversation_id = data.get('conversation_id')
        notes = data.get('notes', '')
        if request.user.is_superuser or request.user.role == User.RoleEnum.MANAGER:
            conversation = get_object_or_404(Conversation, id=conversation_id)
        else:
            conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
        conversation.notes = notes
        conversation.save()
        return JsonResponse({'status': 'updated'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required(login_url='login')
def update_conversation_pipeline(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    try:
        data = json.loads(request.body)
        conversation_id = data.get('conversation_id')
        stage = data.get('pipeline_stage')
        if not stage:
            return JsonResponse({'error': 'Missing pipeline_stage'}, status=400)
        
        if request.user.is_superuser or request.user.role == User.RoleEnum.MANAGER:
            conversation = get_object_or_404(Conversation, id=conversation_id)
        else:
            conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
        old_stage_display = conversation.get_pipeline_stage_display()
        conversation.pipeline_stage = stage
        conversation.save()
        
        new_stage_display = conversation.get_pipeline_stage_display()
        # Log system message
        Message.objects.create(
            conversation=conversation,
            sender=User.objects.filter(is_superuser=True).first() or request.user,
            content=f"[SYSTEME] Étape du prospect modifiée : {old_stage_display} ➔ {new_stage_display}."
        )
        return JsonResponse({'status': 'updated'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required(login_url='login')
def create_reminder(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    try:
        data = json.loads(request.body)
        conversation_id = data.get('conversation_id')
        title = data.get('title')
        remind_at_str = data.get('remind_at')
        
        if not conversation_id or not title or not remind_at_str:
            return JsonResponse({'error': 'Missing required fields'}, status=400)
            
        if request.user.is_superuser or request.user.role == User.RoleEnum.MANAGER:
            conversation = get_object_or_404(Conversation, id=conversation_id)
        else:
            conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
        remind_at = parse_datetime(remind_at_str)
        if not remind_at:
            return JsonResponse({'error': 'Invalid datetime format'}, status=400)
            
        # Ensure it is timezone-aware
        if timezone.is_naive(remind_at):
            remind_at = timezone.make_aware(remind_at, timezone.get_current_timezone())
            
        Reminder.objects.create(
            conversation=conversation,
            agent=request.user,
            title=title,
            remind_at=remind_at
        )
        return JsonResponse({'status': 'created'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required(login_url='login')
def complete_reminder(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    try:
        data = json.loads(request.body)
        reminder_id = data.get('reminder_id')
        if not reminder_id:
            return JsonResponse({'error': 'Missing reminder_id'}, status=400)
            
        if request.user.is_superuser or request.user.role == User.RoleEnum.MANAGER:
            reminder = get_object_or_404(Reminder, id=reminder_id)
        else:
            reminder = get_object_or_404(Reminder, id=reminder_id, agent=request.user)
        reminder.is_done = True
        reminder.save()
        return JsonResponse({'status': 'completed'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required(login_url='login')
def export_leads_csv(request):
    status_filter = request.GET.get('status', 'ACTIVE')
    tag_filter = request.GET.get('tag', '')
    agent_filter = request.GET.get('agent', 'MY')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    if request.user.is_superuser or request.user.role == User.RoleEnum.MANAGER:
        conversations = Conversation.objects.all()
    else:
        conversations = Conversation.objects.filter(participants=request.user)
    
    if start_date_str:
        try:
            # Using basic date parsing to avoid timezone-naive issues
            start_date = timezone.datetime.strptime(start_date_str, '%Y-%m-%d').date()
            conversations = conversations.filter(created_at__date__gte=start_date)
        except (ValueError, TypeError):
            pass
            
    if end_date_str:
        try:
            end_date = timezone.datetime.strptime(end_date_str, '%Y-%m-%d').date()
            conversations = conversations.filter(created_at__date__lte=end_date)
        except (ValueError, TypeError):
            pass
    
    if status_filter and status_filter != 'ALL':
        conversations = conversations.filter(status=status_filter)
        
    if agent_filter == 'MY':
        conversations = conversations.filter(assigned_to=request.user)
        
    filtered_conversations = []
    for conv in conversations:
        if tag_filter:
            tags_list = [t.strip().lower() for t in conv.tags.split(',') if t.strip()]
            if tag_filter.lower() not in tags_list:
                continue
        filtered_conversations.append(conv)
        
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="leads_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    # Write UTF-8 BOM so Excel opens it with correct French accents encoding
    response.write(u'\ufeff'.encode('utf8'))
    
    writer = csv.writer(response, delimiter=';')
    writer.writerow([
        'Date de Contact',
        'Nom du Prospect', 
        'Téléphone', 
        'Status', 
        'Canal', 
        'Agent Assigné', 
        'Étape du Pipeline', 
        'Projet Client',
        'Type de Bien',
        'Zone / Quartier',
        'Note Satisfaction (/5)',
        'Étiquettes / Catégories', 
        'Notes de l\'Agent', 
        'Dernier Message'
    ])
    
    for conv in filtered_conversations:
        client = conv.participants.filter(role=User.RoleEnum.CLIENT).first()
        client_name = client.get_full_name() or client.username if client else "N/A"
        client_phone = client.phone_number if client else "N/A"
        
        last_msg = conv.messages.all().order_by('-created_at').first()
        last_msg_content = last_msg.content if last_msg else ""
        
        # Determine client project (Rent/Sale) properly
        projet = conv.client_project or ""
        
        writer.writerow([
            timezone.localtime(conv.created_at).strftime("%Y-%m-%d %H:%M") if conv.created_at else "",
            client_name,
            client_phone,
            conv.get_status_display(),
            'WhatsApp' if conv.is_whatsapp else 'Web Chat',
            conv.assigned_to.get_full_name() or conv.assigned_to.username if conv.assigned_to else 'Non assigné',
            conv.get_pipeline_stage_display(),
            projet,
            conv.client_property_type or "",
            conv.client_zone or "",
            conv.satisfaction_rating or "",
            conv.tags,
            conv.notes,
            last_msg_content
        ])
        
    return response

@login_required(login_url='login')
def update_conversation_tags(request):
    """
    POST: Update comma-separated tags for a conversation.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    try:
        data = json.loads(request.body)
        conversation_id = data.get('conversation_id')
        tags_list = data.get('tags', [])
        
        if not conversation_id:
            return JsonResponse({'error': 'Missing conversation_id'}, status=400)
            
        if request.user.is_superuser or request.user.role == User.RoleEnum.MANAGER:
            conversation = get_object_or_404(Conversation, id=conversation_id)
        else:
            conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
        conversation.tags = ",".join([t.strip() for t in tags_list if t.strip()])
        conversation.save()
        
        return JsonResponse({'status': 'updated', 'tags': tags_list})
    except Exception as e:
        logger.error(f"Error updating conversation tags: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)

@login_required(login_url='login')
def update_conversation_sla_limit(request):
    """
    POST: Update the SLA duration limit in minutes for a conversation.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    try:
        data = json.loads(request.body)
        conversation_id = data.get('conversation_id')
        limit = data.get('sla_limit_minutes')
        
        if not conversation_id or limit is None:
            return JsonResponse({'error': 'Missing conversation_id or sla_limit_minutes'}, status=400)
            
        if request.user.is_superuser or request.user.role == User.RoleEnum.MANAGER:
            conversation = get_object_or_404(Conversation, id=conversation_id)
        else:
            conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
        conversation.sla_limit_minutes = int(limit)
        conversation.sla_started_at = timezone.now()
        conversation.save()
        
        return JsonResponse({'status': 'updated', 'sla_limit_minutes': conversation.sla_limit_minutes})
    except Exception as e:
        logger.error(f"Error updating SLA limit: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)

@login_required(login_url='login')
def manager_dashboard_view(request):
    """Manager Dashboard Panel."""
    if request.user.role != User.RoleEnum.MANAGER and not request.user.is_superuser:
        return redirect('dashboard')
    return render(request, 'chat/manager_dashboard.html', {
        'user': request.user,
        'districts': District.objects.all(),
        'property_types': PropertyType.objects.all(),
    })

@login_required(login_url='login')
def close_conversation(request):
    """POST: Close a conversation (sets status to CLOSED)."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    try:
        data = json.loads(request.body)
        conversation_id = data.get('conversation_id')
        if not conversation_id:
            return JsonResponse({'error': 'Missing conversation_id'}, status=400)
            
        if request.user.is_superuser or request.user.role == User.RoleEnum.MANAGER:
            conversation = get_object_or_404(Conversation, id=conversation_id)
        else:
            conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
        conversation.status = Conversation.StatusEnum.CLOSED
        conversation.sla_started_at = None
        conversation.save()
        
        # Log system message
        Message.objects.create(
            conversation=conversation,
            sender=User.objects.filter(is_superuser=True).first() or request.user,
            content="[SYSTEME] La conversation a été résolue par l'agent."
        )
        return JsonResponse({'status': 'closed'})
    except Exception as e:
        logger.error(f"Error closing conversation: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)

@login_required(login_url='login')
def manager_stats(request):
    """GET: Returns manager stats with date filtering and sectors grouping."""
    if request.user.role != User.RoleEnum.MANAGER and not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    try:
        range_filter = request.GET.get('range', 'all').strip()
        now = timezone.now()
        start_date = None
        end_date = None
        
        if range_filter == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif range_filter == 'yesterday':
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            start_date = today_start - timedelta(days=1)
            end_date = today_start
        elif range_filter == '7days':
            start_date = now - timedelta(days=7)
        elif range_filter == '30days':
            start_date = now - timedelta(days=30)

        # Base querysets
        clients_qs = User.objects.filter(role=User.RoleEnum.CLIENT)
        convs_qs = Conversation.objects.all()
        matches_qs = PartnerMatch.objects.all()
        
        # Apply date filters
        if start_date:
            clients_qs = clients_qs.filter(date_joined__gte=start_date)
            convs_qs = convs_qs.filter(created_at__gte=start_date)
            matches_qs = matches_qs.filter(created_at__gte=start_date)
        if end_date:
            clients_qs = clients_qs.filter(date_joined__lt=end_date)
            convs_qs = convs_qs.filter(created_at__lt=end_date)
            matches_qs = matches_qs.filter(created_at__lt=end_date)

        from .models import AssistancePayment, SystemSetting
        assistance_qs = AssistancePayment.objects.all()
        if start_date:
            assistance_qs = assistance_qs.filter(created_at__gte=start_date)
        if end_date:
            assistance_qs = assistance_qs.filter(created_at__lt=end_date)
        
        total_assistance_revenue = sum(p.amount for p in assistance_qs)

        total_clients = clients_qs.count()
        total_agents = User.objects.filter(role=User.RoleEnum.AGENT).count()
        
        total_convs = convs_qs.count()
        active_convs = convs_qs.filter(status=Conversation.StatusEnum.ACTIVE).count()
        closed_convs = convs_qs.filter(status=Conversation.StatusEnum.CLOSED).count()
        # "En attente" = Non-assignées + (Assignées avec SLA en cours d'attente)
        pending_convs = convs_qs.filter(
            Q(status=Conversation.StatusEnum.PENDING) | 
            Q(status=Conversation.StatusEnum.ACTIVE, sla_started_at__isnull=False)
        ).count()
        
        # 1. Partner Match & Visit Stats
        total_matches = matches_qs.count()
        won_matches = matches_qs.filter(status=PartnerMatch.StatusEnum.WON).count()
        visited_matches = matches_qs.filter(status=PartnerMatch.StatusEnum.VISITED).count()
        lost_matches = matches_qs.filter(status=PartnerMatch.StatusEnum.LOST).count()
        pending_matches = matches_qs.filter(status=PartnerMatch.StatusEnum.PENDING).count()
        
        conversion_rate = 0.0
        if total_matches > 0:
            conversion_rate = (won_matches / total_matches) * 100
            
        # 2. SLA Violations calculation
        sla_violations = 0
        active_convs_qs = convs_qs.filter(status=Conversation.StatusEnum.ACTIVE, sla_started_at__isnull=False)
        for c in active_convs_qs:
            last_msg = c.messages.order_by('-created_at').first()
            if last_msg and last_msg.sender.role == User.RoleEnum.CLIENT:
                limit_mins = c.sla_limit_minutes or 15
                elapsed = now - c.sla_started_at
                if elapsed.total_seconds() > limit_mins * 60:
                    sla_violations += 1
        
        # 3. Sectors / Zones grouping (Real data)
        from django.db.models import Count
        sectors_data = matches_qs.values('zone').annotate(count=Count('id')).order_by('-count')
        sectors_list = [{'zone': item['zone'], 'count': item['count']} for item in sectors_data if item['zone']]
        
        # Conversations per agent
        agents = User.objects.filter(role=User.RoleEnum.AGENT)
        agents_list = []
        for a in agents:
            assigned_count = Conversation.objects.filter(assigned_to=a, status=Conversation.StatusEnum.ACTIVE).count()
            agents_list.append({
                'id': str(a.id),
                'name': a.get_full_name() or a.username,
                'username': a.username,
                'active_conversations_count': assigned_count
            })
            
        # 4. Satisfaction Rating
        rated_convs = convs_qs.filter(satisfaction_rating__isnull=False)
        avg_rating = 0.0
        total_rated = rated_convs.count()
        if total_rated > 0:
            avg_rating = sum(c.satisfaction_rating for c in rated_convs) / total_rated
            
        recent_surveys = []
        for c in rated_convs.order_by('-last_message_at')[:10]:
            client = c.participants.filter(role=User.RoleEnum.CLIENT).first()
            client_name = client.get_full_name() if client else f"Client #{str(c.id)[:4]}"
            recent_surveys.append({
                'id': str(c.id),
                'client_name': client_name,
                'rating': c.satisfaction_rating,
                'comment': getattr(c, 'satisfaction_comment', ''),
                'agent_name': c.assigned_to.get_full_name() if c.assigned_to else "Non assigné",
                'date': c.last_message_at.strftime('%d/%m/%Y %H:%M') if c.last_message_at else c.created_at.strftime('%d/%m/%Y %H:%M')
            })
            
        return JsonResponse({
            'total_clients': total_clients,
            'total_agents': total_agents,
            'total_conversations': total_convs,
            'active_conversations': active_convs,
            'pending_conversations': pending_convs,
            'closed_conversations': closed_convs,
            'total_matches': total_matches,
            'won_matches': won_matches,
            'visited_matches': visited_matches,
            'lost_matches': lost_matches,
            'pending_matches': pending_matches,
            'conversion_rate': round(conversion_rate, 1),
            'sla_violations': sla_violations,
            'avg_satisfaction': round(avg_rating, 1),
            'total_rated': total_rated,
            'recent_surveys': recent_surveys,
            'sectors': sectors_list,
            'agents_performance': agents_list,
            'total_assistance_revenue': total_assistance_revenue,
            'assistance_fee': float(SystemSetting.get_fee())
        })
    except Exception as e:
        logger.error(f"Error getting manager stats: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)

@login_required(login_url='login')
def manager_agents(request):
    """
    GET: List all agents.
    POST: Create a new agent.
    """
    if request.user.role != User.RoleEnum.MANAGER and not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    if request.method == 'GET':
        agents = User.objects.filter(role=User.RoleEnum.AGENT)
        agents_data = [{
            'id': str(a.id),
            'username': a.username,
            'first_name': a.first_name,
            'last_name': a.last_name,
            'phone_number': a.phone_number or '',
            'is_active': a.is_active
        } for a in agents]
        return JsonResponse({'agents': agents_data})
        
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
            first_name = data.get('first_name', '')
            last_name = data.get('last_name', '')
            phone_number = data.get('phone_number', '')
            
            if not username or not password:
                return JsonResponse({'error': 'Username and password are required'}, status=400)
                
            if User.objects.filter(username=username).exists():
                return JsonResponse({'error': 'A user with this username already exists'}, status=400)
                
            new_agent = User.objects.create_user(
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name,
                phone_number=phone_number,
                role=User.RoleEnum.AGENT
            )
            return JsonResponse({
                'status': 'created',
                'agent': {
                    'id': str(new_agent.id),
                    'username': new_agent.username,
                    'first_name': new_agent.first_name,
                    'last_name': new_agent.last_name
                }
            })
        except Exception as e:
            logger.error(f"Error creating agent: {str(e)}", exc_info=True)
            return JsonResponse({'error': str(e)}, status=500)
            
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required(login_url='login')
def manager_delegate(request):
    """POST: Delegate a conversation to an agent."""
    if request.user.role != User.RoleEnum.MANAGER and not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    try:
        data = json.loads(request.body)
        conversation_id = data.get('conversation_id')
        agent_id = data.get('agent_id') # Can be null or 'unassigned' to clear
        
        if not conversation_id:
            return JsonResponse({'error': 'Missing conversation_id'}, status=400)
            
        conversation = get_object_or_404(Conversation, id=conversation_id)
        
        if agent_id and agent_id != 'unassigned':
            agent = get_object_or_404(User, id=agent_id, role=User.RoleEnum.AGENT)
            conversation.assigned_to = agent
            conversation.status = Conversation.StatusEnum.ACTIVE
            
            # Make sure agent is a participant
            if not conversation.participants.filter(id=agent.id).exists():
                conversation.participants.add(agent)
                
            agent_name = agent.get_full_name() or agent.username
            msg_content = f"[SYSTEME] La conversation a été déléguée à l'agent {agent_name} par le manager."
        else:
            conversation.assigned_to = None
            msg_content = "[SYSTEME] La conversation a été libérée (non assignée) par le manager."
            
        conversation.save()
        
        # Log system message
        Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=msg_content
        )
        return JsonResponse({'status': 'delegated'})
    except Exception as e:
        logger.error(f"Error delegating conversation: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)

from urllib.parse import quote

@login_required(login_url='login')
def search_partners(request):
    """GET: Search and filter partners dynamically."""
    zone_filter = request.GET.get('zone', '').strip()
    type_filter = request.GET.get('property_type', '').strip()
    query = request.GET.get('query', '').strip()
    
    partners = Partner.objects.all()
    
    if zone_filter:
        partners = partners.filter(zone__icontains=zone_filter)
    if type_filter:
        partners = partners.filter(property_type__icontains=type_filter)
    if query:
        partners = partners.filter(
            Q(name__icontains=query) | Q(ref__icontains=query) | Q(zone__icontains=query)
        )
        
    partners_data = [{
        'id': str(p.id),
        'name': p.name,
        'ref': p.ref or '',
        'contact_1': p.contact_1,
        'contact_2': p.contact_2 or '',
        'zone': p.zone,
        'property_type': p.property_type,
        'meteo': p.meteo,
        'meteo_display': p.get_meteo_display()
    } for p in partners]
    
    return JsonResponse({'partners': partners_data})

@login_required(login_url='login')
def create_partner_match(request):
    """POST: Match client with partner and notify client + generate wa.me link for partner."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    try:
        data = json.loads(request.body)
        conversation_id = data.get('conversation_id')
        partner_id = data.get('partner_id')
        visitor_name = data.get('visitor_name', '').strip()
        visitor_phone = data.get('visitor_phone', '').strip()
        price = data.get('price')
        zone = data.get('zone', '').strip()
        
        if not conversation_id or not partner_id or not visitor_name or not visitor_phone or price is None or not zone:
            return JsonResponse({'error': 'Tous les champs (Client, Partenaire, Visiteur, Prix, Zone) sont obligatoires.'}, status=400)
            
        # Get conversation & partner
        if request.user.is_superuser or request.user.role == User.RoleEnum.MANAGER:
            conversation = get_object_or_404(Conversation, id=conversation_id)
        else:
            conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
            
        partner = get_object_or_404(Partner, id=partner_id)
        
        # Create partner match in database
        match = PartnerMatch.objects.create(
            conversation=conversation,
            partner=partner,
            visitor_name=visitor_name,
            visitor_phone=visitor_phone,
            price=float(price),
            zone=zone,
            status=PartnerMatch.StatusEnum.PENDING
        )
        
        # 1. Format the message for the CLIENT
        client = conversation.participants.filter(role=User.RoleEnum.CLIENT).first()
        client_name = client.first_name if client else "Client"
        
        client_text = (
            f"Bonjour {client_name} ! 😊\n\n"
            f"Pour la visite du bien situé à *{zone}* (Budget : {float(price):,.0f} FCFA), "
            f"nous vous mettons en rapport avec notre partenaire local :\n"
            f"👤 *{partner.name}*\n"
            f"📞 Tel : *{partner.contact_1}*\n\n"
            f"Vous pouvez le contacter de la part de *Loger Sénégal* pour planifier la visite."
        )
        
        # Save message to conversation & send if WhatsApp is active
        client_message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=client_text
        )
        
        conversation.last_message_at = timezone.now()
        conversation.save()
        
        if conversation.is_whatsapp and client and client.phone_number:
            success, msg_id = trigger_meta_whatsapp_api(client.phone_number, client_text)
            if success and msg_id:
                client_message.msg_id = msg_id
                client_message.status = Message.StatusEnum.SENT
                client_message.save()
                
        # 2. Format the message for the PARTNER (Pre-filled wa.me link)
        partner_text = (
            f"Bonjour {partner.name} ! 🏡\n\n"
            f"Un client de *Loger Sénégal* va vous contacter pour visiter le bien situé à *{zone}* (Budget : {float(price):,.0f} FCFA).\n\n"
            f"📋 *Détails du Visiteur :*\n"
            f"- Nom : {visitor_name}\n"
            f"- Contact : {visitor_phone}\n\n"
            f"Merci de lui réserver un excellent accueil ! 🙏"
        )
        
        # Hashed URL for whatsapp web redirection
        encoded_text = quote(partner_text)
        wa_link = f"https://wa.me/{partner.contact_1.replace(' ', '').replace('+', '')}?text={encoded_text}"
        
        # 3. Add system log in chat
        system_text = (
            f"[SYSTEME] Prospect mis en relation avec le partenaire {partner.name} ({partner.contact_1}). "
            f"Visiteur : {visitor_name} ({visitor_phone}) pour le bien à {zone} (Budget: {float(price):,.0f} FCFA)."
        )
        Message.objects.create(
            conversation=conversation,
            sender=User.objects.filter(is_superuser=True).first() or request.user,
            content=system_text
        )
        
        return JsonResponse({
            'status': 'created',
            'match_id': str(match.id),
            'wa_link': wa_link
        })
        
    except Exception as e:
        logger.error(f"Error creating partner match: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)

@login_required(login_url='login')
def manager_matches(request):
    """
    GET: List all matches (for manager).
    POST: Update status of a match.
    """
    if request.user.role != User.RoleEnum.MANAGER and not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    if request.method == 'GET':
        range_val = request.GET.get('range', 'all')
        matches = PartnerMatch.objects.all()
        
        from django.utils import timezone
        from datetime import timedelta
        now = timezone.now()
        start_date = None
        end_date = None
        
        if range_val == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif range_val == 'yesterday':
            start_date = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=1)
        elif range_val == '7days':
            start_date = now - timedelta(days=7)
        elif range_val == '30days':
            start_date = now - timedelta(days=30)
            
        if start_date:
            matches = matches.filter(created_at__gte=start_date)
        if end_date:
            matches = matches.filter(created_at__lt=end_date)
            
        matches = matches.order_by('-created_at')
        matches_data = []
        for m in matches:
            client = m.conversation.participants.filter(role=User.RoleEnum.CLIENT).first()
            matches_data.append({
                'id': str(m.id),
                'client_name': client.get_full_name() or client.username if client else 'Client Inconnu',
                'client_phone': client.phone_number if client else 'N/A',
                'partner_name': m.partner.name,
                'partner_contact': m.partner.contact_1,
                'visitor_name': m.visitor_name,
                'visitor_phone': m.visitor_phone,
                'price': float(m.price),
                'zone': m.zone,
                'status': m.status,
                'status_display': m.get_status_display(),
                'conversation_id': str(m.conversation.id) if m.conversation else '',
                'created_at': m.created_at.strftime('%d/%m/%Y %H:%M')
            })
        return JsonResponse({'matches': matches_data})
        
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            match_id = data.get('match_id')
            new_status = data.get('status')
            
            if not match_id or not new_status:
                return JsonResponse({'error': 'Missing match_id or status'}, status=400)
                
            match = get_object_or_404(PartnerMatch, id=match_id)
            if new_status not in PartnerMatch.StatusEnum.values:
                return JsonResponse({'error': 'Invalid status'}, status=400)
                
            old_status_display = match.get_status_display()
            match.status = new_status
            match.save()
            new_status_display = match.get_status_display()
            
            # Log system message in conversation
            Message.objects.create(
                conversation=match.conversation,
                sender=request.user,
                content=f"[SYSTEME] Suivi Visite Partenaire : Le statut de la visite est passé de '{old_status_display}' à '{new_status_display}'."
            )
            
            return JsonResponse({'status': 'updated'})
        except Exception as e:
            logger.error(f"Error updating match status: {str(e)}", exc_info=True)
            return JsonResponse({'error': str(e)}, status=500)
            
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required(login_url='login')
def manager_visits(request):
    """
    GET: List all agent visits (for manager).
    POST: Update status of a visit.
    """
    if request.user.role != User.RoleEnum.MANAGER and not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    if request.method == 'GET':
        range_val = request.GET.get('range', 'all')
        visits = Visit.objects.all()
        
        from django.utils import timezone
        from datetime import timedelta
        now = timezone.now()
        start_date = None
        end_date = None
        
        if range_val == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif range_val == 'yesterday':
            start_date = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=1)
        elif range_val == '7days':
            start_date = now - timedelta(days=7)
        elif range_val == '30days':
            start_date = now - timedelta(days=30)
            
        if start_date:
            visits = visits.filter(created_at__gte=start_date)
        if end_date:
            visits = visits.filter(created_at__lt=end_date)
            
        visits = visits.order_by('-created_at')
        visits_data = []
        for v in visits:
            visits_data.append({
                'id': str(v.id),
                'client_name': v.client_name,
                'client_phone': v.client_phone,
                'agent_name': v.agent.get_full_name() or v.agent.username if v.agent else 'Inconnu',
                'property_title': v.property_title,
                'visit_date': v.visit_date.strftime('%d/%m/%Y %H:%M') if v.visit_date else '',
                'status': v.status,
                'status_display': v.get_status_display(),
                'notes': v.notes,
                'conversation_id': str(v.conversation.id) if v.conversation else '',
                'created_at': v.created_at.strftime('%d/%m/%Y %H:%M')
            })
        return JsonResponse({'visits': visits_data})
        
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            visit_id = data.get('visit_id')
            new_status = data.get('status')
            
            if not visit_id or not new_status:
                return JsonResponse({'error': 'Missing visit_id or status'}, status=400)
                
            visit = get_object_or_404(Visit, id=visit_id)
            if new_status not in Visit.StatusEnum.values:
                return JsonResponse({'error': 'Invalid status'}, status=400)
                
            old_status_display = visit.get_status_display()
            visit.status = new_status
            visit.save()
            new_status_display = visit.get_status_display()
            
            # Log system message in conversation
            Message.objects.create(
                conversation=visit.conversation,
                sender=request.user,
                content=f"[SYSTEME] Suivi Visite Agent : Le statut de la visite est passé de '{old_status_display}' à '{new_status_display}'."
            )
            
            return JsonResponse({'status': 'updated'})
        except Exception as e:
            logger.error(f"Error updating visit status: {str(e)}", exc_info=True)
            return JsonResponse({'error': str(e)}, status=500)
            
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required(login_url='login')
def whatsapp_media_proxy(request, media_id):
    """
    Proxy to fetch secure media from Meta API and serve it to the authenticated frontend.
    """
    token = os.getenv('WA_ACCESS_TOKEN')
    version = os.getenv('WA_API_VERSION', 'v19.0')
    
    if not token:
        return HttpResponse('Unauthorized', status=401)
        
    # 1. Fetch media URL metadata
    url_req = f"https://graph.facebook.com/{version}/{media_id}"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.get(url_req, headers=headers, timeout=5)
        if resp.status_code != 200:
            logger.error(f"Media Proxy Meta Error: {resp.text}")
            return HttpResponse('Media not found', status=404)
            
        media_data = resp.json()
        media_url = media_data.get('url')
        mime_type = media_data.get('mime_type', 'application/octet-stream')
        
        # Simple extension guessing
        file_extension = mime_type.split('/')[-1] if '/' in mime_type else 'bin'
        if mime_type == 'audio/ogg; codecs=opus': file_extension = 'ogg'
        
        if not media_url:
            return HttpResponse('Invalid media data', status=404)
            
        is_download = request.GET.get('download') == '1'
        
        # 2. Fetch binary data, forwarding Range headers for seeking support
        req_headers = {"Authorization": f"Bearer {token}"}
        if 'Range' in request.headers:
            req_headers['Range'] = request.headers['Range']
            
        # Download the file completely into memory (fast from Meta CDN, avoids holding open connections)
        # UPDATE: Now using stream=True and StreamingHttpResponse to fix audio/video playback issues
        img_resp = requests.get(media_url, headers=req_headers, stream=True, timeout=20)
        
        if img_resp.status_code in [200, 206]:
            from django.http import StreamingHttpResponse
            response = StreamingHttpResponse(img_resp.iter_content(chunk_size=8192), content_type=mime_type, status=img_resp.status_code)
            
            # Forward essential headers for audio/video playback
            if 'Content-Length' in img_resp.headers:
                response['Content-Length'] = img_resp.headers['Content-Length']
            if 'Content-Range' in img_resp.headers:
                response['Content-Range'] = img_resp.headers['Content-Range']
            if 'Accept-Ranges' in img_resp.headers:
                response['Accept-Ranges'] = img_resp.headers['Accept-Ranges']
                
            if is_download:
                response['Content-Disposition'] = f'attachment; filename="media_{media_id}.{file_extension}"'
            else:
                response['Content-Disposition'] = f'inline; filename="media_{media_id}.{file_extension}"'
                
            return response
            
        return HttpResponse('Failed to download media bytes', status=img_resp.status_code)
    except Exception as e:
        logger.error(f"Exception in media proxy: {str(e)}", exc_info=True)
        return HttpResponse('Internal Server Error', status=500)

@login_required(login_url='login')
def manager_templates_api(request):
    """
    CRUD API for QuickTemplates. Managers only.
    """
    if request.user.role not in [User.RoleEnum.MANAGER] and not request.user.is_superuser:
        return JsonResponse({'error': 'Non autorisé'}, status=403)
        
    if request.method == 'GET':
        templates = QuickTemplate.objects.all().order_by('title')
        data = [{'id': str(t.id), 'title': t.title, 'category': t.category, 'content': t.content} for t in templates]
        return JsonResponse({'templates': data})
        
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            t_id = data.get('id')
            title = data.get('title', '').strip()
            content = data.get('content', '').strip()
            category = data.get('category', 'UTILITY')
            
            if not title or not content:
                return JsonResponse({'error': 'Le titre et le contenu sont obligatoires'}, status=400)
                
            if t_id:
                t = get_object_or_404(QuickTemplate, id=t_id)
                t.title = title
                t.content = content
                t.category = category
                t.save()
                return JsonResponse({'status': 'updated'})
            else:
                QuickTemplate.objects.create(title=title, content=content, category=category)
                return JsonResponse({'status': 'created'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
            
    elif request.method == 'DELETE':
        try:
            data = json.loads(request.body)
            t_id = data.get('id')
            if not t_id:
                return JsonResponse({'error': 'ID obligatoire'}, status=400)
            get_object_or_404(QuickTemplate, id=t_id).delete()
            return JsonResponse({'status': 'deleted'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
            
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required(login_url='login')
@require_POST
def send_survey(request):
    try:
        data = json.loads(request.body)
        conversation_id = data.get('conversation_id')
        conversation = get_object_or_404(Conversation, id=conversation_id)
        
        if not conversation.is_whatsapp:
            return JsonResponse({'error': 'Enquête disponible uniquement pour WhatsApp'}, status=400)
            
        client = conversation.participants.filter(role=User.RoleEnum.CLIENT).first()
        if not client or not client.phone_number:
            return JsonResponse({'error': 'Client introuvable'}, status=400)
            
        # Build the survey link using the current host
        host = request.get_host()
        protocol = 'https' if request.is_secure() else 'http'
        survey_link = f"{protocol}://{host}/survey/{conversation.id}/"
        survey_text = f"Merci d'avoir contacté Loger Sénégal ! Pour nous aider à nous améliorer, pourriez-vous prendre 30 secondes pour évaluer notre service ?\nCliquez ici : {survey_link} ⭐"
        success, msg_id = trigger_meta_whatsapp_api(client.phone_number, survey_text)
        
        if success:
            conversation.survey_sent = True
            conversation.status = Conversation.StatusEnum.CLOSED
            conversation.save()
            
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=survey_text,
                status=Message.StatusEnum.SENT,
                msg_id=msg_id
            )
            return JsonResponse({'status': 'sent'})
        else:
            return JsonResponse({'error': "Échec de l'envoi de l'enquête"}, status=500)
            
    except Exception as e:
        logger.error(f"Error sending survey: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required(login_url='login')
@require_POST
def upload_media(request):
    try:
        if 'file' not in request.FILES:
            return JsonResponse({'error': 'Aucun fichier sélectionné'}, status=400)
            
        file = request.FILES['file']
        fs = FileSystemStorage(location=settings.MEDIA_ROOT)
        filename = fs.save(file.name, file)
        file_url = fs.url(filename)
        absolute_url = request.build_absolute_uri(file_url)
        
        return JsonResponse({'status': 'uploaded', 'url': absolute_url})
    except Exception as e:
        logger.error(f"Error uploading media: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required(login_url='login')
@require_POST
def update_conversation_sla_toggle(request):
    try:
        data = json.loads(request.body)
        conversation_id = data.get('conversation_id')
        sla_enabled = data.get('sla_enabled')
        
        conversation = get_object_or_404(Conversation, id=conversation_id)
        if request.user.role != User.RoleEnum.MANAGER and conversation.assigned_to != request.user:
            return JsonResponse({'error': 'Unauthorized'}, status=403)
            
        conversation.sla_enabled = sla_enabled
        conversation.save()
        
        return JsonResponse({'status': 'updated'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required(login_url='login')
@require_POST
def create_reminder(request):
    try:
        data = json.loads(request.body)
        conv_id = data.get('conversation_id')
        title = data.get('title')
        remind_at_str = data.get('remind_at')
        
        if not conv_id or not title or not remind_at_str:
            return JsonResponse({'error': 'Missing required fields'}, status=400)
            
        conv = get_object_or_404(Conversation, id=conv_id)
        remind_at = parse_datetime(remind_at_str)
        
        if not remind_at:
            return JsonResponse({'error': 'Invalid date format'}, status=400)
            
        reminder = Reminder.objects.create(
            conversation=conv,
            agent=request.user,
            title=title,
            remind_at=remind_at
        )
        
        return JsonResponse({'status': 'created', 'reminder_id': str(reminder.id)})
    except Exception as e:
        logger.error(f"Error creating reminder: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required(login_url='login')
@require_POST
def create_visit(request):
    try:
        data = json.loads(request.body)
        conv_id = data.get('conversation_id')
        visit_date_str = data.get('visit_date')
        property_title = data.get('property_title')
        client_name = data.get('client_name', '')
        client_phone = data.get('client_phone', '')
        notes = data.get('notes', '')
        
        if not conv_id or not visit_date_str or not property_title:
            return JsonResponse({'error': 'Missing required fields'}, status=400)
            
        conv = get_object_or_404(Conversation, id=conv_id)
        visit_date = parse_datetime(visit_date_str)
        
        if not visit_date:
            return JsonResponse({'error': 'Invalid date format'}, status=400)
            
        visit = Visit.objects.create(
            conversation=conv,
            agent=request.user,
            property_title=property_title,
            visit_date=visit_date,
            client_name=client_name,
            client_phone=client_phone,
            notes=notes,
            status=Visit.StatusEnum.PLANNED
        )
        
        conv.pipeline_stage = Conversation.PipelineStageEnum.VISIT
        conv.save()
        
        return JsonResponse({'status': 'success', 'visit_id': str(visit.id)})
    except Exception as e:
        logger.error(f"Error creating visit: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required(login_url='login')
@require_POST
def update_visit(request):
    try:
        data = json.loads(request.body)
        visit_id = data.get('visit_id')
        new_status = data.get('status')
        
        if not visit_id or not new_status:
            return JsonResponse({'error': 'Missing required fields'}, status=400)
            
        visit = get_object_or_404(Visit, id=visit_id)
        visit.status = new_status
        visit.save()
        
        # If visit completed, update pipeline stage to VISIT automatically
        if new_status == Visit.StatusEnum.COMPLETED.value:
            visit.conversation.pipeline_stage = Conversation.PipelineStageEnum.VISIT
            visit.conversation.save()
            
        return JsonResponse({'status': 'success'})
    except Exception as e:
        logger.error(f"Error updating visit: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required(login_url='login')
def list_visits(request):
    try:
        if request.user.role == User.RoleEnum.MANAGER or request.user.is_superuser:
            visits = Visit.objects.all().select_related('agent', 'conversation')
        else:
            visits = Visit.objects.filter(agent=request.user).select_related('agent', 'conversation')
            
        visits_data = []
        for v in visits.order_by('visit_date'):  # Ascending: upcoming visits first
            visits_data.append({
                'id': str(v.id),
                'property_title': v.property_title,
                'visit_date': v.visit_date.isoformat(),
                'status': v.status,
                'status_display': v.get_status_display(),
                'client_name': v.client_name,
                'client_phone': v.client_phone,
                'notes': v.notes,
                'agent_name': v.agent.get_full_name() or v.agent.username,
                'conv_id': str(v.conversation.id),
                'created_at': v.created_at.strftime('%d/%m/%Y %H:%M'),
            })
            
        return JsonResponse({'status': 'success', 'visits': visits_data})
    except Exception as e:
        logger.error(f"Error listing visits: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

@api_view(['POST'])
@permission_classes([AllowAny])
def mobile_login(request):
    try:
        username = request.data.get('username')
        password = request.data.get('password')
        if not username or not password:
            return JsonResponse({'error': 'Veuillez saisir votre nom d\'utilisateur et mot de passe.'}, status=400)
        
        user = authenticate(username=username, password=password)
        if not user:
            return JsonResponse({'error': 'Identifiants invalides.'}, status=400)
            
        if user.role not in [User.RoleEnum.AGENT, User.RoleEnum.MANAGER]:
            return JsonResponse({'error': 'Accès interdit. Réservé aux conseillers et managers.'}, status=403)
            
        token, created = Token.objects.get_or_create(user=user)
        return JsonResponse({
            'status': 'success',
            'token': token.key,
            'username': user.username,
            'full_name': user.get_full_name() or user.username,
            'role': user.role
        })
    except Exception as e:
        logger.error(f"Error in mobile login: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['GET'])
def mobile_conversations(request):
    try:
        # Returns conversations assigned to the current agent, or all if manager
        status_filter = request.query_params.get('status')
        
        if request.user.role == User.RoleEnum.MANAGER:
            convs = Conversation.objects.all()
        else:
            # Agents should see their own conversations PLUS any unassigned pending conversations
            convs = Conversation.objects.filter(
                Q(assigned_to=request.user) | 
                Q(status=Conversation.StatusEnum.PENDING, assigned_to__isnull=True)
            )
            
        if status_filter:
            convs = convs.filter(status=status_filter)
            
        data = []
        for c in convs.order_by('-last_message_at'):
            # Get client name/phone (which is the participant with role=CLIENT)
            client = c.participants.filter(role=User.RoleEnum.CLIENT).first()
            client_name = client.get_full_name() or client.username if client else "Client inconnu"
            client_phone = client.phone_number if client else ""
            
            # Get last message snippet
            last_msg = c.messages.order_by('-created_at').first()
            last_msg_text = last_msg.text if last_msg else ""
            last_msg_time = last_msg.created_at.isoformat() if last_msg else c.created_at.isoformat()
            
            data.append({
                'id': str(c.id),
                'client_name': client_name,
                'client_phone': client_phone,
                'status': c.status,
                'pipeline_stage': c.pipeline_stage,
                'last_message_text': last_msg_text,
                'last_message_time': last_msg_time,
                'unread_count': c.messages.filter(is_read=False).exclude(sender=request.user).count()
            })
            
        return JsonResponse({'status': 'success', 'conversations': data})
    except Exception as e:
        logger.error(f"Error listing mobile conversations: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['GET'])
def mobile_messages(request, conversation_id):
    try:
        conv = get_object_or_404(Conversation, id=conversation_id)
        # Check permissions
        if request.user.role != User.RoleEnum.MANAGER and conv.assigned_to != request.user:
            return JsonResponse({'error': 'Accès interdit'}, status=403)
            
        # Mark messages as read
        conv.messages.exclude(sender=request.user).update(is_read=True)
        
        msgs = conv.messages.order_by('created_at')
        data = []
        for m in msgs:
            data.append({
                'id': str(m.id),
                'sender_username': m.sender.username,
                'sender_role': m.sender.role,
                'text': m.text,
                'media_url': m.media_url if m.media_url else '',
                'mime_type': m.mime_type if m.mime_type else '',
                'created_at': m.created_at.isoformat(),
                'is_read': m.is_read
            })
            
        # Get conversation meta-info
        client = conv.participants.filter(role=User.RoleEnum.CLIENT).first()
        client_name = client.get_full_name() or client.username if client else "Client inconnu"
        client_phone = client.phone_number if client else ""
        
        return JsonResponse({
            'status': 'success',
            'client_name': client_name,
            'client_phone': client_phone,
            'pipeline_stage': conv.pipeline_stage,
            'messages': data
        })
    except Exception as e:
        logger.error(f"Error loading mobile messages: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['POST'])
def mobile_update_conversation(request):
    try:
        conversation_id = request.data.get('conversation_id')
        if not conversation_id:
            return JsonResponse({'error': 'Missing conversation_id'}, status=400)
            
        conv = get_object_or_404(Conversation, id=conversation_id)
        if request.user.role != User.RoleEnum.MANAGER and conv.assigned_to != request.user:
            return JsonResponse({'error': 'Accès interdit'}, status=403)
            
        updated_fields = []
        
        if 'pipeline_stage' in request.data:
            old_stage_display = conv.get_pipeline_stage_display()
            conv.pipeline_stage = request.data['pipeline_stage']
            new_stage_display = conv.get_pipeline_stage_display()
            Message.objects.create(
                conversation=conv,
                sender=User.objects.filter(is_superuser=True).first() or request.user,
                content=f"[SYSTEME] Étape du prospect modifiée : {old_stage_display} ➔ {new_stage_display}."
            )
            updated_fields.append('pipeline_stage')
            
        if 'notes' in request.data:
            conv.notes = request.data['notes']
            updated_fields.append('notes')
            
        if 'tags' in request.data:
            conv.tags = request.data['tags']
            updated_fields.append('tags')
            
        if 'client_project' in request.data:
            conv.client_project = request.data['client_project']
            updated_fields.append('client_project')
            
        if 'client_property_type' in request.data:
            conv.client_property_type = request.data['client_property_type']
            updated_fields.append('client_property_type')
            
        if 'client_zone' in request.data:
            conv.client_zone = request.data['client_zone']
            updated_fields.append('client_zone')
            
        if updated_fields:
            conv.save()
            
        return JsonResponse({'status': 'success', 'updated_fields': updated_fields})
    except Exception as e:
        logger.error(f"Error in mobile_update_conversation: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['GET'])
def mobile_properties(request):
    try:
        properties = get_live_properties()
        return JsonResponse({'status': 'success', 'properties': properties})
    except Exception as e:
        logger.error(f"Error in mobile_properties: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['GET'])
def mobile_partners(request):
    try:
        zone_filter = request.query_params.get('zone', '').strip()
        type_filter = request.query_params.get('property_type', '').strip()
        query = request.query_params.get('query', '').strip()
        
        partners = Partner.objects.all()
        
        if zone_filter:
            partners = partners.filter(zone__icontains=zone_filter)
        if type_filter:
            partners = partners.filter(property_type__icontains=type_filter)
        if query:
            partners = partners.filter(
                Q(name__icontains=query) | Q(ref__icontains=query) | Q(zone__icontains=query)
            )
            
        partners_data = [{
            'id': str(p.id),
            'name': p.name,
            'ref': p.ref or '',
            'contact_1': p.contact_1,
            'contact_2': p.contact_2 or '',
            'zone': p.zone,
            'property_type': p.property_type,
            'meteo': p.meteo,
            'meteo_display': p.get_meteo_display()
        } for p in partners]
        
        return JsonResponse({'status': 'success', 'partners': partners_data})
    except Exception as e:
        logger.error(f"Error in mobile_partners: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['POST'])
def mobile_create_partner_match(request):
    try:
        conversation_id = request.data.get('conversation_id')
        partner_id = request.data.get('partner_id')
        visitor_name = request.data.get('visitor_name', '').strip()
        visitor_phone = request.data.get('visitor_phone', '').strip()
        price = request.data.get('price')
        zone = request.data.get('zone', '').strip()
        
        if not conversation_id or not partner_id or not visitor_name or not visitor_phone or price is None or not zone:
            return JsonResponse({'error': 'Tous les champs sont obligatoires.'}, status=400)
            
        conv = get_object_or_404(Conversation, id=conversation_id)
        if request.user.role != User.RoleEnum.MANAGER and conv.assigned_to != request.user:
            return JsonResponse({'error': 'Accès interdit'}, status=403)
            
        partner = get_object_or_404(Partner, id=partner_id)
        
        match = PartnerMatch.objects.create(
            conversation=conv,
            partner=partner,
            visitor_name=visitor_name,
            visitor_phone=visitor_phone,
            price=float(price),
            zone=zone,
            status=PartnerMatch.StatusEnum.PENDING
        )
        
        Message.objects.create(
            conversation=conv,
            sender=User.objects.filter(is_superuser=True).first() or request.user,
            content=f"[PARTENAIRE] Visite proposée au partenaire {partner.name} pour {visitor_name} ({zone}, {price} FCFA)."
        )
        
        text_message = f"Bonjour {partner.name}, je te propose une visite pour {visitor_name} ({visitor_phone}) pour le bien à {zone} au prix de {price} FCFA."
        encoded_message = quote(text_message)
        wa_link = f"https://wa.me/{partner.contact_1}?text={encoded_message}"
        
        return JsonResponse({
            'status': 'success',
            'match_id': str(match.id),
            'wa_link': wa_link
        })
    except Exception as e:
        logger.error(f"Error in mobile_create_partner_match: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


def survey_page(request, conv_id):
    """
    Renders the satisfaction survey page for a client and saves their response.
    """
    conv = get_object_or_404(Conversation, id=conv_id)
    agent_name = conv.assigned_to.get_full_name() if conv.assigned_to else 'notre conseiller'
    
    if conv.satisfaction_rating is not None:
        return render(request, 'chat/survey.html', {
            'success': True,
            'already_submitted': True,
            'agent_name': agent_name
        })
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment', '').strip()
        if rating and rating.isdigit():
            conv.satisfaction_rating = int(rating)
            conv.satisfaction_comment = comment
            conv.save()
            return render(request, 'chat/survey.html', {
                'success': True,
                'already_submitted': False,
                'agent_name': agent_name
            })
            
    return render(request, 'chat/survey.html', {'success': False, 'conv': conv, 'agent_name': agent_name})


@login_required(login_url='login')
def agent_profile(request):
    """
    Renders the agent profile page with KPIs and recent feedback.
    """
    user = request.user
    
    # Calculate KPIs
    assigned_convs = Conversation.objects.filter(assigned_to=user)
    total_conversations = assigned_convs.count()
    total_won = assigned_convs.filter(pipeline_stage=Conversation.PipelineStageEnum.WON).count()
    total_visits = Visit.objects.filter(agent=user, status=Visit.StatusEnum.COMPLETED).count()
    
    # Average satisfaction rating
    rated_convs = assigned_convs.filter(satisfaction_rating__isnull=False)
    if rated_convs.exists():
        avg_satisfaction = sum(c.satisfaction_rating for c in rated_convs) / rated_convs.count()
        avg_satisfaction = round(avg_satisfaction, 1)
    else:
        avg_satisfaction = None
        
    # Recent feedback
    recent_feedback = []
    for conv in rated_convs.order_by('-last_message_at')[:10]:
        client = conv.participants.filter(role=User.RoleEnum.CLIENT).first()
        client_name = client.get_full_name() if client else f"Client #{str(conv.id)[:4]}"
        recent_feedback.append({
            'client_name': client_name,
            'rating': conv.satisfaction_rating,
            'comment': getattr(conv, 'satisfaction_comment', ''),
            'date': conv.last_message_at.strftime('%d/%m/%Y') if conv.last_message_at else conv.created_at.strftime('%d/%m/%Y')
        })
        
    context = {
        'total_conversations': total_conversations,
        'total_won': total_won,
        'total_visits': total_visits,
        'avg_satisfaction': avg_satisfaction,
        'recent_feedback': recent_feedback,
    }
    return render(request, 'chat/agent_profile.html', context)


@login_required(login_url='login')
@require_POST
def mark_assistance_paid(request):
    import json
    from .models import SystemSetting, AssistancePayment
    try:
        data = json.loads(request.body)
        conversation_id = data.get('conversation_id')
        if not conversation_id:
            return JsonResponse({'status': 'error', 'message': 'Missing conversation_id'}, status=400)
            
        conversation = get_object_or_404(Conversation, id=conversation_id)
        client = conversation.participants.filter(role=User.RoleEnum.CLIENT).first()
        if not client:
            return JsonResponse({'status': 'error', 'message': 'No client found in conversation'}, status=404)
            
        if client.is_assistance_paid:
            return JsonResponse({'status': 'error', 'message': 'Client already paid assistance'}, status=400)
            
        # Update client
        client.is_assistance_paid = True
        client.save()
        
        # Create payment record
        fee = SystemSetting.get_fee()
        AssistancePayment.objects.create(
            client=client,
            agent=request.user,
            amount=fee
        )
            
        return JsonResponse({
            'status': 'success',
            'is_assistance_paid': True,
            'message': f"Paiement d'assistance de {fee} CFA validé pour {client.get_full_name() or client.username}."
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required(login_url='login')
@require_POST
def update_system_settings(request):
    import json
    from .models import SystemSetting
    
    # Restrict to Super Admin or Manager
    if not (request.user.is_superuser or request.user.role == User.RoleEnum.MANAGER):
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)
        
    try:
        data = json.loads(request.body)
        new_fee = data.get('assistance_fee')
        
        if new_fee is None:
            return JsonResponse({'status': 'error', 'message': 'Missing assistance_fee'}, status=400)
            
        setting = SystemSetting.objects.first()
        if not setting:
            setting = SystemSetting.objects.create()
            
        setting.assistance_fee = new_fee
        setting.save()
        
        return JsonResponse({
            'status': 'success',
            'assistance_fee': setting.assistance_fee,
            'message': f"Frais d'assistance mis à jour à {setting.assistance_fee} CFA."
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required(login_url='login')
def whatsapp_media_proxy(request, media_id):
    """
    Proxy to fetch media from WhatsApp Cloud API and serve it to the frontend.
    WhatsApp requires the Bearer token to download media.
    """
    wa_token = os.getenv('WA_ACCESS_TOKEN')
    if not wa_token:
        return HttpResponse('WhatsApp Access Token not configured', status=500)
        
    try:
        # Step 1: Get media URL
        headers = {'Authorization': f'Bearer {wa_token}'}
        resp = requests.get(f'https://graph.facebook.com/v17.0/{media_id}/', headers=headers, timeout=10)
        if resp.status_code != 200:
            logger.error(f"Failed to get media URL for {media_id}: {resp.text}")
            return HttpResponse('Media not found on WhatsApp', status=404)
            
        media_info = resp.json()
        media_url = media_info.get('url')
        mime_type = media_info.get('mime_type', 'application/octet-stream')
        
        if not media_url:
            return HttpResponse('Invalid media response', status=500)
            
        # Step 2: Download actual media
        media_resp = requests.get(media_url, headers=headers, timeout=20)
        if media_resp.status_code == 200:
            return HttpResponse(media_resp.content, content_type=mime_type)
        else:
            logger.error(f"Failed to download media {media_id} from {media_url}: {media_resp.text}")
            return HttpResponse('Failed to download media', status=media_resp.status_code)
            
    except Exception as e:
        logger.error(f"Error in whatsapp_media_proxy: {str(e)}")
        return HttpResponse('Internal Server Error', status=500)

@login_required(login_url='login')
def media_manager_view(request):
    """
    Super Admin view to manage stored media files (images, videos, etc).
    """
    if not request.user.is_superuser:
        return redirect('select_portal')
        
    # Get all messages with attachments, order by newest first
    messages_with_media = Message.objects.exclude(attachment_url__isnull=True).exclude(attachment_url='').order_by('-created_at')
    
    # Render template
    return render(request, 'chat/media_manager.html', {
        'user': request.user,
        'messages_with_media': messages_with_media,
    })

@login_required(login_url='login')
@require_POST
def delete_media_api(request):
    """
    Deletes the physical media file and removes the attachment_url from the message.
    """
    if not request.user.is_superuser:
        return JsonResponse({'status': 'error', 'message': 'Accès non autorisé'}, status=403)
        
    try:
        data = json.loads(request.body)
        msg_id = data.get('msg_id')
        if not msg_id:
            return JsonResponse({'status': 'error', 'message': 'ID du message manquant'}, status=400)
            
        msg = get_object_or_404(Message, id=msg_id)
        
        # Only proceed if there is an attachment
        if msg.attachment_url:
            # Check if it's a local file in /media/
            if msg.attachment_url.startswith('/media/') or msg.attachment_url.startswith(settings.MEDIA_URL):
                file_path = os.path.join(settings.MEDIA_ROOT, msg.attachment_url.replace('/media/', '').replace(settings.MEDIA_URL, ''))
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"Deleted physical file: {file_path}")
            
            # Remove attachment reference but keep the message text
            msg.attachment_url = None
            msg.save()
            return JsonResponse({'status': 'success', 'message': 'Média supprimé avec succès'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Aucun média attaché à ce message'}, status=404)
            
    except Exception as e:
        logger.error(f"Error deleting media: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
