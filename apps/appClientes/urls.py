from django.urls import path, re_path
from apps.appClientes import views

urlpatterns = [

    # Logins
    path('', views.restaurantes, name='restaurantes'),
    path('busca', views.busca, name='busca'),
    path('pedidos', views.pedidos, name='pedidos'),
    path('perfil', views.perfil, name='perfil'),

]
