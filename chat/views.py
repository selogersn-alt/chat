import os
import re
import json
import logging
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from datetime import timedelta
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Q
from django.core.cache import cache
from .models import User, Conversation, Message, Property, QuickTemplate, Reminder

logger = logging.getLogger(__name__)

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

def custom_login_view(request):
    """Simple login view for agents."""
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
    else:
        form = AuthenticationForm()
        

    return render(request, 'chat/login.html', {'form': form})

def custom_logout_view(request):
    """Logout view."""
    logout(request)
    return redirect('login')

@login_required(login_url='login')
def dashboard_view(request):
    """Main Agent Chat Dashboard."""
    # Ensure there is at least one agent (the logged in user should be an AGENT)
    if request.user.role != User.RoleEnum.AGENT:
        request.user.role = User.RoleEnum.AGENT
        request.user.save()
        
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
        'user': request.user
    })

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
                attachment_url = media_id if media_id and (media_id.startswith('http://') or media_id.startswith('https://')) else f"https://graph.facebook.com/v19.0/{media_id}"
            elif message_type == 'document':
                media_id = message_data.get('document', {}).get('id')
                content = message_data.get('document', {}).get('filename', '[Document WhatsApp]')
                attachment_url = media_id if media_id and (media_id.startswith('http://') or media_id.startswith('https://')) else f"https://graph.facebook.com/v19.0/{media_id}"
            elif message_type == 'audio':
                media_id = message_data.get('audio', {}).get('id')
                content = "[Note Vocale WhatsApp]"
                attachment_url = media_id if media_id and (media_id.startswith('http://') or media_id.startswith('https://')) else f"https://graph.facebook.com/v19.0/{media_id}"
            elif message_type == 'video':
                media_id = message_data.get('video', {}).get('id')
                content = message_data.get('video', {}).get('caption', '[Vidéo WhatsApp]')
                attachment_url = media_id if media_id and (media_id.startswith('http://') or media_id.startswith('https://')) else f"https://graph.facebook.com/v19.0/{media_id}"
            elif message_type == 'location':
                loc = message_data.get('location', {})
                content = f"Localisation : Lat {loc.get('latitude')}, Lng {loc.get('longitude')}"
            else:
                content = f"[{message_type.capitalize()} Message]"

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
            ).filter(~Q(status=Conversation.StatusEnum.CLOSED)).first()
            
            if not conversation:
                conversation = Conversation.objects.create(
                    topic=f"WhatsApp de {sender_name}",
                    is_whatsapp=True,
                    status=Conversation.StatusEnum.ACTIVE
                )
                conversation.participants.add(client_user)
                agents = User.objects.filter(role=User.RoleEnum.AGENT)
                conversation.participants.add(*agents)
                
                # --- BOT D'ACCUEIL WHATSAPP ---
                welcome_text = (
                    "Bienvenue chez Loger Sénégal ! 🏡\n\n"
                    "Pour que notre équipe vous propose les meilleures options, pouvez-vous nous préciser :\n\n"
                    "1️⃣ *Quel type de bien cherchez-vous ?*\n"
                    "(Appartement, Villa, Studio, Terrain, Bureau...)\n\n"
                    "2️⃣ *Dans quel quartier ou ville ?*\n"
                    "(Dakar Plateau, Almadies, Ngor, Ouakam, Saly, Thies... ou autre)\n\n"
                    "3️⃣ *Quel est votre budget approximatif ?*\n\n"
                    "Un de nos agents va prendre en charge votre demande dans quelques instants !"
                )
                
                # Send welcome message
                success, msg_id = trigger_meta_whatsapp_api(sender_phone, welcome_text)
                
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
                conversation.last_message_at = timezone.now()
                conversation.save()

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

            # 4. Save the actual message (with msg_id and READ status since it is incoming)
            Message.objects.create(
                conversation=conversation,
                sender=client_user,
                content=content,
                attachment_url=attachment_url,
                msg_id=message_data.get('id'),
                status=Message.StatusEnum.READ
            )
            
            # 5. Update last message time
            conversation.last_message_at = timezone.now()
            conversation.save()
            
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
    
    # Get all conversations the agent has access to
    conversations = agent.conversations.all().order_by('-last_message_at', '-updated_at')
    
    conv_data = []
    for conv in conversations:
        # Find client in participants
        client = conv.participants.filter(role=User.RoleEnum.CLIENT).first()
        client_name = client.first_name if client else "Client Inconnu"
        client_phone = client.phone_number if client else "N/A"
        
        last_msg = conv.messages.all().order_by('-created_at').first()
        last_msg_content = last_msg.content if last_msg else "Aucun message"
        last_msg_time = last_msg.created_at.strftime("%H:%M") if last_msg else ""
        
        # Last message sent by the CLIENT (for activity indicator)
        last_client_msg = conv.messages.filter(sender__role=User.RoleEnum.CLIENT).order_by('-created_at').first()
        last_client_msg_at = last_client_msg.created_at.isoformat() if last_client_msg else None
        
        assigned_to_name = conv.assigned_to.get_full_name() or conv.assigned_to.username if conv.assigned_to else None
        
        # Check if last message is from client for SLA tracking
        is_last_msg_from_client = (last_msg.sender.role == User.RoleEnum.CLIENT) if last_msg else False
        
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
        })
        
    messages_data = []
    active_conv_info = None
    suggested_properties_data = []
    active_reminders_data = []
    
    if active_conv_id:
        try:
            active_conv = Conversation.objects.get(id=active_conv_id, participants=agent)
            
            # Fetch active client
            client = active_conv.participants.filter(role=User.RoleEnum.CLIENT).first()
            
            # Locate last message sent by client
            last_client_msg = active_conv.messages.filter(sender__role=User.RoleEnum.CLIENT).order_by('-created_at').first()
            client_last_message_at = last_client_msg.created_at.isoformat() if last_client_msg else active_conv.created_at.isoformat()
            
            active_last_msg = active_conv.messages.all().order_by('-created_at').first()
            active_is_last_msg_from_client = (active_last_msg.sender.role == User.RoleEnum.CLIENT) if active_last_msg else False
            
            active_conv_info = {
                'id': str(active_conv.id),
                'topic': active_conv.topic,
                'client_name': client.first_name if client else "Client",
                'client_phone': client.phone_number if client else "N/A",
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
            }
            
            # Fetch messages
            msgs = active_conv.messages.all().order_by('created_at')
            for msg in msgs:
                messages_data.append({
                    'id': str(msg.id),
                    'sender_name': msg.sender.first_name or msg.sender.username,
                    'sender_role': msg.sender.role,
                    'sender_is_self': msg.sender == agent,
                    'content': msg.content,
                    'attachment_url': msg.attachment_url,
                    'status': msg.status,
                    'created_at': msg.created_at.strftime("%H:%M")
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
        'agent_reminders': agent_reminders_data
    })

@login_required(login_url='login')
@csrf_exempt
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
        content = data.get('content')
        
        if not conversation_id or not content:
            return JsonResponse({'error': 'Missing conversation_id or content'}, status=400)
            
        conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
        
        # Save the message in our DB
        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=content
        )
        
        conversation.last_message_at = timezone.now()
        conversation.save()
        
        # If it is a WhatsApp conversation, invoke Meta Cloud API
        if conversation.is_whatsapp:
            client = conversation.participants.filter(role=User.RoleEnum.CLIENT).first()
            if client and client.phone_number:
                # Trigger the webhook request to Meta
                success, msg_id = trigger_meta_whatsapp_api(client.phone_number, content)
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
                'created_at': message.created_at.strftime("%H:%M")
            }
        })
        
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)

def trigger_meta_whatsapp_api(to_phone, message_text):
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
        logger.info(f"MOCK API WhatsApp ➔ To: {to_phone} | Msg: {message_text} | ID: {mock_id}")
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
        "type": "text",
        "text": {
            "preview_url": True,
            "body": message_text
        }
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
@csrf_exempt
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
            
        conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
        
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

import csv
from django.utils.dateparse import parse_datetime

@login_required(login_url='login')
@csrf_exempt
def update_conversation_notes(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    try:
        data = json.loads(request.body)
        conversation_id = data.get('conversation_id')
        notes = data.get('notes', '')
        conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
        conversation.notes = notes
        conversation.save()
        return JsonResponse({'status': 'updated'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required(login_url='login')
@csrf_exempt
def update_conversation_pipeline(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    try:
        data = json.loads(request.body)
        conversation_id = data.get('conversation_id')
        stage = data.get('pipeline_stage')
        if not stage:
            return JsonResponse({'error': 'Missing pipeline_stage'}, status=400)
        
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
@csrf_exempt
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
@csrf_exempt
def complete_reminder(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    try:
        data = json.loads(request.body)
        reminder_id = data.get('reminder_id')
        if not reminder_id:
            return JsonResponse({'error': 'Missing reminder_id'}, status=400)
            
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
    
    conversations = Conversation.objects.filter(participants=request.user)
    
    if status_filter:
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
        'Nom du Prospect', 
        'Téléphone', 
        'Status', 
        'Canal', 
        'Agent Assigné', 
        'Étape du Pipeline', 
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
        
        writer.writerow([
            client_name,
            client_phone,
            conv.status,
            'WhatsApp' if conv.is_whatsapp else 'Web Chat',
            conv.assigned_to.get_full_name() or conv.assigned_to.username if conv.assigned_to else 'Non assigné',
            conv.get_pipeline_stage_display(),
            conv.tags,
            conv.notes,
            last_msg_content
        ])
        
    return response

@csrf_exempt
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
            
        conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
        conversation.sla_limit_minutes = int(limit)
        conversation.save()
        
        return JsonResponse({'status': 'updated', 'sla_limit_minutes': conversation.sla_limit_minutes})
    except Exception as e:
        logger.error(f"Error updating SLA limit: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)
