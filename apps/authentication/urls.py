from django.urls import path, re_path
from apps.authentication import views

urlpatterns = [

    # Logins
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('em-breve/', views.em_breve, name='em_breve'),

    # Cadastrar Parceiros/Empresas
    path('cadastrar/parceiros/', views.cadastrar_parceiros, name='cadastrar_parceiros'),
    path('cadastrar/parceiros/etapa2/<int:empresa_id>/', views.cadastrar_parceiros_etapa2, name='cadastrar_parceiros_etapa2'),
    path('cadastrar/parceiros/etapa3/<int:empresa_id>/', views.cadastrar_parceiros_etapa3, name='cadastrar_parceiros_etapa3'),

    # Cadastrar Clientes
    path('cadastrar/clientes/', views.cadastrar_clientes, name='cadastrar_clientes'),
    path('cadastrar/clientes/etapa2/<int:cliente_id>/', views.cadastrar_clientes_etapa2, name='cadastrar_clientes_etapa2'),

    # Resetar Senha
    path('reset-password/', views.request_reset_password, name='request_reset_password'),
    path('verificar-codigo/<int:user_id>', views.verificar_codigo, name='verificar_codigo'),
    path('reset-password/<int:user_id>/<str:verification_code>/', views.reset_password, name='reset_password'),

]
