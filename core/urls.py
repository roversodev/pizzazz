from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin-django/', admin.site.urls),
    # LANDING PAGES
    path("", include("apps.lp.urls")),
    # AUTH LOGIN/REGISTRAR - PARCEIROS E CLIENTES
    path("", include("apps.authentication.urls")),
    # ADMIN DA EMPRESA
    path("empresas/<str:cnpj>/", include("apps.appEmpresa.urls")),
    # ADMIN PIZZAZZZ
    path("admin/", include("apps.admin.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)