from django.db import models
from django.forms import ValidationError
from django.utils.timezone import now
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import pre_save
from django.dispatch import receiver

class CustomUser(AbstractUser):
    is_cliente = models.BooleanField(default=False)
    is_empresa = models.BooleanField(default=False)
    profile_image = models.ImageField(upload_to='profile_pics/', default='profile_pics/user2.jpg')
    is_first_login = models.BooleanField(default=True)

    def __str__(self):
        return self.username

    def is_dono(self):
        try:
            return self.empresa_usuario.papel == 'Dono'
        except:
            return False



class Empresa(models.Model):
    id_empresa = models.AutoField(primary_key=True)
    cnpj = models.TextField(max_length='18', unique=True)
    razao = models.TextField(max_length='100')
    nome_fantasia = models.TextField(max_length='100')
    data_abertura = models.DateField()
    subdominio = models.CharField(max_length=50)
    telefone = models.CharField(max_length=15)
    logo = models.ImageField(upload_to='logo_pics/', default='logo_pics/logo_default.png')
    data_criacao = models.DateTimeField(default=now)
    banner = models.ImageField(upload_to='empresa_banners/', null=True, blank=True)
    tempo_entrega_min = models.IntegerField(null=True, blank=True)
    tempo_entrega_max = models.IntegerField(null=True, blank=True)
    preco_frete = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=None)
    pedido_minimo = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=None)
    perfil_empresa = models.ImageField(upload_to='profile_pics/', default='profile_pics/user2.jpg')

    # Itens em destaque
    itens_destaque = models.ManyToManyField('Cardapio', related_name='em_destaque', blank=True)

    def __str__(self):
        return self.nome_fantasia

    def is_dono(self):
        try:
            return self.empresa_usuario.papel == 'Dono'
        except:
            return False

    def get_vendas_mensais(self):
        """Retorna as vendas mensais dos últimos 12 meses"""
        from django.db.models import Sum
        from django.db.models.functions import TruncMonth
        
        return Pedido.objects.filter(
            empresa=self,
            status='Concluido',
            data_pedido__year=now().year
        ).annotate(
            mes=TruncMonth('data_pedido')
        ).values('mes').annotate(
            total=Sum('total')
        ).order_by('mes')

    def get_estatisticas_gerais(self):
        """Retorna estatísticas gerais para o dashboard"""
        from django.db.models import Count, Avg
        
        pedidos_total = Pedido.objects.filter(empresa=self).count()
        clientes_ativos = Cliente.objects.filter(
            pedido__empresa=self
        ).distinct().count()
        
        avaliacao_media = AvaliacaoPedido.objects.filter(
            pedido__empresa=self
        ).aggregate(Avg('nota'))['nota__avg'] or 0
        
        itens_ativos = Cardapio.objects.filter(
            empresa=self, 
            ativo=True
        ).count()
        
        return {
            'pedidos_total': pedidos_total,
            'clientes_ativos': clientes_ativos,
            'avaliacao_media': round(avaliacao_media, 1),
            'itens_ativos': itens_ativos
        }



class EmpresaUsuario(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    usuario = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='empresa_usuario', null=False, blank=False)
    papel = models.CharField(max_length=50, choices=[
        ('Dono', 'Dono'),
        ('Caixa', 'Caixa'),
        ('Pizzaiolo', 'Pizzaiolo'),
    ])

    def __str__(self):
        return f'{self.usuario.username} - {self.papel}'

    def is_dono(self):
        try:
            return self.papel == 'Dono'
        except:
            return False




class Cliente(models.Model):
    id_cliente = models.AutoField(primary_key=True)
    usuario = models.OneToOneField(CustomUser, on_delete=models.CASCADE, null=True)
    nome = models.TextField(max_length='100')
    telefone = models.TextField(max_length='16')
    cpf = models.TextField(max_length='14')
    dataN = models.DateField()
    genero = models.TextField(max_length='20', null=True)
    data_criacao = models.DateTimeField(default=now)
    pizzarias_favoritas = models.ManyToManyField(Empresa, related_name='clientes_favoritos', blank=True)

    def __str__(self):
        return self.usuario.username

    def telefone_formatado(self):
        telefone_numeros = ''.join(filter(str.isdigit, self.telefone))
        return f"55{telefone_numeros}"

    def link_whatsapp(self):
        telefone_formatado = self.telefone_formatado()
        return f"https://wa.me/{telefone_formatado}"


class EnderecoCliente(models.Model):
    id_enderecocliente = models.AutoField(primary_key=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='enderecos')
    cep = models.CharField(max_length=9)
    endereco = models.CharField(max_length=255)
    numero = models.IntegerField(null=True)
    complemento = models.CharField(max_length=255, null=True, blank=True)
    bairro = models.CharField(max_length=255)
    estado = models.CharField(max_length=255)
    municipio = models.CharField(max_length=255)
    principal = models.BooleanField(default=False)
    data_criacao = models.DateTimeField(default=now)

    LOCAL_CHOICES = [
    ('casa', 'Casa'),
    ('trabalho', 'Trabalho'),
]

    local = models.CharField(
        max_length=10,
        choices=LOCAL_CHOICES,
        default='casa',
    )

    def save(self, *args, **kwargs):
        if self.local == 'casa':
            if not self.pk and EnderecoCliente.objects.filter(cliente=self.cliente, local='casa').exists():
                EnderecoCliente.objects.filter(cliente=self.cliente, local='casa').update(principal=False)
        
        elif self.local == 'trabalho':
            if not self.pk and EnderecoCliente.objects.filter(cliente=self.cliente, local='trabalho').exists():
                EnderecoCliente.objects.filter(cliente=self.cliente, local='trabalho').update(principal=False)

        if self.principal:
            EnderecoCliente.objects.filter(cliente=self.cliente, principal=True).exclude(id_enderecocliente=self.id_enderecocliente).update(principal=False)

        super(EnderecoCliente, self).save(*args, **kwargs)


    def __str__(self):
        return f"{self.cliente.nome}: {self.endereco}, {self.numero} - {self.municipio}/{self.estado}"


class EnderecoEmpresa(models.Model):
    id_enderecoempresa = models.AutoField(primary_key=True)
    empresa = models.OneToOneField(Empresa, on_delete=models.CASCADE)
    cep = models.CharField(max_length=9)
    endereco = models.CharField(max_length=255)
    numero = models.IntegerField(null=True)
    complemento = models.CharField(max_length=255, null=True, blank=True)
    bairro = models.CharField(max_length=255)
    estado = models.CharField(max_length=255)
    municipio = models.CharField(max_length=255)
    data_criacao = models.DateTimeField(default=now)

    def __str__(self):
        return f"{self.endereco}, {self.numero} - {self.municipio}/{self.estado}"
    


class Sequencia(models.Model):
    valor_atual = models.IntegerField(default=1000)

    @classmethod
    def obter_novo_valor(cls):
        sequencia = cls.objects.first()

        if not sequencia:
            sequencia = cls.objects.create(valor_atual=1000)

        # Incrementa o valor atual
        sequencia.valor_atual += 1
        sequencia.save()

        return sequencia.valor_atual




class Pedido(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    data_pedido = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=[('pendente', 'Pendente'), ('em_andamento', 'Em Andamento'), ('Concluido', 'Concluido')], default='pendente')
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    numero_pedido = models.IntegerField(unique=True, null=False, blank=False)
    canal = models.CharField(max_length=50, default='Manual')

    def calcular_total(self):
        total = sum(item.preco_total for item in self.itens.all())
        self.total = total
        self.save()

    def calcular_custo_total(self):
        custo_total = 0
        for item in self.itens.all():
            ingredientes = IngredienteCardapio.objects.filter(cardapio_item=item.cardapio_item)
            for ingrediente in ingredientes:
                quantidade_usada = ingrediente.quantidade * item.quantidade
                preco_unitario = ingrediente.ingrediente.preco_unitario
                custo_total += preco_unitario * quantidade_usada
        return custo_total

    def atualizar_estoque(self):
        for item in self.itens.all():
            ingredientes = IngredienteCardapio.objects.filter(cardapio_item=item.cardapio_item)
            for ingrediente in ingredientes:
                quantidade_usada = ingrediente.quantidade * item.quantidade
                estoque_item = Estoque.objects.get(ingrediente=ingrediente.ingrediente)
                try:
                    estoque_item.atualizar_estoque(quantidade_usada)
                except ValueError as e:
                    raise ValueError(f"Erro ao atualizar o estoque para {ingrediente.ingrediente.nome}: {str(e)}")

    def __str__(self):
        return f"Pedido #{self.numero_pedido} - {self.cliente.usuario.username} - {self.empresa.nome_fantasia}"
    
    def save(self, *args, **kwargs):
        if not self.numero_pedido:
            self.numero_pedido = Sequencia.obter_novo_valor()
        super(Pedido, self).save(*args, **kwargs)


class AvaliacaoPedido(models.Model):
    id_avaliacaopedido = models.AutoField(primary_key=True)
    pedido = models.OneToOneField(Pedido, on_delete=models.CASCADE, related_name='avaliacao')
    nota = models.IntegerField(choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')], default=5)
    comentario = models.TextField(null=True, blank=True)
    data_avaliacao = models.DateTimeField(auto_now_add=True)
    resposta = models.TextField(null=True, blank=True, unique=True)

    def __str__(self):
        return f"Avaliação do pedido #{self.pedido.id} - Nota: {self.nota} - {self.pedido.cliente.usuario.username}"

    class Meta:
        unique_together = ('pedido',)



class Categoria(models.Model):
    nome = models.CharField(max_length=50)
    ativo = models.BooleanField(default=True)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='categoria')


class Cardapio(models.Model):
    id_cardapio = models.AutoField(primary_key=True)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='cardapio')
    nome = models.CharField(max_length=100)
    descricao = models.TextField(null=True, blank=True)
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='categoria')
    imagem = models.ImageField(upload_to='cardapio_images/', null=True, blank=True)
    ativo = models.BooleanField(default=False)
    borda_recheada = models.BooleanField(default=False)
    completo = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.nome} - {self.empresa.nome_fantasia}"

    class Meta:
        unique_together = ('empresa', 'nome')





class ItemPedido(models.Model):
    id_itempedido = models.AutoField(primary_key=True)
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='itens')
    cardapio_item = models.ForeignKey(Cardapio, on_delete=models.CASCADE)
    quantidade = models.IntegerField(default=1)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    preco_total = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        self.preco_total = self.quantidade * self.preco_unitario
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.cardapio_item.nome} - {self.quantidade}x"

    class Meta:
        unique_together = ('pedido', 'cardapio_item')


class Ingrediente(models.Model):
    id_ingrediente = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=100)
    unidade = models.CharField(max_length=50, choices=[('kg', 'kg'), ('g', 'g'), ('unidade', 'Unidade'), ('litro', 'Litro')], default='kg')
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='ingredientes')
    quantidade_inicial = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    estoque_minimo = models.DecimalField(max_digits=10, decimal_places=2, default=0)


    def __str__(self):
        return self.nome


class Estoque(models.Model):
    id_estoque = models.AutoField(primary_key=True)
    ingrediente = models.ForeignKey(Ingrediente, on_delete=models.CASCADE)
    quantidade_disponivel = models.DecimalField(max_digits=10, decimal_places=2)
    data_atualizacao = models.DateTimeField(auto_now=True)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='estoque')

    def __str__(self):
        return f"{self.ingrediente.nome} - {self.quantidade_disponivel} {self.ingrediente.unidade}"

    def atualizar_estoque(self, quantidade_usada):
        if self.quantidade_disponivel >= quantidade_usada:
            self.quantidade_disponivel -= quantidade_usada
            self.save()
        else:
            raise ValueError(f"Estoque insuficiente para {self.ingrediente.nome}.")



class MovimentacaoEstoque(models.Model):
    ingrediente = models.ForeignKey(Ingrediente, on_delete=models.CASCADE)
    tipo = models.CharField(choices=[('entrada', 'Entrada'), ('saida', 'Saída')], max_length=10)
    quantidade = models.DecimalField(max_digits=10, decimal_places=2)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    data = models.DateTimeField(auto_now_add=True)
    observacao = models.TextField(blank=True, null=True)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='movimentacao_estoque')
    atendente = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='atendente_movi_estoque')

    def adicionar_estoque(self, quantidade, preco_unitario):
        """
        Adiciona a quantidade ao estoque e ajusta o custo médio.
        """
        if quantidade > 0:
            novo_total = self.quantidade + quantidade
            novo_valor_total = (self.quantidade * self.preco_unitario + quantidade * preco_unitario)
            self.preco_unitario = novo_valor_total / novo_total
            self.quantidade = novo_total
            self.save()

    def remover_estoque(self, quantidade):
        """
        Remove a quantidade do estoque. Verifica se é possível antes de remover.
        """
        if quantidade > self.quantidade:
            raise ValueError("Quantidade insuficiente em estoque.")
        self.quantidade -= quantidade
        self.save()
        if self.quantidade < self.estoque_minimo:
            # Criar notificação ou alerta
            print(f"⚠️ Estoque de {self.nome} abaixo do mínimo!")


class IngredienteCardapio(models.Model):
    id_ingredientecardapio = models.AutoField(primary_key=True)
    cardapio_item = models.ForeignKey(Cardapio, on_delete=models.CASCADE, related_name='ingredientes')
    ingrediente = models.ForeignKey(Ingrediente, on_delete=models.CASCADE)
    quantidade = models.DecimalField(max_digits=10, decimal_places=2)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='ingredienteCardapio')

    def __str__(self):
        return f"{self.quantidade} {self.ingrediente.unidade} de {self.ingrediente.nome} para {self.cardapio_item.nome}"
    

class Carrinho(models.Model):
    id_carrinho = models.AutoField(primary_key=True)
    cliente = models.OneToOneField(Cliente, on_delete=models.CASCADE)
    pizzaria = models.ForeignKey(Empresa, on_delete=models.CASCADE)

    def adicionar_item(self, item):
        # Verifica se o item pertence a uma empresa diferente
        if self.pizzaria != item.cardapio_item.empresa:
            # Limpar o carrinho e associar a nova pizzaria
            self.itens.all().delete()
            self.pizzaria = item.cardapio_item.empresa
        self.itens.create(cardapio_item=item, quantidade=1, preco_unitario=item.cardapio_item.preco)
        self.save()

    def clean(self):
        # Verifica se o carrinho contém itens de empresas diferentes
        empresas = set(item.cardapio_item.empresa for item in self.itens.all())
        if len(empresas) > 1:
            raise ValidationError("O carrinho não pode ter itens de empresas diferentes.")
    
    def save(self, *args, **kwargs):
        self.clean()  # Chamando clean para garantir a validação antes de salvar
        super().save(*args, **kwargs)

class ItemCarrinho(models.Model):
    carrinho = models.ForeignKey(Carrinho, related_name='itens', on_delete=models.CASCADE)
    cardapio_item = models.ForeignKey(Cardapio, on_delete=models.CASCADE)
    quantidade = models.IntegerField(default=1)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    preco_total = models.DecimalField(max_digits=10, decimal_places=2, editable=False)

    def clean(self):
        # Verifica se o carrinho tem itens de empresas diferentes
        if self.carrinho.pizzaria != self.cardapio_item.empresa:
            raise ValidationError("O carrinho não pode ter itens de empresas diferentes.")

    def save(self, *args, **kwargs):
        self.preco_total = self.quantidade * self.preco_unitario  # Recalcula o preço total
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantidade} x {self.cardapio_item.nome} no carrinho"

# Sistema de Cupons
class Cupom(models.Model):
    codigo = models.CharField(max_length=20, unique=True)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20, choices=[
        ('valor_fixo', 'Valor Fixo'),
        ('percentual', 'Percentual'),
    ])
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    data_inicio = models.DateTimeField()
    data_fim = models.DateTimeField()
    valor_minimo_pedido = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    quantidade_maxima = models.IntegerField(default=1)
    quantidade_utilizada = models.IntegerField(default=0)
    ativo = models.BooleanField(default=True)

    def esta_valido(self):
        agora = now()
        return (
            self.ativo and
            self.data_inicio <= agora <= self.data_fim and
            self.quantidade_utilizada < self.quantidade_maxima
        )

# Programa de Fidelidade
class ProgramaFidelidade(models.Model):
    empresa = models.OneToOneField(Empresa, on_delete=models.CASCADE)
    pontos_por_real = models.IntegerField(default=1)
    valor_ponto = models.DecimalField(max_digits=10, decimal_places=2, default=0.01)
    pontos_minimos_resgate = models.IntegerField(default=100)

class PontosFidelidade(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    pontos = models.IntegerField(default=0)
    
    def adicionar_pontos(self, valor_pedido):
        programa = ProgramaFidelidade.objects.get(empresa=self.empresa)
        pontos_ganhos = int(valor_pedido * programa.pontos_por_real)
        self.pontos += pontos_ganhos
        self.save()

# Sistema de Notificações
class Notificacao(models.Model):
    TIPOS_NOTIFICACAO = [
        ('pedido_status', 'Status do Pedido'),
        ('promocao', 'Promoção'),
        ('sistema', 'Sistema'),
    ]
    
    usuario = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20, choices=TIPOS_NOTIFICACAO)
    titulo = models.CharField(max_length=100)
    mensagem = models.TextField()
    data_criacao = models.DateTimeField(auto_now_add=True)
    lida = models.BooleanField(default=False)
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, null=True, blank=True)

# Histórico de Status de Pedidos
class HistoricoPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='historico')
    status = models.CharField(max_length=50, choices=[
        ('pendente', 'Pendente'),
        ('confirmado', 'Confirmado'),
        ('preparando', 'Preparando'),
        ('saiu_entrega', 'Saiu para Entrega'),
        ('entregue', 'Entregue'),
        ('cancelado', 'Cancelado'),
    ])
    observacao = models.TextField(null=True, blank=True)
    data_alteracao = models.DateTimeField(auto_now_add=True)
    alterado_por = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)

# Pagamentos
class Pagamento(models.Model):
    pedido = models.OneToOneField(Pedido, on_delete=models.CASCADE)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    forma_pagamento = models.CharField(max_length=50, choices=[
        ('dinheiro', 'Dinheiro'),
        ('cartao_credito', 'Cartão de Crédito'),
        ('cartao_debito', 'Cartão de Débito'),
        ('pix', 'PIX'),
    ])
    status = models.CharField(max_length=20, choices=[
        ('pendente', 'Pendente'),
        ('aprovado', 'Aprovado'),
        ('recusado', 'Recusado'),
    ])
    data_pagamento = models.DateTimeField(auto_now_add=True)
    codigo_transacao = models.CharField(max_length=100, null=True, blank=True)