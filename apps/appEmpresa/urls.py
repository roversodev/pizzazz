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
    path('cardapio/categoria/cadastrar', views.adicionar_categoria, name='adicionar_categoria'),
    path('cardapio/categoria/<int:item_id>/deletar', views.deletar_categoria, name='deletar_categoria'),
    path('cardapio/categoria/<int:categoria_id>/adicionar/', views.adicionar_item, name='adicionar_item'),
    path('cardapio/item/<int:item_id>/editar/', views.editar_item, name='editar_item'),
    path('cardapio/item/<int:item_id>/deletar/', views.deletar_item, name='deletar_item'),
    path('cardapio/item/<int:item_id>/toggle-ativo/', views.toggle_ativo_item, name='toggle_ativo_item'),
]
