from django.apps import AppConfig


class PoetryAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'poetry_app'

    def ready(self):
        import poetry_app.signals