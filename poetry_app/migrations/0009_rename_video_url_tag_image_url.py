# Generated by Django 5.1.1 on 2024-10-11 03:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('poetry_app', '0008_tag_video_url'),
    ]

    operations = [
        migrations.RenameField(
            model_name='tag',
            old_name='video_url',
            new_name='image_url',
        ),
    ]
