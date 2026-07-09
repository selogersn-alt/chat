# Generated manually
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0006_conversation_sla_limit_minutes'),
    ]

    operations = [
        migrations.AddField(
            model_name='conversation',
            name='sla_started_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
