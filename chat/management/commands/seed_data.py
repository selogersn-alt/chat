from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from chat.models import User, Conversation, Message, Property, QuickTemplate, Partner, PartnerMatch

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
        Partner.objects.all().delete()
        PartnerMatch.objects.all().delete()
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
            is_staff=False,
            is_superuser=False
        )
        agent.set_password('agent123')
        agent.save()

        manager = User.objects.create_user(
            username='manager_demo',
            phone_number='+221711111111',
            first_name='Adama',
            last_name='Diop',
            role=User.RoleEnum.MANAGER,
            is_staff=False,
            is_superuser=False
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

        # 8. Create partners
        self.stdout.write("Création des partenaires (54)...")
        partners_list = [
            ("PRESTA IMMO", "PREST", "772380835", "705657870", "PLATEAU", "MEUBLE", "NUAGEUX"),
            ("NOUROULAHI", "NRI", "778374545", None, "FOIRE LIB SC", "VIDE", "ENSOLEILLE"),
            ("WOURA BUILDING", "WRA", "764372365", None, "DAKAR", "VIDE", "ENSOLEILLE"),
            ("GUEYE IMMO", "ADR", "775478818", None, "FOIRE LIB SC", "VIDE", "ENSOLEILLE"),
            ("LUXURA", "LUX", "772286467", None, "FASS MEDINA", "VIDE", "ENSOLEILLE"),
            ("KING IMMO", "KNG", "778339425", None, "OUAKAM MAMELLES", "VIDES", "NUAGEUX"),
            ("SEYLON IMMO", "SLY", "775149985", None, "OUAKAM", "VIDE", "NUAGEUX"),
            ("TERANGA IMMO", "HFL", "776898987", None, "ZONE DE CAPTAGE", "VIDE", "NUAGEUX"),
            ("SANE IMMO", "SNE", "771996326", None, "SACRE CŒUR", "VIDE", "NUAGEUX"),
            ("MOUHAMED IMMO", "ADF", "776966605", None, "NORD FOIRE", "VIDE", "ENSOLEILLE"),
            ("BARRY IMMO", "MMB", "779024571", None, "SACRE CŒUR", "VIDE", "ENSOLEILLE"),
            ("YEUF IMMO", "YEUF", "774577031", None, "DAKAR", "VIDE", "ORAGEUX"),
            ("GILBERT", "GILB", "774454442", None, "SACRE CŒUR", "VIDE", "ENSOLEILLE"),
            ("MOHAMED COURTIER", "MHD", "772727478", None, "OUAKAM", "VIDE", "ENSOLEILLE"),
            ("AMADOU OUSSAS", "AMD", "776941371", None, "OUAKAM MONUMENT", "VIDE", "ENSOLEILLE"),
            ("ADAMA", "ADM", "778893740", None, "MAMELLES", "VIDE", "ENSOLEILLE"),
            ("NOUROU", "NOK", "764747161", None, "MBAO", "VIDE", "NUAGEUX"),
            ("DARROU SALAM", "DROU", "789742269", None, "OUEST FOIRE", "VIDE", "NUAGEUX"),
            ("BLOIM HUB", "BLO", "784396060", None, "OUAKAM", "VIDE", "NUAGEUX"),
            ("HASSAN SOLUTION", "HAS", "761957082", None, "DAKAR", "VIDE", "ORAGEUX"),
            ("JAMM IMMO", "JAMM", "761660377", None, "SACRE CŒUR", "VIDE", "NUAGEUX"),
            ("AMB IMMO", "ABM", "778314975", None, "MERMOZ", "VIDE", "NUAGEUX"),
            ("AMB IMMO (2)", "ABM", "773693368", None, "MERMOZ", "VIDE", "ORAGEUX"),
            ("BEU IMMO", "BEU", "784581818", None, "DAKAR", "MEUBLE", "NUAGEUX"),
            ("SASSOUMAN", "SSM", "774637679", None, "DAKAR", "VIDE", "NUAGEUX"),
            ("CABINET OMEGA", "CAB", "774061261", None, "MERMOZ", "VIDE", "ORAGEUX"),
            ("ALASSANE", "ALN", "771727438", None, "DAKAR", "VIDE", "NUAGEUX"),
            ("MBALLO IMMO", "MBA", "708525372", None, "MAMELELS", "VIDE", "NUAGEUX"),
            ("SEN IMMO", "IFN", "785532017", None, "MARISTES", "VIDE", "ORAGEUX"),
            ("YVAN IMMO", "BANNI", "784814614", None, "OUAKAM", "VIDE", "NUAGEUX"),
            ("MAODO IMMO", "MAO", "783879676", None, "OUAKAM", "VIDE", "NUAGEUX"),
            ("TAWFIK IMMO", "TAW", "772739362", None, "SALY", "MEUBLE", "ORAGEUX"),
            ("OUM SARA", "OUM", "776629544", None, "MAMELLES", "VIDE", "NUAGEUX"),
            ("DJIBRIL IMMO", "DJI", "765999588", None, "SACRE CŒUR", "VIDE", "NUAGEUX"),
            ("ADJI IMMO", "ADJ", "774848342", None, "SALY", "VENTE", "ORAGEUX"),
            ("MMS SERVICE", "MMS", "774723333", None, "DAKAR", "VIDE", "NUAGEUX"),
            ("BOBO DIALLO", "BOBO", "705322000", None, "MBAO", "VIDE", "NUAGEUX"),
            ("ABOUBACRY", "HAN", "779441330", None, "KEUR MASSAR", "VIDE", "ORAGEUX"),
            ("NGM IMMO", "NGM", "757476776", None, "ALMADIES 2", "VENTE", "NUAGEUX"),
            ("NDELLA IMMO", "NDEL", "775002757", None, "DAKAR", "VIDE", "NUAGEUX"),
            ("MADJI IMMO", "MADJ", "704826376", None, "MAMELLES", "VIDE", "ORAGEUX"),
            ("JULES LONDON", "JULES", "784378837", None, "KEUR MASSAR", "VIDE", "NUAGEUX"),
            ("PHILLIPE", "PHIL", "775920361", None, "MERMOZ", "VIDE", "NUAGEUX"),
            ("YOUSRA", "YSH", "762555274", None, "OUAKAM", "VIDE", "ORAGEUX"),
            ("MR DIAKHATE", "DKH", "784980959", None, "NGOR", "VIDE", "NUAGEUX"),
            ("Barry", "bar", "761343074", None, "DAKAR", "VIDE", "NUAGEUX"),
            ("ABOU IMMO", "ABI", "783969472", None, "Rufisque", "VIDE", "NUAGEUX"),
            ("AZIZ IMMO", "AZZ", "772327868", None, "LIBERTE", "VIDE", "NUAGEUX"),
            ("AXEL", "AXE", "781379788", None, "OUAKAM", "VIDE", "NUAGEUX"),
            ("TOUBA KHELCOM", "MSA", "765406039", "784905306", "ZONE DE CAPTAGE", "VIDE", "NUAGEUX"),
            ("NDIOGOU NDIAYE", "NDA", "775500847", None, "LIBERTE 6", "VIDE", "ENSOLEILLE"),
            ("GAYE", "GAY", "775173845", None, "YOFF", "VIDE", "NUAGEUX"),
            ("TINE", "TIN", "776358282", None, "LIBERTE 6", "VIDE", "NUAGEUX"),
            ("aboulabas immo // Cheikh tidiane", "TID", "778628019", None, "HLM 5", "VIDE", "NUAGEUX")
        ]

        for name, ref, c1, c2, zone_val, p_type, meteo_val in partners_list:
            Partner.objects.create(
                name=name,
                ref=ref,
                contact_1=c1,
                contact_2=c2,
                zone=zone_val,
                property_type=p_type,
                meteo=meteo_val
            )

        self.stdout.write(self.style.SUCCESS("Base de données peuplée avec succès !"))
        self.stdout.write(self.style.SUCCESS("Agent de démo : agent_demo / agent123"))
        self.stdout.write(self.style.SUCCESS("Conversations créées : 2 (1 Active, 1 En attente)"))
