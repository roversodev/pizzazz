from django.apps import AppConfig


class AppempresaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.appEmpresa'

    def ready(self):
        import apps.authentication.signals
