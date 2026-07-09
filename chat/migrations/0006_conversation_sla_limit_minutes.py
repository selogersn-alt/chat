# Generated manually
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0005_conversation_sla_auto_reply_sent'),
    ]

    operations = [
        migrations.AddField(
            model_name='conversation',
            name='sla_limit_minutes',
            field=models.IntegerField(default=15),
        ),
    ]
