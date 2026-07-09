# Generated manually
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0004_conversation_notes_conversation_pipeline_stage_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='conversation',
            name='sla_limit_minutes',
            field=models.IntegerField(default=15),
        ),
    ]
