# Generated by Django 5.1.1 on 2024-10-11 02:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('poetry_app', '0007_tag_category_alter_badge_name_alter_poetry_author_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='tag',
            name='video_url',
            field=models.URLField(blank=True, null=True),
        ),
    ]
