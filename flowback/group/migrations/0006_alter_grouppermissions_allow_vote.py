# Generated by Django 4.0.8 on 2022-11-16 17:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('group', '0005_group_hide_poll_users'),
    ]

    operations = [
        migrations.AlterField(
            model_name='grouppermissions',
            name='allow_vote',
            field=models.BooleanField(default=True),
        ),
    ]