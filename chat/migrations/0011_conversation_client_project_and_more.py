# Generated manually

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0010_visit'),
    ]

    operations = [
        migrations.AddField(
            model_name='conversation',
            name='client_project',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='conversation',
            name='client_property_type',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='conversation',
            name='client_zone',
            field=models.CharField(blank=True, max_length=150, null=True),
        ),
        migrations.AddField(
            model_name='conversation',
            name='satisfaction_rating',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='conversation',
            name='survey_sent',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='conversation',
            name='assigned_to',
            field=models.ForeignKey(blank=True, limit_choices_to={'role__in': ['AGENT', 'MANAGER']}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_conversations', to=settings.AUTH_USER_MODEL),
        ),
    ]
