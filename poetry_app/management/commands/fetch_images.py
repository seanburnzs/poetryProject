from django.core.management.base import BaseCommand
from poetry_app.models import Tag
import requests
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Fetch and set image URLs for tags based on their names.'

    def handle(self, *args, **kwargs):
        tags = Tag.objects.filter(category='Topic', image_url__isnull=True)
        total_tags = tags.count()
        if total_tags == 0:
            self.stdout.write(self.style.WARNING('No tags found without images.'))
            return

        self.stdout.write(self.style.NOTICE(f'Found {total_tags} tags to process.'))
        for tag in tags:
            try:
                tag.fetch_image()
                if tag.image_url:
                    self.stdout.write(self.style.SUCCESS(f'Image set for tag: {tag.name}'))
                else:
                    self.stdout.write(self.style.WARNING(f'No image found for tag: {tag.name}'))
            except requests.exceptions.RequestException as e:
                self.stderr.write(self.style.ERROR(f"Error fetching image for tag '{tag.name}': {e}"))
