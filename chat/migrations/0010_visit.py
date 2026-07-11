# Generated manually

import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0009_partner_partnermatch'),
    ]

    operations = [
        migrations.CreateModel(
            name='Visit',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('property_title', models.CharField(max_length=255)),
                ('visit_date', models.DateTimeField()),
                ('status', models.CharField(choices=[('PLANNED', 'Planifiée'), ('COMPLETED', 'Effectuée'), ('CANCELED', 'Annulée')], default='PLANNED', max_length=20)),
                ('client_name', models.CharField(blank=True, max_length=255)),
                ('client_phone', models.CharField(blank=True, max_length=30)),
                ('notes', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('agent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='visits_assigned', to=settings.AUTH_USER_MODEL)),
                ('conversation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='visits', to='chat.conversation')),
            ],
            options={
                'ordering': ['visit_date'],
            },
        ),
    ]
