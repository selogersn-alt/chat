# Generated manually

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0011_conversation_client_project_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='conversation',
            name='sla_enabled',
            field=models.BooleanField(default=True),
        ),
    ]
