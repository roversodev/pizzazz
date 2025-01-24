from django.contrib import admin
from .models import (
    CustomUser, Cliente, Empresa, EnderecoCliente, EnderecoEmpresa,
    EmpresaUsuario, EnderecoPedido, HistoricoPedido, Pedido, AvaliacaoPedido, Categoria, Cardapio,
    ItemPedido, Ingrediente, Estoque, MovimentacaoEstoque, IngredienteCardapio,
    Carrinho, ItemCarrinho, RelatorioFinanceiro, Sequencia
)
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

User = get_user_model()
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass


# Registra o CustomUser  com o modelo de administração
class CustomUserAdmin(UserAdmin):
    # Campos a serem exibidos na lista de usuários
    list_display = ('email', 'is_cliente', 'is_empresa', 'is_first_login', 'is_adm', 'papel_adm', 'date_joined')
    search_fields = ('email',)
    list_filter = ('is_cliente', 'is_empresa', 'is_adm', 'papel_adm')

    # Campos a serem exibidos na página de edição do usuário
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Informações Pessoais', {'fields': ('first_name', 'last_name', 'profile_image', 'is_cliente', 'is_empresa', 'is_first_login', 'is_adm', 'papel_adm')}),
        ('Permissões', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Datas', {'fields': ('last_login', 'date_joined')}),
    )

    # Campos que podem ser editados na página de edição do usuário
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'is_cliente', 'is_empresa', 'is_first_login', 'is_adm', 'papel_adm')}
        ),
    )

    # Define o modelo que será usado para criar novos usuários
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

# Registra o CustomUser Admin
admin.site.register(CustomUser, CustomUserAdmin)


# Registra o Cliente com o modelo de administração
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'nome', 'telefone', 'cpf', 'data_criacao')
    search_fields = ('usuario__email', 'nome', 'cpf')
    list_filter = ('data_criacao',)

admin.site.register(Cliente, ClienteAdmin)


# Registra a Empresa com o modelo de administração
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('nome_fantasia', 'cnpj', 'razao', 'telefone', 'subdominio', 'data_criacao')
    search_fields = ('nome_fantasia', 'cnpj', 'razao')
    list_filter = ('data_criacao',)

admin.site.register(Empresa, EmpresaAdmin)


# Registra o EnderecoCliente com o modelo de administração
class EnderecoClienteAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'local', 'endereco', 'numero', 'municipio', 'estado', 'cep', 'principal')
    search_fields = ('cliente__usuario__email', 'cliente__nome', 'municipio')
    list_filter = ('principal', 'estado')

admin.site.register(EnderecoCliente, EnderecoClienteAdmin)


# Registra o EnderecoEmpresa com o modelo de administração
class EnderecoEmpresaAdmin(admin.ModelAdmin):
    list_display = ('empresa', 'endereco', 'numero', 'municipio', 'estado', 'cep')
    search_fields = ('empresa__nome_fantasia', 'empresa__cnpj', 'municipio')
    list_filter = ('estado',)

admin.site.register(EnderecoEmpresa, EnderecoEmpresaAdmin)


# Registra o EmpresaUsuario com o modelo de administração
class EmpresaUsuarioAdmin(admin.ModelAdmin):
    list_display = ('empresa', 'usuario', 'papel')
    search_fields = ('empresa__nome_fantasia', 'usuario__username')
    list_filter = ('papel',)

admin.site.register(EmpresaUsuario, EmpresaUsuarioAdmin)


# Registra o Pedido com o modelo de administração
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('numero_pedido', 'cliente', 'empresa', 'total', 'data_pedido',)
    search_fields = ('cliente__cpf', 'empresa__nome_fantasia', 'numero_pedido')
    list_filter = ('historico__status', 'data_pedido')

admin.site.register(Pedido, PedidoAdmin)

# Registra o Pedido com o modelo de administração
class EnderecoPedidoAdmin(admin.ModelAdmin):
    list_display = ('cep', 'endereco')
    search_fields = ('pedido__cliente__cpf', 'pedido__empresa__nome_fantasia', 'pedido__empresa__cnpj', 'pedido__numero_pedido')
    list_filter = ('pedido__historico__status', 'pedido__data_pedido')

admin.site.register(EnderecoPedido, EnderecoPedidoAdmin)

# Registra o HistoricoPedido com o modelo de administração
class HistoricoPedidoAdmin(admin.ModelAdmin):

    search_fields = ('pedido__cliente__cpf', 'pedido__empresa__nome_fantasia', 'pedido__empresa__cnpj', 'pedido__numero_pedido')
    list_filter = ('status', 'data_alteracao')

admin.site.register(HistoricoPedido, HistoricoPedidoAdmin)


# Registra a AvaliacaoPedido com o modelo de administração
class AvaliacaoPedidoAdmin(admin.ModelAdmin):
    list_display = ('pedido', 'nota', 'comentario', 'data_avaliacao')
    search_fields = ('pedido__cliente__usuario__email', 'pedido__empresa__nome_fantasia')
    list_filter = ('nota',)

admin.site.register(AvaliacaoPedido, AvaliacaoPedidoAdmin)


# Registra a Categoria com o modelo de administração
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'ativo', 'empresa')
    search_fields = ('nome', 'empresa__nome_fantasia')
    list_filter = ('ativo',)

admin.site.register(Categoria, CategoriaAdmin)


# Registra o Cardapio com o modelo de administração
class CardapioAdmin(admin.ModelAdmin):
    list_display = ('nome', 'descricao', 'preco', 'empresa', 'categoria', 'ativo', 'borda_recheada', 'completo')
    search_fields = ('nome', 'empresa__nome_fantasia', 'categoria__nome')
    list_filter = ('ativo', 'categoria')

admin.site.register(Cardapio, CardapioAdmin)


# Registra o ItemPedido com o modelo de administração
class ItemPedidoAdmin(admin.ModelAdmin):
    list_display = ('id_itempedido', 'cardapio_item', 'quantidade', 'preco_unitario', 'preco_total')
    search_fields = ('pedido__cliente__usuario__email', 'cardapio_item__nome')
    list_filter = ('pedido__historico__status',)

admin.site.register(ItemPedido, ItemPedidoAdmin)


# Registra o Ingrediente com o modelo de administração
class IngredienteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'preco_unitario', 'quantidade_inicial', 'estoque_minimo', 'empresa')
    search_fields = ('nome', 'empresa__nome_fantasia')
    list_filter = ('empresa',)

admin.site.register(Ingrediente, IngredienteAdmin)


# Registra o Estoque com o modelo de administração
class EstoqueAdmin(admin.ModelAdmin):
    list_display = ('ingrediente', 'quantidade_disponivel', 'empresa')
    search_fields = ('ingrediente__nome', 'empresa__nome_fantasia')
    list_filter = ('empresa',)

admin.site.register(Estoque, EstoqueAdmin)


# Registra a MovimentacaoEstoque com o modelo de administração
class MovimentacaoEstoqueAdmin(admin.ModelAdmin):
    list_display = ('ingrediente', 'tipo', 'quantidade', 'preco_unitario', 'data', 'observacao', 'empresa', 'atendente')
    search_fields = ('ingrediente__nome', 'empresa__nome_fantasia', 'atendente__username')
    list_filter = ('tipo', 'data', 'empresa')

admin.site.register(MovimentacaoEstoque, MovimentacaoEstoqueAdmin)


# Registra o IngredienteCardapio com o modelo de administração
class IngredienteCardapioAdmin(admin.ModelAdmin):
    list_display = ('cardapio_item', 'ingrediente', 'quantidade', 'empresa')
    search_fields = ('cardapio_item__nome', 'ingrediente__nome', 'empresa__nome_fantasia')
    list_filter = ('empresa',)

admin.site.register(IngredienteCardapio, IngredienteCardapioAdmin)


# Registra o Carrinho com o modelo de administração
class CarrinhoAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'pizzaria')
    search_fields = ('cliente__usuario__email', 'pizzaria__nome_fantasia')

admin.site.register(Carrinho, CarrinhoAdmin)


# Registra o ItemCarrinho com o modelo de administração
class ItemCarrinhoAdmin(admin.ModelAdmin):
    list_display = ('carrinho', 'cardapio_item', 'quantidade', 'preco_unitario', 'preco_total')
    search_fields = ('carrinho__cliente__usuario__email', 'cardapio_item__nome')

admin.site.register(ItemCarrinho, ItemCarrinhoAdmin)


class RelatorioFinanceiroAdmin(admin.ModelAdmin):
    list_display = ('empresa', 'ano', 'mes', 'vendas_mes_atual', 'lucro_mes_atual', 'vendas_mes_passado', 'lucro_mes_passado', 'variacao_percentual_lucro')
    search_fields = ('empresa__nome', 'ano', 'mes')  # Ajuste conforme necessário

admin.site.register(RelatorioFinanceiro, RelatorioFinanceiroAdmin)
