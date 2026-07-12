from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('login/', views.custom_login_view, name='login'),
    path('logout/', views.custom_logout_view, name='logout'),
    path('select-portal/', views.select_portal_view, name='select_portal'),
    path('manager/', views.manager_dashboard_view, name='manager_dashboard'),
    
    path('api/webhook/', views.whatsapp_webhook, name='whatsapp_webhook'),
    path('api/media/<str:media_id>/', views.whatsapp_media_proxy, name='whatsapp_media_proxy'),
    path('api/upload/', views.upload_media, name='upload_media'),
    path('api/sync/', views.sync_messages, name='sync_messages'),
    path('api/send/', views.send_message, name='send_message'),
    path('api/claim/', views.claim_conversation, name='claim_conversation'),
    path('api/conversation/close/', views.close_conversation, name='close_conversation'),
    path('api/conversation/tags/', views.update_conversation_tags, name='update_conversation_tags'),
    path('api/conversation/notes/', views.update_conversation_notes, name='update_conversation_notes'),
    path('api/conversation/pipeline/', views.update_conversation_pipeline, name='update_conversation_pipeline'),
    path('api/conversation/sla-limit/', views.update_conversation_sla_limit, name='update_conversation_sla_limit'),
    path('api/reminders/create/', views.create_reminder, name='create_reminder'),
    path('api/reminders/complete/', views.complete_reminder, name='complete_reminder'),
    path('api/leads/export/', views.export_leads_csv, name='export_leads_csv'),
    path('api/conversation/send-survey/', views.send_survey, name='send_survey'),
    
    # Visits APIs
    path('api/visits/create/', views.create_visit, name='create_visit'),
    path('api/visits/update/', views.update_visit, name='update_visit'),
    path('api/visits/list/', views.list_visits, name='list_visits'),
    
    # Manager APIs
    path('api/manager/stats/', views.manager_stats, name='manager_stats'),
    path('api/manager/agents/', views.manager_agents, name='manager_agents'),
    path('api/manager/delegate/', views.manager_delegate, name='manager_delegate'),
    path('api/manager/templates/', views.manager_templates_api, name='manager_templates_api'),
    path('api/manager/matches/', views.manager_matches, name='manager_matches'),
    
    # Mobile App APIs
    path('api/mobile/login/', views.mobile_login, name='mobile_login'),
    path('api/mobile/conversations/', views.mobile_conversations, name='mobile_conversations'),
    path('api/mobile/conversations/<uuid:conversation_id>/messages/', views.mobile_messages, name='mobile_messages'),
    path('api/mobile/conversations/update/', views.mobile_update_conversation, name='mobile_update_conversation'),
    path('api/mobile/properties/', views.mobile_properties, name='mobile_properties'),
    path('api/mobile/partners/', views.mobile_partners, name='mobile_partners'),
    path('api/mobile/partners/match/', views.mobile_create_partner_match, name='mobile_create_partner_match'),
    
    # Partner APIs
    path('api/partners/search/', views.search_partners, name='search_partners'),
    path('api/partners/match/', views.create_partner_match, name='create_partner_match'),
]
