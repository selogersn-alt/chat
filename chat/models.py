import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    class RoleEnum(models.TextChoices):
        MANAGER = 'MANAGER', 'Manager'
        AGENT = 'AGENT', 'Agent Immobilier'
        CLIENT = 'CLIENT', 'Client'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone_number = models.CharField(max_length=30, unique=True, null=True, blank=True, db_index=True)
    role = models.CharField(max_length=20, choices=RoleEnum.choices, default=RoleEnum.CLIENT)
    
    # We allow blank email and override username field requirement if needed, 
    # but for safety in admin, we keep default abstract user requirements.
    
    def __str__(self):
        if self.first_name or self.last_name:
            return f"{self.first_name} {self.last_name} ({self.phone_number or self.username})"
        return self.phone_number or self.username

class Conversation(models.Model):
    class StatusEnum(models.TextChoices):
        PENDING = 'PENDING', 'En attente'
        ACTIVE = 'ACTIVE', 'Active'
        CLOSED = 'CLOSED', 'Fermée'

    class PipelineStageEnum(models.TextChoices):
        NEW = 'NEW', 'Nouveau'
        QUALIFIED = 'QUALIFIED', 'Qualifié'
        VISIT = 'VISIT', 'Visite Planifiée'
        NEGOTIATION = 'NEGOTIATION', 'Négociation'
        WON = 'WON', 'Gagné'
        LOST = 'LOST', 'Perdu'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    participants = models.ManyToManyField(User, related_name='conversations')
    status = models.CharField(max_length=20, choices=StatusEnum.choices, default=StatusEnum.ACTIVE)
    topic = models.CharField(max_length=150, default='Discussion Générale', blank=True)
    is_whatsapp = models.BooleanField(default=False)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_conversations', limit_choices_to={'role__in': ['AGENT', 'MANAGER']})
    tags = models.CharField(max_length=500, blank=True, default='')
    notes = models.TextField(blank=True, default='')
    pipeline_stage = models.CharField(max_length=20, choices=PipelineStageEnum.choices, default=PipelineStageEnum.NEW)
    sla_limit_minutes = models.IntegerField(default=15)
    sla_started_at = models.DateTimeField(null=True, blank=True)
    sla_enabled = models.BooleanField(default=True)
    
    survey_sent = models.BooleanField(default=False)
    satisfaction_rating = models.IntegerField(null=True, blank=True)
    satisfaction_comment = models.TextField(blank=True, null=True)
    
    # Interactive flow fields
    client_project = models.CharField(max_length=50, blank=True, null=True)
    client_property_type = models.CharField(max_length=50, blank=True, null=True)
    client_zone = models.CharField(max_length=150, blank=True, null=True)
    
    last_message_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-last_message_at', '-updated_at']

    def __str__(self):
        return f"Conversation {str(self.id)[:8]} - {self.topic}"

class Message(models.Model):
    class StatusEnum(models.TextChoices):
        SENT = 'SENT', 'Envoyé'
        DELIVERED = 'DELIVERED', 'Délivré'
        READ = 'READ', 'Lu'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    attachment_url = models.URLField(max_length=500, null=True, blank=True)
    
    # Meta WhatsApp specifics
    msg_id = models.CharField(max_length=200, null=True, blank=True, db_index=True)
    status = models.CharField(max_length=20, choices=StatusEnum.choices, default=StatusEnum.SENT)
    
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        sender_name = self.sender.first_name or self.sender.username
        return f"Message from {sender_name} at {self.created_at.strftime('%Y-%m-%d %H:%M')}"

class Property(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField()
    image_url = models.URLField(max_length=500, null=True, blank=True)
    url = models.URLField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Properties"

    def __str__(self):
        return self.title

class QuickTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=100)
    content = models.TextField()
    category = models.CharField(max_length=50, default='UTILITY')

    def __str__(self):
        return self.title

class Reminder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='reminders')
    agent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reminders')
    title = models.CharField(max_length=255)
    remind_at = models.DateTimeField()
    is_done = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rappel: {self.title} pour {self.conversation.topic}"

class Partner(models.Model):
    class MeteoEnum(models.TextChoices):
        ENSOLEILLE = 'ENSOLEILLE', '☀️ Ensoleillée (Très réactif)'
        NUAGEUX = 'NUAGEUX', '☁️ Nuageux (Réactif)'
        ORAGEUX = 'ORAGEUX', '⛈️ Orageux (Peu réactif / Problèmes)'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    ref = models.CharField(max_length=50, blank=True, null=True)
    contact_1 = models.CharField(max_length=30)
    contact_2 = models.CharField(max_length=30, blank=True, null=True)
    zone = models.CharField(max_length=150)
    property_type = models.CharField(max_length=50, default='VIDE') # VIDE ou MEUBLE
    meteo = models.CharField(max_length=20, choices=MeteoEnum.choices, default=MeteoEnum.NUAGEUX)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.zone})"

class PartnerMatch(models.Model):
    class StatusEnum(models.TextChoices):
        PENDING = 'PENDING', 'En attente'
        VISITED = 'VISITED', 'Visité'
        WON = 'WON', 'Gagné'
        LOST = 'LOST', 'Perdu'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='partner_matches')
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name='matches')
    visitor_name = models.CharField(max_length=255)
    visitor_phone = models.CharField(max_length=30)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    zone = models.CharField(max_length=150)
    status = models.CharField(max_length=20, choices=StatusEnum.choices, default=StatusEnum.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Match: {self.visitor_name} ➔ {self.partner.name}"

class Visit(models.Model):
    class StatusEnum(models.TextChoices):
        PLANNED = 'PLANNED', 'Planifiée'
        COMPLETED = 'COMPLETED', 'Effectuée'
        CANCELED = 'CANCELED', 'Annulée'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='visits')
    agent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='visits_assigned')
    property_title = models.CharField(max_length=255)
    visit_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=StatusEnum.choices, default=StatusEnum.PLANNED)
    client_name = models.CharField(max_length=255, blank=True)
    client_phone = models.CharField(max_length=30, blank=True)
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['visit_date']

    def __str__(self):
        return f"Visite: {self.client_name} - {self.property_title} le {self.visit_date.strftime('%d/%m/%Y')}"

class District(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Quartier/Zone")
    
    class Meta:
        ordering = ['name']
        verbose_name = "Quartier"
        verbose_name_plural = "Quartiers"

    def __str__(self):
        return self.name

class PropertyType(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Type de bien")
    
    class Meta:
        ordering = ['name']
        verbose_name = "Type de bien"
        verbose_name_plural = "Types de bien"

    def __str__(self):
        return self.name
