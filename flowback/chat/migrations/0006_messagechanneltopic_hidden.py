# Generated by Django 4.2.7 on 2024-01-26 14:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0005_messagechanneltopic_message_topic'),
    ]

    operations = [
        migrations.AddField(
            model_name='messagechanneltopic',
            name='hidden',
            field=models.BooleanField(default=False),
        ),
    ]
