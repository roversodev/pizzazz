from django.apps import AppConfig


class AppempresaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.appEmpresa'

    def ready(self):
        from .scheduler import start_scheduler
        start_scheduler()
        import apps.authentication.signals
