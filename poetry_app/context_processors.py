import datetime
from django.conf import settings

def current_year(request):
    return {
        'current_year': datetime.datetime.now().year
    }

def notifications_enabled(request):
    return {
        'NOTIFICATIONS_ENABLED': settings.NOTIFICATIONS_ENABLED
    }
