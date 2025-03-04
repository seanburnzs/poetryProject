# Generated by Django 5.1.1 on 2024-10-04 20:31

import django.db.models.deletion
import django.utils.timezone
import django_summernote.fields
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DailyPrompt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('prompt_text', models.TextField()),
                ('date', models.DateField(unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='News',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('content', models.TextField()),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=50, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('body', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='replies', to='poetry_app.comment')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Conversation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('participants', models.ManyToManyField(related_name='conversations', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-last_updated'],
            },
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('body', models.TextField()),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('is_read', models.BooleanField(default=False)),
                ('is_deleted', models.BooleanField(default=False)),
                ('conversation', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='poetry_app.conversation')),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sent_messages', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['timestamp'],
            },
        ),
        migrations.CreateModel(
            name='Poetry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(db_index=True, max_length=200)),
                ('body', django_summernote.fields.SummernoteTextField()),
                ('audio', models.FileField(blank=True, null=True, upload_to='poem_audio/')),
                ('anonymous', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('published', 'Publish')], default='draft', max_length=10)),
                ('allow_comments', models.BooleanField(default=True)),
                ('author', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('tags', models.ManyToManyField(blank=True, to='poetry_app.tag')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notification_type', models.CharField(choices=[('like', 'Like'), ('comment', 'Comment'), ('favorite', 'Favorite'), ('follow', 'Follow'), ('mention', 'Mention'), ('prompt', 'Prompt Reminder')], max_length=20)),
                ('is_read', models.BooleanField(default=False)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('extra_data', models.JSONField(blank=True, null=True)),
                ('actor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notifications_from', to=settings.AUTH_USER_MODEL)),
                ('comment', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='poetry_app.comment')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to=settings.AUTH_USER_MODEL)),
                ('poem', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='poetry_app.poetry')),
            ],
            options={
                'ordering': ['-timestamp'],
            },
        ),
        migrations.CreateModel(
            name='Folder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='folders', to=settings.AUTH_USER_MODEL)),
                ('poems', models.ManyToManyField(related_name='folders', to='poetry_app.poetry')),
            ],
        ),
        migrations.AddField(
            model_name='comment',
            name='poem',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='poetry_app.poetry'),
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bio', models.TextField(blank=True)),
                ('profile_picture', models.ImageField(blank=True, null=True, upload_to='profile_pictures/')),
                ('dark_mode', models.BooleanField(default=False)),
                ('hide_followers', models.BooleanField(default=False)),
                ('font_size', models.CharField(choices=[('small', 'Small'), ('medium', 'Medium'), ('large', 'Large')], default='medium', max_length=10)),
                ('favorite_poets', models.ManyToManyField(blank=True, related_name='favored_poets', to=settings.AUTH_USER_MODEL)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('favorite_tags', models.ManyToManyField(blank=True, related_name='favored_by', to='poetry_app.tag')),
            ],
        ),
        migrations.CreateModel(
            name='Following',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('follower', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='following_set', to=settings.AUTH_USER_MODEL)),
                ('following', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='followers_set', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Following',
                'verbose_name_plural': 'Followings',
                'unique_together': {('follower', 'following')},
            },
        ),
        migrations.CreateModel(
            name='Like',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('poem', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='likes', to='poetry_app.poetry')),
            ],
            options={
                'indexes': [models.Index(fields=['user', 'poem'], name='poetry_app__user_id_2701cb_idx'), models.Index(fields=['created_at'], name='poetry_app__created_1f3d3f_idx')],
                'unique_together': {('user', 'poem')},
            },
        ),
        migrations.CreateModel(
            name='FavoritePoem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('poem', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='poetry_app.poetry')),
            ],
            options={
                'indexes': [models.Index(fields=['user', 'poem'], name='poetry_app__user_id_00c1a0_idx')],
                'unique_together': {('user', 'poem')},
            },
        ),
        migrations.AddIndex(
            model_name='comment',
            index=models.Index(fields=['poem', 'user'], name='poetry_app__poem_id_314477_idx'),
        ),
        migrations.AddIndex(
            model_name='comment',
            index=models.Index(fields=['created_at'], name='poetry_app__created_fe925c_idx'),
        ),
        migrations.AddIndex(
            model_name='poetry',
            index=models.Index(fields=['title'], name='poetry_app__title_05fe12_idx'),
        ),
        migrations.AddIndex(
            model_name='poetry',
            index=models.Index(fields=['created_at'], name='poetry_app__created_5a4ce8_idx'),
        ),
    ]
