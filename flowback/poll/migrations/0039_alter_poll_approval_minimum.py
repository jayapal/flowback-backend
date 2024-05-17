# Generated by Django 4.2.7 on 2024-05-17 15:41

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('poll', '0038_poll_approval_minimum_poll_finalization_period'),
    ]

    operations = [
        migrations.AlterField(
            model_name='poll',
            name='approval_minimum',
            field=models.PositiveIntegerField(blank=True, default=None, null=True, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(100)]),
        ),
    ]