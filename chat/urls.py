from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('login/', views.custom_login_view, name='login'),
    path('logout/', views.custom_logout_view, name='logout'),
    path('api/webhook/', views.whatsapp_webhook, name='whatsapp_webhook'),
    path('api/sync/', views.sync_messages, name='sync_messages'),
    path('api/send/', views.send_message, name='send_message'),
    path('api/claim/', views.claim_conversation, name='claim_conversation'),
    path('api/conversation/tags/', views.update_conversation_tags, name='update_conversation_tags'),
    path('api/conversation/notes/', views.update_conversation_notes, name='update_conversation_notes'),
    path('api/conversation/pipeline/', views.update_conversation_pipeline, name='update_conversation_pipeline'),
    path('api/reminders/create/', views.create_reminder, name='create_reminder'),
    path('api/reminders/complete/', views.complete_reminder, name='complete_reminder'),
    path('api/leads/export/', views.export_leads_csv, name='export_leads_csv'),
]
