# Generated by Django 4.2.7 on 2024-03-04 15:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kanban', '0004_kanbanentry_priority'),
    ]

    operations = [
        migrations.AlterField(
            model_name='kanbanentry',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
    ]
