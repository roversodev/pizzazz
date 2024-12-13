from django.urls import path, re_path
from apps.authentication import views

urlpatterns = [

    # Logins
    path('login/', views.login, name='login'),
    path('logout', views.logout, name='logout'),

    # Cadastrar Parceiros/Empresas
    path('cadastrar/parceiros', views.cadastrar_parceiros, name='cadastrar_parceiros'),
    path('cadastrar/parceiros/etapa2/<int:empresa_id>/', views.cadastrar_parceiros_etapa2, name='cadastrar_parceiros_etapa2'),
    path('cadastrar/parceiros/etapa3/<int:empresa_id>/', views.cadastrar_parceiros_etapa3, name='cadastrar_parceiros_etapa3'),

    # Cadastrar Clientes
    path('cadastrar/clientes', views.cadastrar_clientes, name='cadastrar_clientes'),
    path('cadastrar/clientes/etapa2/<int:cliente_id>/', views.cadastrar_clientes_etapa2, name='cadastrar_clientes_etapa2'),

]
