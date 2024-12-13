from django.test import TestCase
from decimal import Decimal
from .models import CustomUser, Empresa, Cliente, Cardapio, Ingrediente, Estoque, Pedido, ItemPedido, IngredienteCardapio, Carrinho, ItemCarrinho

class PedidoTestCase(TestCase):
    
    def setUp(self):
        # Criação do usuário Cliente
        usuario_cliente = CustomUser.objects.create_user(
            username='cliente1',
            password='senha123',
            is_cliente=True
        )
        
        # Criação do usuário Empresa
        usuario_empresa = CustomUser.objects.create_user(
            username='empresa1',
            password='senha123',
            is_empresa=True
        )
        
        # Criação da Empresa
        self.empresa = Empresa.objects.create(
            usuario=usuario_empresa,
            cnpj='12345678000199',
            razao='Razão Social',
            nome_fantasia='Empresa Teste',
            data_abertura='2020-05-20',
            subdominio='empresa1',
            telefone='5511987654321'
        )
        
        # Criação do Cliente
        self.cliente = Cliente.objects.create(
            usuario=usuario_cliente,
            nome='João da Silva',
            telefone='5511998765432',
            cpf='12345678901',
            dataN='1990-08-15'
        )
        
        # Criando Ingredientes
        self.ingrediente1 = Ingrediente.objects.create(
            nome='Tomate',
            unidade='kg',
            preco_unitario=Decimal('5.00')
        )
        
        self.ingrediente2 = Ingrediente.objects.create(
            nome='Queijo',
            unidade='kg',
            preco_unitario=Decimal('20.00')
        )

        # Criando Estoque para os Ingredientes
        self.estoque_ingrediente1 = Estoque.objects.create(
            ingrediente=self.ingrediente1,
            quantidade_disponivel=Decimal('100.00')
        )

        self.estoque_ingrediente2 = Estoque.objects.create(
            ingrediente=self.ingrediente2,
            quantidade_disponivel=Decimal('50.00')
        )

        # Criando um Cardápio
        self.cardapio_item = Cardapio.objects.create(
            empresa=self.empresa,
            nome='Pizza de Tomate e Queijo',
            descricao='Pizza deliciosa com tomate e queijo',
            preco=Decimal('40.00'),
            categoria='Pizza'
        )

        # Associando Ingredientes ao Cardápio
        IngredienteCardapio.objects.create(
            cardapio_item=self.cardapio_item,
            ingrediente=self.ingrediente1,
            quantidade=Decimal('0.5'),  # 0.5 kg de tomate por pizza
            unidade='kg'
        )

        IngredienteCardapio.objects.create(
            cardapio_item=self.cardapio_item,
            ingrediente=self.ingrediente2,
            quantidade=Decimal('0.2'),  # 0.2 kg de queijo por pizza
            unidade='kg'
        )

    def test_pedido_total(self):
        # Criando um Pedido
        pedido = Pedido.objects.create(
            cliente=self.cliente,
            empresa=self.empresa
        )

        # Criando um ItemPedido (2 pizzas)
        item_pedido = ItemPedido.objects.create(
            pedido=pedido,
            cardapio_item=self.cardapio_item,
            quantidade=2,
            preco_unitario=self.cardapio_item.preco
        )

        # Calculando o total do pedido
        pedido.calcular_total()
        
        # Teste se o total está correto
        self.assertEqual(pedido.total, Decimal('80.00'))  # 2 pizzas * 40.00 cada

    def test_atualizar_estoque(self):
        # Criando um Pedido
        pedido = Pedido.objects.create(
            cliente=self.cliente,
            empresa=self.empresa
        )

        # Criando um ItemPedido (2 pizzas)
        item_pedido = ItemPedido.objects.create(
            pedido=pedido,
            cardapio_item=self.cardapio_item,
            quantidade=2,
            preco_unitario=self.cardapio_item.preco
        )

        # Atualizando o estoque após o pedido
        pedido.atualizar_estoque()

        # Atualizando o objeto de estoque para verificar as quantidades
        self.estoque_ingrediente1.refresh_from_db()
        self.estoque_ingrediente2.refresh_from_db()

        # Teste se o estoque foi atualizado corretamente
        self.assertEqual(self.estoque_ingrediente1.quantidade_disponivel, Decimal('99.00'))  # 100 - (0.5 * 2)
        self.assertEqual(self.estoque_ingrediente2.quantidade_disponivel, Decimal('49.60'))  # 50 - (0.2 * 2)

    def test_calcular_custo_total(self):
        # Criando um Pedido
        pedido = Pedido.objects.create(
            cliente=self.cliente,
            empresa=self.empresa
        )

        # Criando um ItemPedido (2 pizzas)
        item_pedido = ItemPedido.objects.create(
            pedido=pedido,
            cardapio_item=self.cardapio_item,
            quantidade=2,
            preco_unitario=self.cardapio_item.preco
        )

        # Calculando o custo total do pedido
        custo_total = pedido.calcular_custo_total()
        
        # Teste se o custo total está correto
        # Custo do tomate: (0.5 * 2) * 5.00 = 5.00
        # Custo do queijo: (0.2 * 2) * 20.00 = 8.00
        # Custo total: 5.00 + 8.00 = 13.00
        self.assertEqual(custo_total, Decimal('13.00'))

    def test_lucro_do_pedido(self):
        # Criando um Pedido
        pedido = Pedido.objects.create(
            cliente=self.cliente,
            empresa=self.empresa
        )

        # Criando um ItemPedido (2 pizzas)
        item_pedido = ItemPedido.objects.create(
            pedido=pedido,
            cardapio_item=self.cardapio_item,
            quantidade=2,
            preco_unitario=self.cardapio_item.preco
        )

        # Calculando o lucro do pedido
        custo_total = pedido.calcular_custo_total()
        pedido.calcular_total()
        lucro = pedido.total - custo_total
        
        # Teste se o lucro está correto
        self.assertEqual(lucro, Decimal('67.00'))  # Total (80.00) - Custo total (13.00)