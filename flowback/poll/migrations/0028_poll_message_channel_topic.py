# Generated by Django 4.2.7 on 2024-01-26 13:44

from django.db import migrations, models
import django.db.models.deletion


def create_topic_for_each_poll(apps, schema_editor):
    Poll = apps.get_model("poll", "Poll")
    MessageChannelTopic = apps.get_model("chat", "MessageChannelTopic")

    for poll in Poll.objects.all():
        topic = MessageChannelTopic.objects.create(channel=poll.created_by.group.chat,
                                                   name=f'poll.{poll.id}',
                                                   hidden=True)
        poll.message_channel_topic = topic
        poll.save()


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0005_messagechanneltopic_message_topic'),
        ('poll', '0027_merge_20240116_1418'),
    ]

    operations = [
        migrations.AddField(
            model_name='poll',
            name='message_channel_topic',
            field=models.ForeignKey(null=True, blank=True, on_delete=django.db.models.deletion.PROTECT,
                                    to='chat.messagechanneltopic')
        ),
        migrations.RunPython(create_topic_for_each_poll),
    ]
