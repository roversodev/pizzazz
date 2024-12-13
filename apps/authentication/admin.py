from django.contrib import admin
from .models import CustomUser, Cliente, Empresa, EnderecoCliente, EnderecoEmpresa
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

User = get_user_model()
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass


# Registra o CustomUser com o modelo de administração
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'is_cliente', 'is_empresa', 'is_first_login', 'date_joined')
    search_fields = ('email',)
    list_filter = ('is_cliente', 'is_empresa')

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
