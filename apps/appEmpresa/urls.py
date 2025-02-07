from django.urls import path
from . import views


urlpatterns = [
    path('get_notifications/', views.get_notifications, name='get_notifications'),
    path('get_notifications_all/', views.get_notifications_all, name='get_notifications_all'),
    path('mark_notification_as_read/<int:notification_id>', views.mark_notification_as_read, name='mark_notification_as_read'),
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # Ingredientes
    path('ingredientes/', views.ingredientes, name='ingredientes'),
    path('ingredientes/cadastrar', views.adicionar_ingredientes, name='adicionar_ingredientes'),
    path('ingredientes/<int:ingrediente_id>/editar/', views.editar_ingrediente, name='editar_ingrediente'),
    path('ingredientes/<int:ingrediente_id>/excluir/', views.deletar_ingrediente, name='deletar_ingrediente'),

    # Estoque
    path('estoque/', views.estoque, name='estoque'),

    # Movimentações
    path('movimentacoes/', views.movimentacoes, name='movimentacoes'),
    path('movimentacao_grafico', views.movimentacao_grafico, name='movimentacao_grafico'),
    path('cadastrar_movimentacao', views.cadastrar_movimentacao, name='cadastrar_movimentacao'),

    # Cardápio
    path('cardapio', views.cardapio, name='cardapio'),
    # Categoria CRUD
    path('cardapio/categoria/cadastrar', views.adicionar_categoria, name='adicionar_categoria'),
    path('cardapio/categoria/<int:item_id>/editar', views.editar_categoria, name='editar_categoria'),
    path('cardapio/categoria/<int:item_id>/deletar', views.deletar_categoria, name='deletar_categoria'),
    path('cardapio/categoria/<int:categoria_id>/toggle-ativo/', views.toggle_ativo_categoria, name='toggle_ativo_categoria'),
    # Item CRUD
    path('cardapio/item/<int:categoria_id>/adicionar/', views.adicionar_item, name='adicionar_item'),
    path('cardapio/item/<int:item_id>/editar/', views.editar_item, name='editar_item'),
    path('cardapio/item/<int:item_id>/deletar/', views.deletar_item, name='deletar_item'),
    path('cardapio/item/<int:item_id>/toggle-ativo/', views.toggle_ativo_item, name='toggle_ativo_item'),

    # Receitas
    path('receitas', views.receitas, name='receitas'),
    path('receitas/cadastrar', views.cadastrar_receita, name='cadastrar_receita'),
    path('verificar_completo/', views.verificar_completo, name='verificar_completo'),
    path('deletar-ingrediente-receita/<int:ingrediente_id>/', views.deletar_ingrediente_receita, name='deletar_ingrediente_receita'),

    # Pedidos
    path('pedidos', views.pedidos, name='pedidos'),
    path('pedidos/detalhes/<int:pedido_id>/', views.detalhes_pedido, name='detalhes_pedido'),
    path('exportar_pedidos/', views.exportar_pedidos, name='exportar_pedidos'),
    path('pedidos/criar', views.pedido_manual, name='pedido_manual'),
    path('pedidos/alterar_status/<int:pedido_numero>', views.alterar_status, name="alterar_status"),
    # Requisições AJAX
    path('buscar_cliente/', views.buscar_cliente, name='buscar_cliente'),
    path('cadastro_cliente_manual/', views.cadastro_cliente_manual, name="cadastro_cliente_manual"),
    path('buscar_endereco_cliente/<int:cliente_id>/', views.buscar_endereco, name='buscar_endereco'),

    # Perfil
    path('perfil', views.perfil, name='perfil'),
    path('editar-imagem-perfil/<int:user_id>/', views.editar_imagem_perfil, name='editar_imagem_perfil'),
    path('perfil_empresa', views.perfil_empresa, name='perfil_empresa'),

    # Avaliações
    path('avaliacoes', views.avaliacoes, name='avaliacoes'),

    # Controle de Usuários
    path('controle_usuarios', views.controle_usuarios, name='controle_usuarios'),
    path('cadastrar_user', views.cadastrar_user, name='cadastrar_user'),
    path('excluir_user/<int:user_id>', views.excluir_user, name='excluir_user'),

    # Pizzaiolo
    path('pizzaiolo/', views.pizzaiolo, name='pizzaiolo'),
    path('api/pedidos/', views.listar_pedidos, name='listar_pedidos'),
    path('api/pedidos/<int:pedido_id>/status/', views.atualizar_status_pedido, name='atualizar_status_pedido'),
    path('api/pedido/<int:pedido_id>/receita/', views.receita_pedido, name='receita_pedido'),
    
    # Relatório Financeiro
    path('relatorio_financeiro/', views.relatorio_financeiro, name='relatorio_financeiro'),

]
