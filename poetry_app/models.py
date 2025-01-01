from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_summernote.fields import SummernoteTextField
from django.utils import timezone
from django.conf import settings
import requests, logging

logger = logging.getLogger(__name__)

class Tag(models.Model):
    CATEGORY_CHOICES = [
        ('Content Type', 'Content Type'),
        ('Topic', 'Topic'),
    ]
    name = models.CharField(max_length=50, unique=True, db_index=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Topic')
    image_url = models.URLField(blank=True, null=True)  # For Pexels image URL
    photographer = models.CharField(max_length=255, blank=True, null=True)  # Photographer's name

    def __str__(self):
        return self.name

    def fetch_image(self):
        """
        Fetches a relevant landscape-oriented image from Pexels based on the tag's name and
        sets the image_url and photographer.
        """
        if not self.image_url:
            query = self.name
            api_key = settings.PEXELS_API_KEY
            headers = {
                'Authorization': api_key,
            }
            search_url = f'https://api.pexels.com/v1/search?query={query}&per_page=1&orientation=landscape'
            try:
                response = requests.get(search_url, headers=headers)
                response.raise_for_status()
                data = response.json()
                if data['photos']:
                    photo = data['photos'][0]
                    image_url = photo['src']['medium']  # Choose 'medium' size for consistency
                    photographer = photo['photographer']
                    self.image_url = image_url
                    self.photographer = photographer
                    self.save(update_fields=['image_url', 'photographer'])
                    logger.info(f"Image set for tag '{self.name}': {self.image_url} by {self.photographer}")
                else:
                    logger.warning(f"No photos found for tag '{self.name}'.")
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching image for tag '{self.name}': {e}")
                raise  # Re-raise to let the management command handle it

class Poetry(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
    )
    title = models.CharField(max_length=200, db_index=True)
    body = SummernoteTextField()
    audio = models.FileField(upload_to='poem_audio/', blank=True, null=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='poems')
    anonymous = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name='poems')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    allow_comments = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return self.title

class Badge(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.ImageField(upload_to='badges/', blank=True, null=True)

    def __str__(self):
        return self.name

class Profile(models.Model):
    FONT_SIZE_CHOICES = [
        ('small', 'Small'),
        ('medium', 'Medium'),
        ('large', 'Large'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    favorite_tags = models.ManyToManyField(Tag, blank=True, related_name='favored_by')
    favorite_poets = models.ManyToManyField(User, blank=True, related_name='favored_poets')
    dark_mode = models.BooleanField(default=False)
    hide_followers = models.BooleanField(default=False)
    font_size = models.CharField(max_length=10, choices=FONT_SIZE_CHOICES, default='medium')
    streak = models.IntegerField(default=0)
    last_active = models.DateField(null=True, blank=True)
    badges = models.ManyToManyField(Badge, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

class EducationalResource(models.Model):
    RESOURCE_TYPE_CHOICES = [
        ('Video', 'Video'),
        ('Book', 'Book'),
        ('Article', 'Article'),
        ('Quiz', 'Quiz'),
    ]
    title = models.CharField(max_length=200)
    description = models.TextField()
    url = models.URLField()
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPE_CHOICES)
    topic = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name='resources')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.resource_type})"

class LearningPath(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    poems = models.ManyToManyField(Poetry, related_name='learning_paths', blank=True)
    resources = models.ManyToManyField(EducationalResource, related_name='learning_paths', blank=True)
    badge = models.ForeignKey(Badge, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class UserRole(models.Model):
    ROLE_CHOICES = [
        ('regular', 'Regular User'),
        ('parent', 'Parent'),
        ('child', 'Child'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='role')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='regular')
    parent = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='children')

    def __str__(self):
        return f"{self.user.username} - {self.role.title()}"

class ReportedContent(models.Model):
    REPORT_REASON_CHOICES = [
        ('spam', 'Spam'),
        ('harassment', 'Harassment'),
        ('nsfw', 'NSFW'),
        ('other', 'Other'),
    ]
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_made')
    poem = models.ForeignKey(Poetry, on_delete=models.CASCADE, related_name='reports')
    reason = models.CharField(max_length=20, choices=REPORT_REASON_CHOICES)
    description = models.TextField(blank=True, null=True)
    reported_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(blank=True, null=True)
    resolver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reports_resolved')

    def __str__(self):
        return f"Report by {self.reporter.username} on {self.poem.title} - {self.reason}"

class FavoritePoem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    poem = models.ForeignKey(Poetry, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'poem')
        indexes = [
            models.Index(fields=['user', 'poem']),
        ]

    def __str__(self):
        return f"{self.user.username} favorites {self.poem.title}"

class Following(models.Model):
    follower = models.ForeignKey(User, related_name='following_set', on_delete=models.CASCADE)
    following = models.ForeignKey(User, related_name='followers_set', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')
        verbose_name = 'Following'
        verbose_name_plural = 'Followings'

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"

class Comment(models.Model):
    poem = models.ForeignKey(Poetry, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    parent = models.ForeignKey(
        'self', null=True, blank=True, related_name='replies', on_delete=models.CASCADE
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['poem', 'user']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} on {self.poem.title}"

@receiver(post_save, sender=User)
def create_user_profile_role(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
        UserRole.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile_role(sender, instance, **kwargs):
    instance.profile.save()
    instance.role.save()

class News(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class DailyPrompt(models.Model):
    prompt_text = models.TextField()
    date = models.DateField(unique=True)

    def __str__(self):
        return f"Prompt for {self.date}"

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('like', 'Like'),
        ('comment', 'Comment'),
        ('favorite', 'Favorite'),
        ('follow', 'Follow'),
        ('mention', 'Mention'),
        ('prompt', 'Prompt Reminder'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    actor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications_from', null=True, blank=True)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    poem = models.ForeignKey(Poetry, on_delete=models.CASCADE, null=True, blank=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    extra_data = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']

class Folder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='folders')
    name = models.CharField(max_length=100)
    poems = models.ManyToManyField(Poetry, related_name='folders')

    def __str__(self):
        return f"{self.name} by {self.user.username}"

class Conversation(models.Model):
    participants = models.ManyToManyField(User, related_name='conversations')
    last_updated = models.DateTimeField(default=timezone.now)

    def __str__(self):
        participant_usernames = ', '.join([user.username for user in self.participants.all()])
        return f"Conversation between {participant_usernames}"

    class Meta:
        ordering = ['-last_updated']

class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation, related_name='messages', on_delete=models.CASCADE,
        null=True, blank=True
    )
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    body = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)  # Unsend

    def __str__(self):
        return f"From {self.sender.username} at {self.timestamp}"

    class Meta:
        ordering = ['timestamp']

class PoemReaction(models.Model):
    REACTION_CHOICES = [
        ('like', 'Like'),
        ('love', 'Love'),
        ('insightful', 'Insightful'),
        ('funny', 'Funny'),
        # Additional reaction types can go here
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    poem = models.ForeignKey(Poetry, on_delete=models.CASCADE, related_name='reactions')
    reaction_type = models.CharField(max_length=20, choices=REACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'poem', 'reaction_type')
        indexes = [
            models.Index(fields=['user', 'poem', 'reaction_type']),
        ]

    def __str__(self):
        return f"{self.user.username} reacted {self.reaction_type} to {self.poem.title}"

@receiver(post_save, sender=Tag)
def set_tag_image(sender, instance, created, **kwargs):
    if created:
        instance.fetch_image()
