from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from chat.models import User, Conversation, Message, Property, QuickTemplate

class Command(BaseCommand):
    help = 'Seeds initial data for Loger Sénégal Chat Dashboard (Properties, Templates, Agent, and Client)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='OBLIGATOIRE pour exécuter cette commande. Protège contre un lancement accidentel en production.',
        )

    def handle(self, *args, **options):
        if not options['force']:
            self.stdout.write(self.style.ERROR(
                "[ANNULÉ] Sécurité : utilisez --force pour confirmer le peuplement et la purge de la base de données."
            ))
            self.stdout.write(self.style.WARNING(
                "Exemple : python manage.py seed_data --force"
            ))
            return

        self.stdout.write(self.style.WARNING("Début du peuplement de la base de données..."))

        # 1. Clear old data
        Property.objects.all().delete()
        QuickTemplate.objects.all().delete()
        Message.objects.all().delete()
        Conversation.objects.all().delete()
        # Delete demo users to avoid conflict, keeping admin if created via createsuperuser
        User.objects.filter(username__in=['agent_demo', 'manager_demo', 'wa_221771234567', 'wa_221778901234']).delete()

        # 2. Create properties
        self.stdout.write("Création des biens immobiliers...")
        prop1 = Property.objects.create(
            title="Appartement F4 Haut Standing - Ouakam",
            price=450000.00,
            description="Superbe appartement de 4 pièces avec vue sur mer, cuisine équipée, parking sécurisé et climatisation.",
            image_url="https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=400&q=80",
            url="https://logersn.com/bien/apt-ouakam-f4"
        )
        prop2 = Property.objects.create(
            title="Studio meublé - Almadies",
            price=35000.00,
            description="Studio chic meublé avec toutes charges comprises (électricité, eau, wifi haut débit). Ménage inclus.",
            image_url="https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=400&q=80",
            url="https://logersn.com/bien/studio-almadies"
        )
        prop3 = Property.objects.create(
            title="Villa avec piscine - Saly",
            price=1200000.00,
            description="Grande villa contemporaine de 4 chambres, grand jardin avec piscine privative. Quartier calme et résidentiel.",
            image_url="https://images.unsplash.com/photo-1613977257363-707ba9348227?auto=format&fit=crop&w=400&q=80",
            url="https://logersn.com/bien/villa-saly-piscine"
        )
        prop4 = Property.objects.create(
            title="Terrain viabilisé 200m² - Diamniadio",
            price=15000000.00,
            description="Terrain plat d'angle prêt pour construction immédiate dans une zone résidentielle à fort potentiel.",
            image_url="https://images.unsplash.com/photo-1500382017468-9049fed747ef?auto=format&fit=crop&w=400&q=80",
            url="https://logersn.com/bien/terrain-diamniadio"
        )

        # 3. Create templates
        self.stdout.write("Création des modèles de messages...")
        QuickTemplate.objects.create(
            title="Accueil Client",
            content="Bonjour ! Je suis ravi de vous aider. Quel type de bien recherchez-vous aujourd'hui et dans quel quartier ?",
            category="UTILITY"
        )
        QuickTemplate.objects.create(
            title="Demande Budget",
            content="Merci pour votre intérêt ! Pour mieux cibler nos recherches, pourriez-vous m'indiquer votre budget mensuel maximum (ou budget d'achat) ?",
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

        # 4. Create default agent and manager
        self.stdout.write("Création des profils d'utilisateurs...")
        agent = User.objects.create_user(
            username='agent_demo',
            phone_number='+221700000000',
            first_name='Moussa',
            last_name='Ndiaye',
            role=User.RoleEnum.AGENT,
            is_staff=True,
            is_superuser=True
        )
        agent.set_password('agent123')
        agent.save()

        manager = User.objects.create_user(
            username='manager_demo',
            phone_number='+221711111111',
            first_name='Adama',
            last_name='Diop',
            role=User.RoleEnum.MANAGER,
            is_staff=True,
            is_superuser=True
        )
        manager.set_password('manager123')
        manager.save()

        # 5. Create default clients
        client1 = User.objects.create_user(
            username='wa_221771234567',
            phone_number='221771234567',
            first_name='Amadou Diop',
            role=User.RoleEnum.CLIENT
        )
        client2 = User.objects.create_user(
            username='wa_221778901234',
            phone_number='221778901234',
            first_name='Mariama Diallo',
            role=User.RoleEnum.CLIENT
        )

        # 6. Create conversations
        self.stdout.write("Création des fils de discussion de démo...")
        conv1 = Conversation.objects.create(
            topic="Amadou Diop - Studio meublé - Almadies",
            is_whatsapp=True,
            status=Conversation.StatusEnum.ACTIVE,
            last_message_at=timezone.now(),
            assigned_to=agent
        )
        conv1.participants.add(agent, client1)

        past_time = timezone.now() - timedelta(hours=25)
        conv2 = Conversation.objects.create(
            topic="WhatsApp de Mariama Diallo",
            is_whatsapp=True,
            status=Conversation.StatusEnum.PENDING,
            last_message_at=past_time
        )
        conv2.participants.add(agent, client2)

        # 7. Create messages
        # Conversation 1 (Amadou)
        Message.objects.create(
            conversation=conv1,
            sender=client1,
            content="Bonjour ! Est-ce que le studio meublé aux Almadies est toujours disponible ? J'aimerais avoir plus de détails.",
            msg_id="wamid.HBgLMjI4OTA5MDkwOTAVAgIGE0E1RDY2REQ0RjhDMQ==",
            status=Message.StatusEnum.READ
        )
        Message.objects.create(
            conversation=conv1,
            sender=agent,  # System simulation
            content=f"[SYSTEME] Le client a partagé le bien : {prop2.title} ({prop2.price:,.0f} FCFA)",
            status=Message.StatusEnum.READ
        )
        Message.objects.create(
            conversation=conv1,
            sender=agent,
            content="Bonjour Amadou ! Oui, le studio aux Almadies est tout à fait disponible. Il a été libéré hier.",
            msg_id="mock_wamid_sent_1",
            status=Message.StatusEnum.READ
        )
        Message.objects.create(
            conversation=conv1,
            sender=agent,
            content="Souhaitez-vous planifier une visite cet après-midi ? Un de nos agents est dans la zone.",
            msg_id="mock_wamid_sent_2",
            status=Message.StatusEnum.DELIVERED
        )

        # Conversation 2 (Mariama)
        msg2 = Message.objects.create(
            conversation=conv2,
            sender=client2,
            content="Bonjour, j'ai vu votre annonce sur TikTok pour la villa à Saly. Est-elle meublée ?",
            msg_id="wamid.HBgLMjI4OTA5MDkwOTAVAgIGE0E1RDY2REQ0RjhDMg==",
            status=Message.StatusEnum.READ
        )
        # Update auto_now_add field directly in the DB
        Message.objects.filter(id=msg2.id).update(created_at=past_time)

        self.stdout.write(self.style.SUCCESS("Base de données peuplée avec succès !"))
        self.stdout.write(self.style.SUCCESS("Agent de démo : agent_demo / agent123"))
        self.stdout.write(self.style.SUCCESS("Conversations créées : 2 (1 Active, 1 En attente)"))
