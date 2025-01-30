from django.urls import path
from . import views


urlpatterns = [
    # Dashboard
    path("", views.Dashboard.adminDashboard, name="adminD"),
    path("atualizar_grafico/", views.Dashboard.atualizar_grafico, name="atualizar_grafico"),
    path('exportar_dados/<int:ano>/', views.Dashboard.exportar_dados_excel, name='exportar_dados_excel'),
    path('baixar_dados', views.Dashboard.baixar_dados, name='baixar_dados'),
    #Empresas
    path("empresas/", views.Empresas_Admin.empresas, name="admin_empresas"),
    path("empresas/toggle_ativo_empresa/<int:empresa_id>", views.Empresas_Admin.toggle_ativo_empresa, name="toggle_ativo_empresa"),
    # Perfil
    path("perfil/", views.Perfil.perfil_admin, name='perfil_admin'),
    path("editar_imagem_perfil_admin/<int:user_id>", views.Perfil.editar_imagem_perfil_admin, name='editar_imagem_perfil_admin'),
    path("controle_usuarios", views.Controle_Users.controle_usuarios_admin, name='controle_usuarios_admin'),
    path("controle_usuarios/toggle_ativo_user/<int:user_id>", views.Controle_Users.toggle_ativo_user, name="toggle_ativo_user"),
    path("create_user_admin/", views.Controle_Users.create_user_admin, name="create_user_admin"),
    # Pedidos
    path("pedidos/", views.Pedidos.pedidos_admin, name="pedidos_admin"),
    path("pedidos/<int:pedido_numero>", views.Pedidos.detalhes_pedido_admin, name='detalhes_pedido_admin'),
    path("pedidos/<int:pedido_numero>/alterar_status/", views.Pedidos.alterar_status, name="alterar_status"),
]