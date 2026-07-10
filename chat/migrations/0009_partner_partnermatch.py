# Generated manually
from django.db import migrations, models
import django.db.models.deletion
import uuid

class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0008_alter_user_role'),
    ]

    operations = [
        migrations.CreateModel(
            name='Partner',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('ref', models.CharField(blank=True, max_length=50, null=True)),
                ('contact_1', models.CharField(max_length=30)),
                ('contact_2', models.CharField(blank=True, max_length=30, null=True)),
                ('zone', models.CharField(max_length=150)),
                ('property_type', models.CharField(default='VIDE', max_length=50)),
                ('meteo', models.CharField(choices=[('ENSOLEILLE', '☀️ Ensoleillée (Très réactif)'), ('NUAGEUX', '☁️ Nuageux (Réactif)'), ('ORAGEUX', '⛈️ Orageux (Peu réactif / Problèmes)')], default='NUAGEUX', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='PartnerMatch',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('visitor_name', models.CharField(max_length=255)),
                ('visitor_phone', models.CharField(max_length=30)),
                ('price', models.DecimalField(decimal_places=2, max_digits=12)),
                ('zone', models.CharField(max_length=150)),
                ('status', models.CharField(choices=[('PENDING', 'En attente'), ('VISITED', 'Visité'), ('WON', 'Gagné'), ('LOST', 'Perdu')], default='PENDING', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('conversation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='partner_matches', to='chat.conversation')),
                ('partner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='matches', to='chat.partner')),
            ],
        ),
    ]
