# Generated manually - No-op migration
from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0004_conversation_notes_conversation_pipeline_stage_and_more'),
    ]

    operations = [
        # No database schema changes needed (SLA is calculated in frontend)
    ]
