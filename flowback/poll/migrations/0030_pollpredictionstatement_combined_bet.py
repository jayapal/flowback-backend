# Generated by Django 4.2.7 on 2024-03-13 16:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('poll', '0029_alter_poll_description'),
    ]

    operations = [
        migrations.AddField(
            model_name='pollpredictionstatement',
            name='combined_bet',
            field=models.DecimalField(blank=True, decimal_places=7, max_digits=8, null=True),
        ),
    ]
