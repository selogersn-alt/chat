from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Conversation, Message, Property, QuickTemplate, Reminder, Partner, PartnerMatch, District, PropertyType, Visit

# Restriction d'accès à l'administration (/admin/) uniquement aux super-utilisateurs (super-admins)
admin.site.has_permission = lambda request: request.user.is_active and request.user.is_superuser


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'phone_number', 'role', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('Informations Métier', {'fields': ('phone_number', 'role')}),
    )

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'topic', 'status', 'is_whatsapp', 'last_message_at', 'pipeline_stage')
    list_filter = ('status', 'is_whatsapp', 'pipeline_stage')

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'sender', 'created_at')
    list_filter = ('created_at',)

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'created_at')

@admin.register(QuickTemplate)
class QuickTemplateAdmin(admin.ModelAdmin):
    list_display = ('title', 'category')

@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ('title', 'conversation', 'remind_at', 'is_done')
    list_filter = ('is_done', 'remind_at')

@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ('name', 'ref', 'contact_1', 'zone', 'property_type', 'meteo')
    list_filter = ('zone', 'property_type', 'meteo')
    search_fields = ('name', 'ref', 'zone')

@admin.register(PartnerMatch)
class PartnerMatchAdmin(admin.ModelAdmin):
    list_display = ('visitor_name', 'visitor_phone', 'partner', 'zone', 'price', 'status', 'created_at')
    list_filter = ('status', 'zone')
    search_fields = ('visitor_name', 'visitor_phone', 'partner__name')

@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(PropertyType)
class PropertyTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):
    list_display = ('client_name', 'client_phone', 'property_title', 'visit_date', 'agent', 'status', 'created_at')
    list_filter = ('status', 'visit_date', 'agent')
    search_fields = ('client_name', 'client_phone', 'property_title')
