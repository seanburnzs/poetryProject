# Generated by Django 5.1.1 on 2024-10-11 06:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('poetry_app', '0009_rename_video_url_tag_image_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='tag',
            name='photographer',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
