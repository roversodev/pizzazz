from django.utils import timezone
from apps.appEmpresa.views import calcular_lucro
from apps.authentication.models import RelatorioFinanceiro, Empresa, Pedido
from django.db.models import Sum

def salvar_relatorio_financeiro():
    data_atual = timezone.now()
    empresas = Empresa.objects.all()  # Obter todas as empresas

    for empresa in empresas:
        pedidos_entregues = Pedido.objects.filter(empresa=empresa, status='entregue')  # Filtra pedidos da empresa

        # Vendas do mês atual
        vendas_mes_atual = pedidos_entregues.filter(
            data_pedido__year=data_atual.year,
            data_pedido__month=data_atual.month
        ).aggregate(total=Sum('total'))['total'] or 0

        # Mês anterior
        if data_atual.month == 1:
            mes_passado = 12  # Dezembro do ano passado
            ano_passado = data_atual.year - 1
        else:
            mes_passado = data_atual.month - 1  # Mês anterior
            ano_passado = data_atual.year

        # Vendas do mês passado
        vendas_mes_passado = pedidos_entregues.filter(
            data_pedido__year=ano_passado,
            data_pedido__month=mes_passado
        ).aggregate(total=Sum('total'))['total'] or 0

        # Calcular lucro do mês atual
        lucro_mes_atual = sum(calcular_lucro(pedido) for pedido in pedidos_entregues.filter(
            data_pedido__year=data_atual.year,
            data_pedido__month=data_atual.month
        ))

        # Calcular lucro do mês passado
        lucro_mes_passado = sum(calcular_lucro(pedido) for pedido in pedidos_entregues.filter(
            data_pedido__year=ano_passado,
            data_pedido__month=mes_passado
        ))

        # Calcular variação percentual do lucro
        if lucro_mes_passado > 0:
            variacao_percentual_lucro = ((lucro_mes_atual - lucro_mes_passado) / lucro_mes_passado) * 100
        else:
            variacao_percentual_lucro = 100 if lucro_mes_atual > 0 else 0

        # Salvar o relatório
        relatorio = RelatorioFinanceiro(
            empresa=empresa,
            ano=data_atual.year,
            mes=data_atual.month,
            vendas_mes_atual=vendas_mes_atual,
            lucro_mes_atual=lucro_mes_atual,
            vendas_mes_passado=vendas_mes_passado,
            lucro_mes_passado=lucro_mes_passado,
            variacao_percentual_lucro=variacao_percentual_lucro
        )
        relatorio.save()