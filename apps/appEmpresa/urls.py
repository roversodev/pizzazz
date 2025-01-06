from django.urls import path
from . import views


urlpatterns = [
    # Dashboard
    path('dashboard', views.dashboard, name='dashboard'),

    # Ingredientes
    path('ingredientes', views.ingredientes, name='ingredientes'),
    path('ingredientes/cadastrar', views.adicionar_ingredientes, name='adicionar_ingredientes'),
    path('ingredientes/<int:ingrediente_id>/editar/', views.editar_ingrediente, name='editar_ingrediente'),
    path('ingredientes/<int:ingrediente_id>/excluir/', views.deletar_ingrediente, name='deletar_ingrediente'),

    # Estoque
    path('estoque', views.estoque, name='estoque'),

    # Movimentações
    path('movimentacoes', views.movimentacoes, name='movimentacoes'),
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
    path('deletar-ingrediente-receita/<int:ingrediente_id>/', views.deletar_ingrediente_receita, name='deletar_ingrediente_receita'),

    # Pedidos
    path('pedidos', views.pedidos, name='pedidos'),
    path('pedidos/detalhes/<int:pedido_id>/', views.detalhes_pedido, name='detalhes_pedido'),

    # Perfil
    path('perfil', views.perfil, name='perfil'),
    path('editar-imagem-perfil/<int:user_id>/', views.editar_imagem_perfil, name='editar_imagem_perfil'),
    path('perfil_empresa', views.perfil_empresa, name='perfil_empresa'),

    # Avaliações
    path('avaliacoes', views.avaliacoes, name='avaliacoes'),

    # Controle de Usuários
    path('controle_usuarios', views.controle_usuarios, name='controle_usuarios'),
    path('cadastrar_user', views.cadastrar_user, name='cadastrar_user'),
]
