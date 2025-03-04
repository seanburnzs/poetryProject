# Generated by Django 5.1.1 on 2025-02-08 08:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('poetry_app', '0013_create_superuser'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='profile_picture',
            field=models.ImageField(blank=True, null=True, upload_to=''),
        ),
    ]
