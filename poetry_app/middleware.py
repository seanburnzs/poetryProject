# poetry_app/middleware.py

from datetime import date, timedelta
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings  # Import settings to access STATIC_URL
from .models import Badge

class UpdateUserStreakMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Exclude static file requests from being processed by this middleware
        if request.path.startswith(settings.STATIC_URL):
            return None

        if request.user.is_authenticated:
            profile = request.user.profile
            today = date.today()
            streak_updated = False

            if profile.last_active:
                delta = today - profile.last_active
                if delta.days == 1:
                    profile.streak += 1
                    streak_updated = True
                elif delta.days > 1:
                    profile.streak = 1
            else:
                profile.streak = 1

            profile.last_active = today
            profile.save()

            # Award badges if streak is updated
            if streak_updated:
                if profile.streak == 7:
                    badge, created = Badge.objects.get_or_create(
                        name='Weekly Wordsmith',
                        defaults={'description': 'Logged in for 7 consecutive days'}
                    )
                    if created:
                        profile.badges.add(badge)
                elif profile.streak == 30:
                    badge, created = Badge.objects.get_or_create(
                        name='Monthly Maven',
                        defaults={'description': 'Logged in for 30 consecutive days'}
                    )
                    if created:
                        profile.badges.add(badge)
