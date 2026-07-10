# Generated manually
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0007_conversation_sla_started_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(
                choices=[('MANAGER', 'Manager'), ('AGENT', 'Agent Immobilier'), ('CLIENT', 'Client')],
                default='CLIENT',
                max_length=20
            ),
        ),
    ]
