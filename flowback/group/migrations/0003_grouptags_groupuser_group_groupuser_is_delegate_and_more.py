# Generated by Django 4.0.3 on 2022-08-10 14:18

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('group', '0002_alter_group_image'),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupTags',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('tag_name', models.TextField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='groupuser',
            name='group',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='group.group'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='groupuser',
            name='is_delegate',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='groupuserinvite',
            name='group',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='group.group'),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='groupuser',
            unique_together={('user', 'group')},
        ),
        migrations.CreateModel(
            name='GroupUserDelegate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('delegate', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='group_user_delegate_delegate', to='group.groupuser')),
                ('delegator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='group_user_delegate_delegator', to='group.groupuser')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='group.group')),
                ('tag', models.ManyToManyField(to='group.grouptags')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='group',
            name='tags',
            field=models.ManyToManyField(to='group.grouptags'),
        ),
    ]