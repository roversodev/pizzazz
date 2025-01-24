from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
import json, locale, re
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from apps.authentication.models import AvaliacaoPedido, Cardapio, Categoria, Cliente, CustomUser, Empresa, EmpresaUsuario, EnderecoCliente, EnderecoPedido, Estoque, HistoricoPedido, Ingrediente, IngredienteCardapio, ItemPedido, MovimentacaoEstoque, Pagamento, Pedido, AvaliacaoPedido, RelatorioFinanceiro, Sequencia 
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils.dateparse import parse_date
from django.contrib.sessions.models import Session
from django.db.models import Sum, Count, Avg, OuterRef, Subquery
from django.db.models.functions import ExtractWeekDay
from django.views.decorators.csrf import csrf_exempt
from notifications.signals import notify
from notifications.models import Notification
from django.utils import timezone
from apps.authentication.views import logout
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')

def aplicar_mascara_cnpj(cnpj):
    cnpj = re.sub(r'\D', '', cnpj)
    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:14]}"

def remover_mascara_cnpj(cnpj):
    return re.sub(r'\D', '', cnpj)

def remover_mascara_preço(preco):
    formatado = preco.replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    return formatado

def resumir_user_agent(user_agent):
    # Regex para identificar o sistema operacional
    os_patterns = [
        (r"Windows NT 10.0", "Windows 10"),
        (r"Windows NT 6.1", "Windows 7"),
        (r"Macintosh; Intel Mac OS X", "Mac OS X"),
        (r"Android", "Android"),
        (r"iPhone", "iOS"),
        (r"Linux", "Linux")
    ]
    
    # Regex para identificar o navegador
    browser_patterns = [
        (r"Chrome", "Chrome"),
        (r"Safari", "Safari"),
        (r"Firefox", "Firefox"),
        (r"Edge", "Edge"),
        (r"OPR", "Opera")
    ]
    
    # Procurando o sistema operacional
    os_info = "Desconhecido"
    for pattern, replacement in os_patterns:
        if re.search(pattern, user_agent):
            os_info = replacement
            break
    
    # Procurando o navegador
    browser_info = "Desconhecido"
    for pattern, replacement in browser_patterns:
        if re.search(pattern, user_agent):
            browser_info = replacement
            break
    
    # Resumo final no formato "Sistema Operacional - Navegador"
    return f"{os_info} - {browser_info}"

def criar_notificacao(usuario, mensagem):
    adm = CustomUser.objects.get(id=1)
    # Criando a notificação
    notify.send(
        actor=None,
        recipient=usuario,
        verb=mensagem,
        sender=adm,
    )

@login_required
def get_notifications(request, cnpj):
    # Obter notificações não lidas
    notifications = Notification.objects.filter(recipient=request.user, unread=True)

    # Formatar para retorno em JSON
    notifications_data = []
    for notification in notifications:
        # Garantir que o timestamp esteja no fuso horário local
        local_timestamp = timezone.localtime(notification.timestamp)

        # Formatando o timestamp no formato PT-BR
        formatted_timestamp = local_timestamp.strftime('%a, %d %b %Y %H:%M:%S')

        notifications_data.append({
            'message': notification.verb,
            'timestamp': formatted_timestamp,
            'id': notification.id
        })

    return JsonResponse({'notifications': notifications_data})

@login_required
def get_notifications_all(request, cnpj):
    # Obter notificações não lidas
    notifications = Notification.objects.filter(recipient=request.user)

    # Formatar para retorno em JSON
    notifications_data = []
    for notification in notifications:
        # Garantir que o timestamp esteja no fuso horário local
        local_timestamp = timezone.localtime(notification.timestamp)

        # Formatando o timestamp no formato PT-BR
        formatted_timestamp = local_timestamp.strftime('%d %b %Y %H:%M')

        notifications_data.append({
            'message': notification.verb,
            'timestamp': formatted_timestamp,
            'id': notification.id
        })

    return JsonResponse({'notifications': notifications_data})

@login_required
def mark_notification_as_read(request, notification_id, cnpj):
    try:
        notification = Notification.objects.get(id=notification_id, recipient=request.user)
        notification.mark_as_read()
        return JsonResponse({'status': 'success'})
    except Notification.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Notificação não encontrada'})

def calcular_lucro(pedido):
    custo_total = 0
    for item in pedido.itens.all():
        custo_total += item.cardapio_item.calcular_custo_producao() * item.quantidade
    lucro = pedido.total - custo_total
    return lucro

@login_required
def dashboard(request, cnpj):
    cnpj_com_mascara = aplicar_mascara_cnpj(cnpj)    
    empresa = Empresa.objects.get(cnpj=cnpj_com_mascara)

    if not request.user.is_adm:
        empUsu = EmpresaUsuario.objects.get(empresa=empresa, usuario=request.user)
        if empUsu.usuario != request.user:
            usu = EmpresaUsuario.objects.get(usuario=request.user)
            cnpj_usuario = remover_mascara_cnpj(usu.empresa.cnpj)
            return redirect('dashboard', cnpj=cnpj_usuario)

    data_atual = timezone.now()

    # Filtro de pedidos entregues
    pedidos_entregues = Pedido.objects.filter(empresa=empresa, historico__status='entregue')

    pedidos_total = pedidos_entregues.count()
    vendas_total = pedidos_entregues.aggregate(total=Sum('total'))['total'] or 0

    # Vendas do mês atual (mês e ano atuais)
    vendas_mes_atual = pedidos_entregues.filter(
        data_pedido__year=data_atual.year,
        data_pedido__month=data_atual.month
    ).aggregate(total=Sum('total'))['total'] or 0

    # Mês anterior: calculando o mês e o ano anteriores
    if data_atual.month == 1:
        mes_passado = 12  # Dezembro do ano passado
        ano_passado = data_atual.year - 1
    else:
        mes_passado = data_atual.month - 1  # Mês anterior
        ano_passado = data_atual.year

    # Vendas do mês passado (ano e mês anteriores)
    vendas_mes_passado = pedidos_entregues.filter(
        data_pedido__year=ano_passado,
        data_pedido__month=mes_passado
    ).aggregate(total=Sum('total'))['total'] or 0

    vendas_hoje = pedidos_entregues.filter(empresa=empresa, data_pedido__date=date.today()).aggregate(total=Sum('total'))['total'] or 0
    pedidos_hoje = pedidos_entregues.filter(empresa=empresa, data_pedido__date=date.today()).count()

    pedidos_ontem = pedidos_entregues.filter(
        empresa=empresa, 
        data_pedido__date=date.today() - timedelta(days=1)
    ).count()

    # Pegar clientes que fizeram seu primeiro pedido hoje
    clientes_novos = pedidos_entregues.filter(empresa=empresa, data_pedido__date=date.today()).values('cliente').distinct().count()
    clientes_atendidos = pedidos_entregues.values('cliente').distinct().count()

    # Pegar vendas de ontem
    vendas_ontem = pedidos_entregues.filter(
        empresa=empresa, 
        data_pedido__date=date.today() - timedelta(days=1)
    ).aggregate(total=Sum('total'))['total'] or 0

    clientes_ontem = pedidos_entregues.filter(
        empresa=empresa, 
        data_pedido__date=date.today() - timedelta(days=1)
    ).count()

    if pedidos_ontem > 0:
        variacao_percentual_pedidos = ((pedidos_hoje - pedidos_ontem) / pedidos_ontem) * 100
    else:
        variacao_percentual_pedidos = 100 if pedidos_hoje > 0 else 0

    # Calcular a variação percentual das vendas
    if vendas_ontem > 0:
        variacao_percentual = ((vendas_hoje - vendas_ontem) / vendas_ontem) * 100
    else:
        variacao_percentual = 100 if vendas_hoje > 0 else 0

    if clientes_ontem > 0:
        variacao_percentual_clientes = ((clientes_novos - clientes_ontem) / clientes_ontem) * 100
    else:
        variacao_percentual_clientes = 100 if clientes_novos > 0 else 0

    # Cálculo da variação percentual de vendas entre os meses
    if vendas_mes_passado > 0:
        variacao_percentual_vendas_mes = ((vendas_mes_atual - vendas_mes_passado) / vendas_mes_passado) * 100
    else:
        variacao_percentual_vendas_mes = 100 if vendas_mes_atual > 0 else 0

    # Cálculo das avaliações
    avaliacoes_positivas = AvaliacaoPedido.objects.filter(
        pedido__empresa=empresa, 
        nota__gte=4  # Considerando 4 e 5 como avaliações positivas
    ).count()
    
    avaliacoes_neutras = AvaliacaoPedido.objects.filter(
        pedido__empresa=empresa, 
        nota=3  # Considerando 3 como avaliação neutra
    ).count()
    
    avaliacoes_negativas = AvaliacaoPedido.objects.filter(
        pedido__empresa=empresa, 
        nota__lte=2  # Considerando 1 e 2 como avaliações negativas
    ).count()

    total_avaliacoes = avaliacoes_positivas + avaliacoes_neutras + avaliacoes_negativas

    if total_avaliacoes > 0:
        porcentagem_positivas = (avaliacoes_positivas / total_avaliacoes) * 100
        porcentagem_neutras = (avaliacoes_neutras / total_avaliacoes) * 100
        porcentagem_negativas = (avaliacoes_negativas / total_avaliacoes) * 100
    else:
        porcentagem_positivas = 0
        porcentagem_neutras = 0
        porcentagem_negativas = 0

    # Pedidos por dia da semana (entregues)
    pedidos_por_dia = pedidos_entregues.annotate(dia_semana=ExtractWeekDay('data_pedido')).values('dia_semana').annotate(total=Count('id')).order_by('dia_semana')
    
    dados_pedidos = [0] * 7
    for pedido in pedidos_por_dia:
        dados_pedidos[pedido['dia_semana'] - 1] = pedido['total']

    # Dados para o gráfico de vendas mensais
    vendas_mensais = empresa.get_vendas_mensais()
    meses = []
    valores = []
    
    for venda in vendas_mensais:
        meses.append(venda['mes'].strftime('%b'))
        valores.append(float(venda['total']))

    vendas_anual = pedidos_entregues.filter(empresa=empresa, data_pedido__year=date.today().year).aggregate(total=Sum('total'))['total'] or 0
    vendas_anual_anterior = pedidos_entregues.filter(empresa=empresa, data_pedido__year=date.today().year - 1).aggregate(total=Sum('total'))['total'] or 0

    if vendas_anual_anterior > 0:
        variacao_percentual_vendas = ((vendas_anual - vendas_anual_anterior) / vendas_anual_anterior) * 100
    else:
        variacao_percentual_vendas = 100 if vendas_anual > 0 else 0


    
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

    if lucro_mes_passado > 0:
        variacao_percentual_lucro = ((lucro_mes_atual - lucro_mes_passado) / lucro_mes_passado) * 100
    else:
        variacao_percentual_lucro = 100 if lucro_mes_atual > 0 else 0

    context = {
        'page_title': 'Dashboard',
        'empresa': empresa,
        'vendas_hoje': vendas_hoje,
        'variacao_percentual': variacao_percentual,
        'pedidos_hoje': pedidos_hoje,
        'variacao_percentual_pedidos': variacao_percentual_pedidos,
        'clientes_novos': clientes_novos,
        'variacao_percentual_clientes': variacao_percentual_clientes,
        'clientes_atendidos': clientes_atendidos,
        'pedidos_total': pedidos_total,
        'avaliacoes_positivas': round(porcentagem_positivas, 1),
        'avaliacoes_neutras': round(porcentagem_neutras, 1),
        'avaliacoes_negativas': round(porcentagem_negativas, 1),
        'pedidos_por_dia': dados_pedidos,
        'meses': json.dumps(meses),
        'vendas_mensais': json.dumps(valores),
        'estatisticas': empresa.get_estatisticas_gerais(),
        'variacao_percentual_vendas': variacao_percentual_vendas,
        'vendas_total': vendas_total,
        'variacao_percentual_vendas_mes': variacao_percentual_vendas_mes,
        'vendas_mes_atual': vendas_mes_atual,
        'lucro_mes_atual': lucro_mes_atual,
        'variacao_percentual_lucro': variacao_percentual_lucro,
    }
    return render(request, 'appEmpresa/dashboard.html', context)

@login_required
def avaliacoes(request, cnpj):
    cnpj_com_mascara = aplicar_mascara_cnpj(cnpj)    
    empresa = Empresa.objects.get(cnpj=cnpj_com_mascara)

    if not request.user.is_adm:
        empUsu = EmpresaUsuario.objects.get(empresa=empresa, usuario=request.user)
        if empUsu.usuario != request.user:
            usu = EmpresaUsuario.objects.get(usuario=request.user)
            cnpj_usuario = remover_mascara_cnpj(usu.empresa.cnpj)
            return redirect('dashboard', cnpj=cnpj_usuario)

    avaliacoes = AvaliacaoPedido.objects.filter(pedido__empresa=empresa)
    nota_media = avaliacoes.aggregate(Avg('nota'))['nota__avg'] or 0

    context = {
        'page_title': 'Dashboard',
        'empresa': empresa,
        'avaliacoes': avaliacoes,
        'nota_media': nota_media,
    }

    return render(request, 'appEmpresa/avaliacoes.html', context)


@login_required
def controle_usuarios(request, cnpj):
    cnpj_com_mascara = aplicar_mascara_cnpj(cnpj)    
    empresa = Empresa.objects.get(cnpj=cnpj_com_mascara)

    if not request.user.is_adm:
        empUsu = EmpresaUsuario.objects.get(empresa=empresa, usuario=request.user)
        if empUsu.usuario != request.user:
            usu = EmpresaUsuario.objects.get(usuario=request.user)
            cnpj_usuario = remover_mascara_cnpj(usu.empresa.cnpj)
            return redirect('dashboard', cnpj=cnpj_usuario)
        if not empUsu.papel == 'Dono':
            return redirect('perfil', cnpj=cnpj)
        
    usuarios = EmpresaUsuario.objects.filter(empresa=empresa)

    context = {
        'page_title': 'Controle de Usuários',
        'empresa': empresa,
        'usuarios': usuarios,
    }

    return render(request, 'appEmpresa/controle_usuarios.html', context)


@login_required
def excluir_user(request, cnpj, user_id):
    cnpj_com_mascara = aplicar_mascara_cnpj(cnpj)    
    empresa = Empresa.objects.get(cnpj=cnpj_com_mascara)

    if not request.user.is_adm:
        empUsu = EmpresaUsuario.objects.get(empresa=empresa, usuario=request.user)
        if empUsu.usuario != request.user:
            usu = EmpresaUsuario.objects.get(usuario=request.user)
            cnpj_usuario = remover_mascara_cnpj(usu.empresa.cnpj)
            return redirect('dashboard', cnpj=cnpj_usuario)
        if not empUsu.papel == 'Dono':
            return redirect('perfil', cnpj=cnpj)
    
    user_escolhido = CustomUser.objects.get(id=user_id)
    empresaUser = EmpresaUsuario.objects.get(usuario=user_escolhido)

    sessions = Session.objects.filter(expire_date__gte=timezone.now())
                
    for session in sessions:
        data = session.get_decoded()
        if data.get('_auth_user_id') == str(user_escolhido.id):
            session.delete()

    if not request.user.is_adm:
        if empresaUser.papel == 'Dono':
            messages.error(request, f'Não é possivel inativar um usuário com papel de {empresaUser.papel} do sistema, favor contatar o Administrador do sistema.')
            return redirect(controle_usuarios, cnpj=cnpj)

    empresaUser.ativo = not empresaUser.ativo
    empresaUser.save()

    messages.success(request, f'{user_escolhido.first_name} inativado com sucesso!')
    if empresaUser.ativo == True:
        messages.success(request, f'Agora o usuário {user_escolhido.first_name} poderá acessar novamente.')
    
    return redirect(controle_usuarios, cnpj=cnpj)



@login_required
def cadastrar_user(request, cnpj):
    cnpj_com_mascara = aplicar_mascara_cnpj(cnpj)    
    empresa = Empresa.objects.get(cnpj=cnpj_com_mascara)

    if not request.user.is_adm:
        empUsu = EmpresaUsuario.objects.get(empresa=empresa, usuario=request.user)
        if empUsu.usuario != request.user:
            usu = EmpresaUsuario.objects.get(usuario=request.user)
            cnpj_usuario = remover_mascara_cnpj(usu.empresa.cnpj)
            return redirect('dashboard', cnpj=cnpj_usuario)
        

    if request.method == 'POST':
        try:    
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            papel = request.POST.get('papel')
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')


            if CustomUser.objects.filter(email=email).exists():
                messages.error(request, "Erro ao cadastrar, e-mail já está em uso.")
                return redirect('controle_usuarios', cnpj=cnpj)

            if password != confirm_password:
                messages.error(request, "Erro ao cadastrar, senhas não coincidem.")
                return redirect('controle_usuarios', cnpj=cnpj)


            with transaction.atomic():
                # Criando o ingrediente
                custom_user = CustomUser(
                        first_name=first_name,
                        last_name=last_name,
                        email=email,
                        is_empresa=True,
                        username=email,
                        password=password,
                    )
                custom_user.set_password(password)
                custom_user.save()

                    # Criando o estoque com a quantidade inicial
                empresaUser = EmpresaUsuario(
                    usuario=custom_user,
                    empresa=empresa,
                    papel=papel
                )
                empresaUser.save()

            messages.success(request, f'{first_name} Cadastrado com Sucesso!')
            return redirect('controle_usuarios', cnpj=cnpj)
        except Exception as e:
            messages.error(request, "Erro ao cadastrar, verifique os dados e tente novamente.")
            return redirect('controle_usuarios', cnpj=cnpj)



#
# INGREDIENTES
#



@login_required
def ingredientes(request, cnpj):
    cnpj_com_mascara = aplicar_mascara_cnpj(cnpj)    
    empresa = Empresa.objects.get(cnpj=cnpj_com_mascara)

    if not request.user.is_adm:
        empUsu = EmpresaUsuario.objects.get(empresa=empresa, usuario=request.user)
        if empUsu.usuario != request.user:
            usu = EmpresaUsuario.objects.get(usuario=request.user)
            cnpj_usuario = remover_mascara_cnpj(usu.empresa.cnpj)
            return redirect('dashboard', cnpj=cnpj_usuario)

    # Recupera os ingredientes da empresa
    ingredientes = Ingrediente.objects.filter(empresa=empresa).order_by('-preco_unitario')

    context = {
        'empresa': empresa,
        'ingredientes': ingredientes,
        'page_title': 'Ingredientes',
    }

    return render(request, 'appEmpresa/ingredientes.html', context)



@login_required
def adicionar_ingredientes(request, cnpj):

    cnpj_com_mascara = aplicar_mascara_cnpj(cnpj)    
    empresa = Empresa.objects.get(cnpj=cnpj_com_mascara)

    if not request.user.is_adm:
        empUsu = EmpresaUsuario.objects.get(empresa=empresa, usuario=request.user)
        if empUsu.usuario != request.user:
            usu = EmpresaUsuario.objects.get(usuario=request.user)
            cnpj_usuario = remover_mascara_cnpj(usu.empresa.cnpj)
            return redirect('dashboard', cnpj=cnpj_usuario)

    if request.method == 'POST':
        try:
            nome = request.POST.get('nome')
            unidade = request.POST.get('unidade')
            preco_unitario_des = request.POST.get('preco_unitario')
            quantidade_inicial = float(request.POST.get('quantidade_inicial'))
            quantidade_baixo = float(request.POST.get('quantidade_baixo'))

            preco_unitario = remover_mascara_preço(preco_unitario_des)


            with transaction.atomic():
                # Criando o ingrediente
                ingrediente = Ingrediente(
                        nome=nome,
                        unidade=unidade,
                        preco_unitario=preco_unitario,
                        empresa=empresa,
                        quantidade_inicial=quantidade_inicial,
                        estoque_minimo= quantidade_baixo
                    )
                ingrediente.save()

                    # Criando o estoque com a quantidade inicial
                estoque = Estoque(
                    ingrediente=ingrediente,
                    quantidade_disponivel=quantidade_inicial,
                    empresa=empresa
                )
                estoque.save()

            messages.success(request, f'{nome} Cadastrado com Sucesso!')
            return redirect('ingredientes', cnpj=cnpj)
        except Exception as e:
            messages.error(request, "Erro ao cadastrar, verifique os dados e tente novamente.")
            return redirect('ingredientes', cnpj=cnpj)


    return redirect('ingredientes', cnpj=cnpj)



@login_required
def editar_ingrediente(request, cnpj, ingrediente_id):
    cnpj_com_mascara = aplicar_mascara_cnpj(cnpj)    
    empresa = Empresa.objects.get(cnpj=cnpj_com_mascara)

    if not request.user.is_adm:
        empUsu = EmpresaUsuario.objects.get(empresa=empresa, usuario=request.user)
        if empUsu.usuario != request.user:
            usu = EmpresaUsuario.objects.get(usuario=request.user)
            cnpj_usuario = remover_mascara_cnpj(usu.empresa.cnpj)
            return redirect('dashboard', cnpj=cnpj_usuario)

    ingrediente = get_object_or_404(Ingrediente, id_ingrediente=ingrediente_id, empresa=empresa)

    if request.method == 'POST':
        try:
            nome = request.POST.get('nome')
            unidade = request.POST.get('unidade')
            preco_unitario_des = request.POST.get(f'preco_unitario{ingrediente_id}')

            preco_unitario = remover_mascara_preço(preco_unitario_des)

            with transaction.atomic():

                ingrediente.nome = nome
                ingrediente.unidade = unidade
                ingrediente.preco_unitario = preco_unitario
                ingrediente.save()
            messages.success(request, 'Ingrediente editado com sucesso!')
            return redirect('ingredientes', cnpj=cnpj)
        except Exception as e:
            messages.error(request, "Erro ao editar, verifique os dados e tente novamente.")
            return redirect('ingredientes', cnpj=cnpj)

    context = {
        'empresa': empresa,
        'ingrediente': ingrediente
    }
    return render(request, 'appEmpresa/editar_ingrediente.html', context)



@login_required
def deletar_ingrediente(request, cnpj, ingrediente_id):
    cnpj_com_mascara = aplicar_mascara_cnpj(cnpj)    
    empresa = Empresa.objects.get(cnpj=cnpj_com_mascara)

    if not request.user.is_adm:
        empUsu = EmpresaUsuario.objects.get(empresa=empresa, usuario=request.user)
        if empUsu.usuario != request.user:
            usu = EmpresaUsuario.objects.get(usuario=request.user)
            cnpj_usuario = remover_mascara_cnpj(usu.empresa.cnpj)
            return redirect('dashboard', cnpj=cnpj_usuario)

    ingrediente = get_object_or_404(Ingrediente, id_ingrediente=ingrediente_id, empresa=empresa)

    if request.method == 'POST':
        ingrediente.delete()
        messages.success(request, 'Ingrediente excluido com sucesso!')
        return redirect('ingredientes', cnpj=cnpj)
    
    return redirect('ingredientes', cnpj=cnpj)



#
# ESTOQUE
#



@login_required
def estoque(request, cnpj):
    cnpj_com_mascara = aplicar_mascara_cnpj(cnpj)    
    empresa = Empresa.objects.get(cnpj=cnpj_com_mascara)

    if not request.user.is_adm:
        empUsu = EmpresaUsuario.objects.get(empresa=empresa, usuario=request.user)
        if empUsu.usuario != request.user:
            usu = EmpresaUsuario.objects.get(usuario=request.user)
            cnpj_usuario = remover_mascara_cnpj(usu.empresa.cnpj)
            return redirect('dashboard', cnpj=cnpj_usuario)
        
    estoque = Estoque.objects.filter(empresa=empresa)
    ingredientes = Ingrediente.objects.filter(empresa=empresa)

    context = {
        'page_title': 'Estoque',
        'empresa': empresa,
        'estoque': estoque,
        'ingredientes': ingredientes, 
    }
    return render(request, 'appEmpresa/estoque.html', context)


@login_required
def cadastrar_movimentacao(request, cnpj):
    cnpj_com_mascara = aplicar_mascara_cnpj(cnpj)    
    empresa = Empresa.objects.get(cnpj=cnpj_com_mascara)

    if not request.user.is_adm:
        empUsu = EmpresaUsuario.objects.get(empresa=empresa, usuario=request.user)
        if empUsu.usuario != request.user:
            usu = EmpresaUsuario.objects.get(usuario=request.user)
            cnpj_usuario = remover_mascara_cnpj(usu.empresa.cnpj)
            return redirect('dashboard', cnpj=cnpj_usuario)

    if request.method == 'POST':
        ingrediente_id = request.POST.get('ingrediente')
        tipo = request.POST.get('tipo')
        quantidade = Decimal(request.POST.get('quantidade_inicial'))
        observacao = request.POST.get('observacao', '')

        # Inicializa preco_unitario como None para saídas
        preco_unitario_decimal = None

        if tipo == 'entrada':
            preco_unitario = request.POST.get('preco_unitario', '0,00')  # Pega o preço unitário do formulário

            try:
                # Tenta remover qualquer formatação inválida do preço
                preco_unitario = remover_mascara_preço(preco_unitario)  # Certifique-se que essa função remova corretamente 'R$', ',' e outros caracteres

                # Tenta converter para Decimal
                preco_unitario_decimal = Decimal(preco_unitario)

            except InvalidOperation:
                messages.error(request, 'O preço unitário informado é inválido. Verifique o valor e tente novamente.')
                return redirect('estoque', cnpj=cnpj)

        try:
            ingrediente = Ingrediente.objects.get(id_ingrediente=ingrediente_id, empresa=empresa)
            estoque, created = Estoque.objects.get_or_create(empresa=empresa, ingrediente=ingrediente)

            with transaction.atomic():
                # Variável para armazenar o preço anterior do ingrediente antes da alteração
                preco_ingrediente_anterior = ingrediente.preco_unitario

                # Calcula o novo estoque e o preço do ingrediente
                if tipo == 'entrada':
                    # Atualiza o estoque com a nova quantidade
                    estoque.quantidade_disponivel += quantidade

                    # Se o ingrediente já possui estoque, recalcula o preço médio ponderado
                    if estoque.quantidade_disponivel > 0:
                        # Calculando o preço médio ponderado corretamente
                        preco_medio = ((estoque.quantidade_disponivel - quantidade) * ingrediente.preco_unitario + quantidade * preco_unitario_decimal) / estoque.quantidade_disponivel

                        # Atualiza o preço do ingrediente com o novo preço médio calculado
                        ingrediente.preco_unitario = preco_medio
                        ingrediente.save()

                        # Verifica se o preço do ingrediente foi alterado e envia uma notificação
                        if ingrediente.preco_unitario != preco_ingrediente_anterior:
                            criar_notificacao(request.user, f"O preço do ingrediente {ingrediente.nome} foi atualizado de R${preco_ingrediente_anterior:.2f} para R${ingrediente.preco_unitario:.2f}.")

                elif tipo == 'saida':
                    if quantidade > estoque.quantidade_disponivel:
                        messages.error(request, 'Quantidade insuficiente no estoque!')
                        return redirect('estoque', cnpj=cnpj)
                    estoque.quantidade_disponivel -= quantidade

                # Registra a movimentação de estoque
                MovimentacaoEstoque.objects.create(
                    empresa=empresa,
                    ingrediente=ingrediente,
                    tipo=tipo,
                    quantidade=quantidade,
                    preco_unitario=float(preco_unitario_decimal) if preco_unitario_decimal is not None else None,  # Apenas para entradas
                    observacao=observacao,
                    atendente=request.user,
                )

                # Salva as alterações no estoque
                estoque.save()

                messages.success(request, 'Movimentação registrada com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro no cadastro, verifique os dados e tente novamente. Erro: {str(e)}')

    return redirect('estoque', cnpj=cnpj)



def calcular_preco_medio(estoque, quantidade_nova, preco_unitario_novo):
    """
    Calcula o novo preço médio ponderado para o estoque.
    """
    total_atual = estoque.quantidade_disponivel * (estoque.preco_medio or 0)
    total_novo = quantidade_nova * preco_unitario_novo
    nova_quantidade = estoque.quantidade_disponivel + quantidade_nova

    return (total_atual + total_novo) / nova_quantidade if nova_quantidade > 0 else 0



#
# MOVIMENTAÇÕES
#


@login_required
def movimentacao_grafico(request, cnpj):
    # Filtra movimentações por empresa, ajusta de acordo com o contexto do sistema
    cnpj_com_mascara = aplicar_mascara_cnpj(cnpj)    
    empresa = Empresa.objects.get(cnpj=cnpj_com_mascara)
    movimentacoes = MovimentacaoEstoque.objects.filter(empresa=empresa)
    
    # Dados agregados por mês (exemplo: entradas e saídas)
    entradas = movimentacoes.filter(tipo='entrada').order_by('data')
    saidas = movimentacoes.filter(tipo='saida').order_by('data')

    # Dados formatados para o Chart.js
    data = {
        "entradas": [entrada.quantidade for entrada in entradas],
        "saidas": [saida.quantidade for saida in saidas],
        "labels": [entrada.data.strftime('%b %Y') for entrada in entradas],
    }
    return JsonResponse(data)


@login_required
def movimentacoes(request, cnpj):
    cnpj_com_mascara = aplicar_mascara_cnpj(cnpj)    
    empresa = Empresa.objects.get(cnpj=cnpj_com_mascara)

    if not request.user.is_adm:
        empUsu = EmpresaUsuario.objects.get(empresa=empresa, usuario=request.user)
        if empUsu.usuario != request.user:
            usu = EmpresaUsuario.objects.get(usuario=request.user)
            cnpj_usuario = remover_mascara_cnpj(usu.empresa.cnpj)
            return redirect('dashboard', cnpj=cnpj_usuario)
        
    
    movimentacoes = MovimentacaoEstoque.objects.filter(empresa=empresa)
        
    context = {
        'page_title': 'Movimentações',
        'empresa': empresa,
        'movimentacoes': movimentacoes,
    }
        
    return render(request, 'appEmpresa/movimentacoes.html', context)



#
# CARDÁPIO
#


# TO DO: ADICIONAR FUNÇÃO DE PESQUISA
@login_required
def cardapio(request, cnpj):
    cnpj_com_mascara = aplicar_mascara_cnpj(cnpj)    
    empresa = Empresa.objects.get(cnpj=cnpj_com_mascara)

    if not request.user.is_adm:
        empUsu = EmpresaUsuario.objects.get(empresa=empresa, usuario=request.user)
        if empUsu.usuario != request.user:
            usu = EmpresaUsuario.objects.get(usuario=request.user)
            cnpj_usuario = remover_mascara_cnpj(usu.empresa.cnpj)
            return redirect('dashboard', cnpj=cnpj_usuario)
        
    categorias = Categoria.objects.filter(empresa=empresa)
    cardapios = Cardapio.objects.filter(empresa=empresa)

    search = request.GET.get('search', '')
    if search:
        categorias = categorias.filter(nome__icontains=search)
        
    context = {
        'page_title': 'Cardápio',
        'empresa': empresa,
        'categorias': categorias,
        'cardapios': cardapios,
        'search': search,
    }
        
    return render(request, 'appEmpresa/cardapio.html', context)



@login_required
def adicionar_categoria(request, cnpj):

    cnpj_com_mascara = aplicar_mascara_cnpj(cnpj)    
    empresa = Empresa.objects.get(cnpj=cnpj_com_mascara)

    if request.method == 'POST':
        try:
            nome = request.POST.get('nome')
            ativo = True

            with transaction.atomic():
                # Criando a nova categoria
                categoria = Categoria.objects.create(
                    nome=nome,
                    ativo=ativo,
                    empresa=empresa
                )

                messages.success(request, f'Categoria {categoria.nome} criada com sucesso!')
                return redirect('cardapio', cnpj=cnpj)
        
        except Exception as e:
            messages.error(request, 'Erro ao cadastrar, verifique os dados e tente novamente.') 
            return redirect('cardapio', cnpj=cnpj)

    return render(request, 'cardapio/adicionar_categoria.html')



@login_required
def editar_categoria(request, cnpj, item_id):

    item = get_object_or_404(Categoria, id=item_id)

    if request.method == 'POST':
        try:
            nome = request.POST.get('nomeE')

            item.nome = nome
            item.save()

            messages.success(request, f'Categoria editada com sucesso! Novo nome: {nome}')
            return redirect('cardapio', cnpj=cnpj)


        except Exception as e:
            messages.error(request, 'Erro ao editar, verifique os dados e tente novamente.') 
            return redirect('cardapio', cnpj=cnpj)



@login_required
def deletar_categoria(request, cnpj, item_id):
    item = get_object_or_404(Categoria, id=item_id)

    item.delete()
    messages.success(request, f'Categoria {item.nome} deletada com sucesso!')
    return redirect('cardapio', cnpj=cnpj)



# Adicionar item do cardápio
@login_required
def adicionar_item(request, cnpj, categoria_id):
    categoria = get_object_or_404(Categoria, id=categoria_id)

    cnpj_com_mascara = aplicar_mascara_cnpj(cnpj)    
    empresa = Empresa.objects.get(cnpj=cnpj_com_mascara)

    if not request.user.is_adm:
        empUsu = EmpresaUsuario.objects.get(empresa=empresa, usuario=request.user)
        if empUsu.usuario != request.user:
            usu = EmpresaUsuario.objects.get(usuario=request.user)
            cnpj_usuario = remover_mascara_cnpj(usu.empresa.cnpj)
            return redirect('dashboard', cnpj=cnpj_usuario)

    if request.method == 'POST':
        
        try:
            nome = request.POST.get(f'nome{categoria.id}')
            descricao = request.POST.get(f'descricao{categoria.id}')
            preco = request.POST.get(f'preco_unitarioC{categoria.id}')
            preco = remover_mascara_preço(preco)
            imagem = request.FILES.get(f'imagem{categoria.id}')
            ativo = True
            borda_recheada = f'borda_recheada{categoria.id}' in request.POST

            with transaction.atomic():
                novo_item = Cardapio.objects.create(
                nome=nome,
                descricao=descricao,
                preco=preco,
                categoria=categoria,
                imagem=imagem,
                ativo=ativo,
                borda_recheada=borda_recheada,
                empresa=empresa
            )

                messages.success(request, f'Item {novo_item.nome} adicionado ao cardápio com sucesso!')
                return redirect('cardapio', cnpj=cnpj)
        
        except Exception as e:
            messages.error(request, 'Erro ao cadastrar, verifique os dados e tente novamente.') 
            return redirect('cardapio', cnpj=cnpj)
    


# Editar item do cardápio
@login_required
def editar_item(request, cnpj, item_id):
    item = get_object_or_404(Cardapio, id_cardapio=item_id)

    if request.method == 'POST':
        item.nome = request.POST.get(f'nome{item.categoria.id}')
        item.descricao = request.POST.get(f'descricao{item.categoria.id}')
        item.preco = remover_mascara_preço(request.POST.get(f'preco_unitario{item.categoria.id}'))
        imagem_nova = request.FILES.get(f'imagem{item.categoria.id}')
        if imagem_nova:
            item.imagem = imagem_nova
        item.borda_recheada = f'borda_recheada{item.categoria.id}' in request.POST
        
        item.save()
        
        messages.success(request, f'Item "{item.nome}" editado com sucesso!')
        return redirect('cardapio', cnpj=cnpj)

    context = {'item': item}
    return render(request, 'editar_item.html', context)



# Deletar item do cardápio
@login_required
def deletar_item(request, cnpj, item_id):
    item = get_object_or_404(Cardapio, id_cardapio=item_id)

    item.delete()
    messages.success(request, f'Item {item.nome} deletado com sucesso!')
    return redirect('cardapio', cnpj=cnpj)



@login_required
def toggle_ativo_item(request, cnpj, item_id):
    item = get_object_or_404(Cardapio, id_cardapio=item_id)
    item.ativo = not item.ativo
    item.save()

    return JsonResponse({'status': 'success', 'ativo': item.ativo})



@login_required
def toggle_ativo_categoria(request, cnpj, categoria_id):
    categoria = get_object_or_404(Categoria, id=categoria_id)
    categoria.ativo = not categoria.ativo
    categoria.save()

    return JsonResponse({'status': 'success', 'ativo': categoria.ativo})



#
# RECEITA PIZZA
#


@login_required
def receitas(request, cnpj):
    cnpj_com_mascara = aplicar_mascara_cnpj(cnpj)    
    empresa = Empresa.objects.get(cnpj=cnpj_com_mascara)

    if not request.user.is_adm:
        empUsu = EmpresaUsuario.objects.get(empresa=empresa, usuario=request.user)
        if empUsu.usuario != request.user:
            usu = EmpresaUsuario.objects.get(usuario=request.user)
            cnpj_usuario = remover_mascara_cnpj(usu.empresa.cnpj)
            return redirect('dashboard', cnpj=cnpj_usuario)

    # Obtenção dos ingredientes e cardápio da empresa
    receitas = IngredienteCardapio.objects.filter(empresa=empresa)
    ingredientes = Ingrediente.objects.filter(empresa=empresa)
    cardapio = Cardapio.objects.filter(empresa=empresa)
    
    # Se houver um termo de busca, filtramos as receitas
    search = request.GET.get('search', '')
    if search:
        cardapio = cardapio.filter(nome__icontains=search)

    # Criar um dicionário para armazenar a quantidade de ingredientes por item do cardápio
    quantidade_ingredientes = {}
    for item in cardapio:
        total_ingredientes = IngredienteCardapio.objects.filter(cardapio_item=item).count()
        quantidade_ingredientes[item.id_cardapio] = total_ingredientes

    context = {
        'page_title': 'Receitas',
        'empresa': empresa,
        'ingredientes': ingredientes,
        'cardapio': cardapio,
        'quantidade_ingredientes': quantidade_ingredientes,
        'receitas': receitas,
        'search': search,  # Passando o termo de busca para o template
    }

    return render(request, 'appEmpresa/receita.html', context)



@login_required
def cadastrar_receita(request, cnpj):
    cnpj_com_mascara = aplicar_mascara_cnpj(cnpj)    
    empresa = Empresa.objects.get(cnpj=cnpj_com_mascara)

    if not request.user.is_adm:
        empUsu = EmpresaUsuario.objects.get(empresa=empresa, usuario=request.user)
        if empUsu.usuario != request.user:
            usu = EmpresaUsuario.objects.get(usuario=request.user)
            cnpj_usuario = remover_mascara_cnpj(usu.empresa.cnpj)
            return redirect('dashboard', cnpj=cnpj_usuario)
        
    if request.method == 'POST':
        try:
            # Pega os dados do formulário
            cardapio_id = request.POST.get('cardapio')

            # Pega o item do cardápio
            cardapio_item = Cardapio.objects.get(id_cardapio=cardapio_id)
            
            # Atualiza a flag 'completo' do cardápio
            cardapio_item.completo = True
            cardapio_item.save()

            # Pega os ingredientes selecionados e suas quantidades
            ingredientes_selecionados = request.POST.getlist('ingredientes')  # Pega todos os ingredientes selecionados
            for ingrediente_id in ingredientes_selecionados:
                ingrediente = Ingrediente.objects.get(id_ingrediente=ingrediente_id)
                
                # Pega a quantidade específica para este ingrediente
                quantidade = request.POST.get(f'quantidade_{ingrediente_id}')
                
                # Cria a instância de IngredienteCardapio
                if quantidade:  # Verifica se a quantidade foi fornecida
                    ingrediente_cardapio = IngredienteCardapio(
                        cardapio_item=cardapio_item,
                        ingrediente=ingrediente,
                        quantidade=quantidade,
                        empresa=empresa  # Certifique-se de que a variável 'empresa' está definida no contexto
                    )
                    ingrediente_cardapio.save()  # Salva o relacionamento no banco

            messages.success(request, f'Receita {cardapio_item.nome} cadastrada com sucesso!')
            return redirect('receitas', cnpj=cnpj)
        
        except Exception as e:
            messages.error(request, f'Erro ao cadastrar a receita, verifique os dados e tente novamente. {e}')
            return redirect('receitas', cnpj=cnpj)
        


    if request.method == 'GET':
        cardapios = Cardapio.objects.filter(empresa=empresa)
        ingredientes = Ingrediente.objects.filter(empresa=empresa)
        context = {
        'page_title': 'Receitas',
        'empresa': empresa,
        'cardapios': cardapios,
        'ingredientes': ingredientes,
        }
        return render(request, 'appEmpresa/cadastrar_receita.html', context)



def verificar_completo(request, cnpj):
    cardapio_id = request.GET.get('cardapio_id')  # Pega o ID do cardápio selecionado via GET
    try:
        cardapio = Cardapio.objects.get(id_cardapio=cardapio_id)
        return JsonResponse({'completo': cardapio.completo})  # Retorna se o cardapio está completo
    except Cardapio.DoesNotExist:
        return JsonResponse({'completo': False})




def deletar_ingrediente_receita(request, cnpj, ingrediente_id):
    if request.method == 'POST':
        try:
            ingrediente = get_object_or_404(IngredienteCardapio, id_ingredientecardapio=ingrediente_id)
            ingrediente.delete()
            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Método não permitido'}, status=405)



#
# PEDIDOS
#

@login_required
def pedidos(request, cnpj):
    cnpj_com_mascara = aplicar_mascara_cnpj(cnpj)    
    empresa = Empresa.objects.get(cnpj=cnpj_com_mascara)

    if not request.user.is_adm:
        empUsu = EmpresaUsuario.objects.get(empresa=empresa, usuario=request.user)
        if empUsu.usuario != request.user:
            usu = EmpresaUsuario.objects.get(usuario=request.user)
            cnpj_usuario = remover_mascara_cnpj(usu.empresa.cnpj)
            return redirect('dashboard', cnpj=cnpj_usuario)
        
    pedidos = Pedido.objects.filter(empresa=empresa).order_by('-data_pedido')
    
    numero_pedido = request.GET.get('numero')
    status = request.GET.get('status')
    periodo = request.GET.get('periodo')

    if numero_pedido:
        pedidos = pedidos.filter(numero_pedido__icontains=numero_pedido)
    
    if status:
        # Subquery para pegar o último status de cada pedido
        last_status = HistoricoPedido.objects.filter(
            pedido=OuterRef('pk')  # Referencia ao pedido atual
        ).order_by('-data_alteracao')  # Ordena pela data de alteração (mais recente primeiro)
        
        # Pega o status da última alteração
        last_status = last_status.values('status')[:1]
        
        # Filtra os pedidos com o último status correspondente
        pedidos = pedidos.filter(
            historico__status=status,
            historico__status__in=Subquery(last_status)
        )
    
    if periodo:
        datas = periodo.split(' até ')
        if len(datas) == 2:
            data_inicio = datas[0].split('/')
            data_fim = datas[1].split('/')
            if len(data_inicio) == 3 and len(data_fim) == 3:
                data_inicio = f"{data_inicio[2]}-{data_inicio[1]}-{data_inicio[0]}"
                data_fim = f"{data_fim[2]}-{data_fim[1]}-{data_fim[0]}"
                pedidos = pedidos.filter(data_pedido__range=(data_inicio, data_fim))

    # Contexto
    context = {
        'page_title': 'Pedidos',
        'empresa': empresa,
        'pedidos': pedidos,
        'search': numero_pedido or '',
        'selected_status': status or '',
        'selected_periodo': periodo or '',
    }
    return render(request, 'appEmpresa/pedidos.html', context)



import openpyxl
@login_required
def exportar_pedidos(request, cnpj):

    cnpj_com_mascara = aplicar_mascara_cnpj(cnpj)    
    empresa = Empresa.objects.get(cnpj=cnpj_com_mascara)
    pedidos = Pedido.objects.filter(empresa=empresa)
    # Criação da planilha Excel
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Pedidos"

    # Cabeçalhos das colunas
    colunas = ['Data','Horário', 'Canal', 'Pedido', 'Situação', 'Total do Pedido']
    ws.append(colunas)

    # Preenchendo os dados dos pedidos
    for pedido in pedidos:
        historico = pedido.historico.order_by('-data_alteracao').first()  # Pega o mais recente
        status = historico.status if historico else 'Sem Status'  # Caso não tenha histórico, atribui 'Sem Status'
        row = [
            pedido.data_pedido.strftime('%d/%m/%Y'),
            pedido.data_pedido.strftime('%H:%M'),
            "Manual",
            pedido.numero_pedido,
            status,
            f"R$ {pedido.total:.2f}",
        ]
        ws.append(row)

    # Gerar o arquivo Excel
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename={empresa.nome_fantasia}-pedidos.xlsx'
    wb.save(response)
    return response




@login_required
def pedido_manual(request, cnpj):
    cnpj_com_mascara = aplicar_mascara_cnpj(cnpj)    
    empresa = Empresa.objects.get(cnpj=cnpj_com_mascara)

    if not request.user.is_adm:
        empUsu = EmpresaUsuario.objects.get(empresa=empresa, usuario=request.user)
        if empUsu.usuario != request.user:
            usu = EmpresaUsuario.objects.get(usuario=request.user)
            cnpj_usuario = remover_mascara_cnpj(usu.empresa.cnpj)
            return redirect('dashboard', cnpj=cnpj_usuario)
    
    if request.method == 'POST':
        try:
            # 1. Captura dos dados do cliente
            nome_cliente = request.POST.get('cliente')
            cliente = get_object_or_404(Cliente, id_cliente=nome_cliente)

            # 2. Captura dos dados de endereço
            cep = request.POST.get('txtCep')
            endereco = request.POST.get('endereco')
            numero = request.POST.get('numero')
            complemento = request.POST.get('complemento', '')
            bairro = request.POST.get('bairro')
            estado = request.POST.get('estado')
            municipio = request.POST.get('municipio')

            forma_pag = request.POST.get('forma_pagamento')
            pedido_itens_json = request.POST.get('pedidoItens')

            # Converte o JSON para uma lista de dicionários
            itens_pedido = json.loads(pedido_itens_json)
            
            # Variáveis para cálculo do total do pedido
            total_pedido = 0

            # 3. Verificar o estoque antes de criar o pedido
            for item in itens_pedido:
                cardapio_item = get_object_or_404(Cardapio, id_cardapio=item['id'], empresa=empresa)
                preco_unitario = item['preco']
                quantidade = item['quantidade']
                preco_total = preco_unitario * quantidade
                total_pedido += preco_total

                # Verificar o estoque do item antes de criar o pedido
                ingredientes = IngredienteCardapio.objects.filter(cardapio_item=cardapio_item)
                for ingrediente in ingredientes:
                    quantidade_usada = ingrediente.quantidade * quantidade
                    estoque_item = Estoque.objects.get(ingrediente=ingrediente.ingrediente, empresa=empresa)

                    # Verificar o estoque disponível
                    if estoque_item.quantidade_disponivel < quantidade_usada:
                        messages.error(request, f"Estoque insuficiente para o ingrediente {ingrediente.ingrediente.nome}. "
                                                f"Quantidade disponível: {estoque_item.quantidade_disponivel}, "
                                                f"quantidade necessária: {quantidade_usada}.")
                        return redirect('pedido_manual', cnpj=cnpj)

            # 4. Se o estoque for suficiente, criar o pedido
            with transaction.atomic():
                numero_pedido = Sequencia.obter_novo_valor()
                pedido = Pedido.objects.create(
                    cliente=cliente,
                    empresa=empresa,
                    numero_pedido=numero_pedido,
                    canal='Manual'
                )

                # Criando o endereço do pedido
                endereco_pedido = EnderecoPedido.objects.create(
                    cep=cep,
                    endereco=endereco,
                    numero=numero,
                    complemento=complemento,
                    bairro=bairro,
                    estado=estado,
                    municipio=municipio,
                    pedido=pedido
                )

                endereco_cliente = EnderecoCliente.objects.filter(cliente=cliente, principal=True).first()
                if not endereco_cliente:
                    endereco_cliente = EnderecoCliente.objects.create(
                        cliente=cliente,
                        cep=cep,
                        endereco=endereco,
                        numero=numero,
                        complemento=complemento,
                        bairro=bairro,
                        estado=estado,
                        municipio=municipio,
                        principal=True,
                        local='casa',
                    )

                # Criando o histórico do pedido
                historico = HistoricoPedido.objects.create(
                    status='confirmado',
                    observacao='Pedido criado',
                    alterado_por=request.user,
                    pedido=pedido
                )

                # Processando os itens do pedido
                for item in itens_pedido:
                    cardapio_item = get_object_or_404(Cardapio, id_cardapio=item['id'], empresa=empresa)
                    preco_unitario = item['preco']
                    quantidade = item['quantidade']
                    preco_total = preco_unitario * quantidade

                    # Criando o ItemPedido
                    ItemPedido.objects.create(
                        pedido=pedido,
                        cardapio_item=cardapio_item,
                        quantidade=quantidade,
                        preco_unitario=preco_unitario,
                        preco_total=preco_total
                    )

                pedido.calcular_total()

                # Criando o pagamento
                pag = Pagamento.objects.create(
                    pedido=pedido,
                    valor=pedido.total,
                    forma_pagamento=forma_pag,
                    status='aprovado'
                )

                # Atualizar o estoque
                pedido.atualizar_estoque(request)

                users_empresa = CustomUser.objects.filter(empresa_usuario__empresa=empresa)
                for usuario in users_empresa:
                    criar_notificacao(usuario, f'Novo pedido gerado! #{pedido.numero_pedido}')

                # 5. Redirecionar para o resumo ou página de sucesso
                messages.success(request, f"Pedido #{pedido.numero_pedido} criado com sucesso!")
                return redirect('pedidos', cnpj=cnpj)

        except Exception as e:
            # Caso haja um erro, mostrar mensagem de erro
            messages.error(request, f"Ocorreu um erro ao processar o pedido. Por favor, verifique os dados e tente novamente. {e}")
            return redirect('pedidos', cnpj=cnpj)

    cardapios = Cardapio.objects.filter(empresa=empresa, ativo=True, categoria__ativo=True)
    
    context = {
        'page_title': 'Pedidos',
        'empresa': empresa,
        'cardapios': cardapios,
    }

    return render(request, 'appEmpresa/pedido_manual.html', context)




def buscar_cliente(request, cnpj):
    cnpj_com_mascara = aplicar_mascara_cnpj(cnpj)    
    empresa = Empresa.objects.get(cnpj=cnpj_com_mascara)
    query = request.GET.get('q', '')
    if query:
        clientes = Cliente.objects.filter(nome__icontains=query) | Cliente.objects.filter(cpf__icontains=query)
        clientes_data = [{"id": cliente.id_cliente, "nome": cliente.nome, "telefone": cliente.telefone, "cpf": cliente.cpf} for cliente in clientes]
        return JsonResponse({"clientes": clientes_data})
    return JsonResponse({"clientes": []})



@login_required
def cadastro_cliente_manual(request, cnpj):
    if request.method == 'POST':
        cnpj_com_mascara = aplicar_mascara_cnpj(cnpj)    
        empresa = Empresa.objects.get(cnpj=cnpj_com_mascara)
        nome = request.POST.get('nome')
        cpf = request.POST.get('cpf')
        telefone = request.POST.get('telefone')
        dataN = request.POST.get('dataN')
        genero = request.POST.get('genero')

        dia, mes, ano = dataN.split('/')
        data_iso = f"{ano}-{mes}-{dia}"

        # Aqui você pode fazer as validações necessárias
        try:
            cliente = Cliente.objects.create(
                nome=nome,
                cpf=cpf,
                telefone=telefone,
                dataN=data_iso,
                genero=genero
            )
            cliente.empresas.add(empresa)
            cliente.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Método não permitido'}, status=405)



def buscar_endereco(request, cnpj, cliente_id):
    try:
        cliente = Cliente.objects.get(id_cliente=cliente_id)
        endereco = cliente.enderecos.filter(local='casa').first()
        return JsonResponse({
            'endereco': {
                'cep': endereco.cep,
                'logradouro': endereco.endereco,
                'numero': endereco.numero,
                'bairro': endereco.bairro,
                'estado': endereco.estado,
                'municipio': endereco.municipio,
                'complemento': endereco.complemento,
            }
        })
    except Exception as e:
        return JsonResponse({'error': 'Erro ao buscar o endereço'}, status=404)





@login_required
def detalhes_pedido(request, cnpj, pedido_id):
    cnpj_com_mascara = aplicar_mascara_cnpj(cnpj)    
    empresa = Empresa.objects.get(cnpj=cnpj_com_mascara)

    if not request.user.is_adm:
        empUsu = EmpresaUsuario.objects.get(empresa=empresa, usuario=request.user)
        if empUsu.usuario != request.user:
            usu = EmpresaUsuario.objects.get(usuario=request.user)
            cnpj_usuario = remover_mascara_cnpj(usu.empresa.cnpj)
            return redirect('dashboard', cnpj=cnpj_usuario)
        
    pedido = get_object_or_404(Pedido, numero_pedido=pedido_id, empresa=empresa)
    historico_pedido = pedido.historico.all()

    context = {
        'page_title': "Pedidos",
        'empresa': empresa,
        'pedido': pedido,
        'historico_pedido': historico_pedido,
    }

    return render(request, 'appEmpresa/detalhes_pedido.html', context)



@login_required
def alterar_status(request, cnpj, pedido_numero):
    if request.method == 'POST':
         try:
            pedido = Pedido.objects.get(numero_pedido=pedido_numero)
            status = request.POST.get('status')
            obs = request.POST.get('observacao')

            if status == '':
                messages.error(request, f'Ocorreu um erro ao tentar alterar o status do pedido #{pedido.numero_pedido}, verifique as informações e tente novamente.')
                return redirect(detalhes_pedido, cnpj=cnpj, pedido_id=pedido.numero_pedido)

            if not request.POST.get('observacao'):
                if status == 'pendente':
                    obs = 'Pedido criado'
                if status == 'confirmado':
                    obs = 'Pedido confirmado pela Pizzaria'
                if status == 'preparando':
                    obs = 'Pedido em preparação'
                if status == 'saiu_entrega':
                    obs = 'Pedido saiu para a entrega'
                if status == 'entregue':
                    obs = 'Pedido entregue'


            historico = HistoricoPedido.objects.create(
                 status=status,
                 observacao=obs,
                 pedido=pedido,
                 alterado_por=request.user,
             )

            messages.success(request, f'Status do pedido #{pedido.numero_pedido} alterado!')
            return redirect(detalhes_pedido, cnpj=cnpj, pedido_id=pedido.numero_pedido)
         except Exception as e:
             messages.error(request, f'Ocorreu um erro ao tentar alterar o status do pedido #{pedido.numero_pedido}, verifique as informações e tente novamente.')
             return redirect(detalhes_pedido, cnpj=cnpj, pedido_id=pedido.numero_pedido)






@login_required
def perfil(request, cnpj):
    cnpj_com_mascara = aplicar_mascara_cnpj(cnpj)    
    empresa = Empresa.objects.get(cnpj=cnpj_com_mascara)

    if not request.user.is_adm:
        empUsu = EmpresaUsuario.objects.get(empresa=empresa, usuario=request.user)
        if empUsu.usuario != request.user:
            usu = EmpresaUsuario.objects.get(usuario=request.user)
            cnpj_usuario = remover_mascara_cnpj(usu.empresa.cnpj)
            return redirect('dashboard', cnpj=cnpj_usuario)
        
    if request.user.is_adm or request.user.papel_adm:
        return redirect('perfil_admin')

    user = EmpresaUsuario.objects.get(usuario=request.user)

    sessoes = []

    # Obtendo todas as sessões ativas e inativas
    for session in Session.objects.all():
        data = session.get_decoded()  # Decodifica os dados da sessão
        if data.get('_auth_user_id') == str(request.user.id):  # Verifica se a sessão é do usuário logado
            dispositivo = data.get('device_info', 'Dispositivo desconhecido')
            dispositivo = resumir_user_agent(dispositivo)
            status = 'Ativa' if data.get('is_active', True) else 'Inativa'  # Verifica se está ativa
            localizacao = data.get('location', 'Desconhecido')
            device_id = data.get('device_id', 'Desconhecido')

            sessoes.append({
                'informacoes_dispositivo': dispositivo,
                'status': status,
                'localizacao': localizacao,
                'device_id': device_id,
            })

    if request.method == "POST" and 'old_password' in request.POST:
            form_senha = PasswordChangeForm(user, request.POST)
            if form_senha.is_valid():
                user = form_senha.save()
                update_session_auth_hash(request, user)  # Mantém o usuário logado após a mudança de senha
                messages.success(request, 'Sua senha foi atualizada com sucesso!')
                return redirect('perfil_admin')  # Redireciona para a mesma página para evitar reenvio do formulário
            else:
                messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
            form_senha = PasswordChangeForm(user)

    # Se o botão de deslogar for pressionado
    if request.method == 'POST' and 'deslogar_todas_sessoes' in request.POST:
        for session in Session.objects.all():
            data = session.get_decoded()
            if data.get('_auth_user_id') == str(request.user.id):
                session.delete()  # Deleta a sessão
        logout(request)  # Desloga o usuário da sessão atual
        return redirect('perfil', cnpj=cnpj)  # Redireciona para a página de login, ou onde desejar
    
    context = {
        'page_title': 'Perfil',
        'empresa': empresa,
        'user': user,
        'sessoes': sessoes,
        'form_senha': form_senha,
    }

    return render(request, 'appEmpresa/perfil.html', context)



@csrf_exempt
@login_required
def editar_imagem_perfil(request, cnpj,user_id):
    if request.method == "POST" and request.FILES.get('profile_image'):
        user = CustomUser.objects.get(id=user_id)
        user.profile_image = request.FILES['profile_image']
        user.save()
        return JsonResponse({'new_image_url': user.profile_image.url})
    return JsonResponse({'error': 'Invalid request'}, status=400)





@login_required
def perfil_empresa(request, cnpj):
    cnpj_com_mascara = aplicar_mascara_cnpj(cnpj)    
    empresa = Empresa.objects.get(cnpj=cnpj_com_mascara)

    if not request.user.is_adm:
        empUsu = EmpresaUsuario.objects.get(empresa=empresa, usuario=request.user)
        if empUsu.usuario != request.user:
            usu = EmpresaUsuario.objects.get(usuario=request.user)
            cnpj_usuario = remover_mascara_cnpj(usu.empresa.cnpj)
            return redirect('dashboard', cnpj=cnpj_usuario)
        if not empUsu.papel == 'Dono':
            return redirect('perfil', cnpj=cnpj)

    if request.method == 'POST':
        if 'logo' in request.FILES:
            empresa.logo = request.FILES['logo']
        if 'perfil' in request.FILES:
            empresa.perfil_empresa = request.FILES['perfil']
        if 'banner' in request.FILES:
            empresa.banner = request.FILES['banner']
        if 'tempo_entrega' in request.POST:
            tempo_entrega = request.POST['tempo_entrega'].split('-')
            empresa.tempo_entrega_min = int(tempo_entrega[0].strip())
            empresa.tempo_entrega_max = int(tempo_entrega[1].strip())
            empresa.preco_frete = remover_mascara_preço(request.POST['preco_frete'])
            empresa.pedido_minimo = remover_mascara_preço(request.POST['pedido_minimo'])

        empresa.save()
        messages.success(request, "Informações atualizadas com sucesso!")
        return redirect('perfil_empresa', cnpj=cnpj)


    context = {
        'page_title': 'Perfil Empresa',
        'empresa': empresa,
    }

    return render(request, 'appEmpresa/perfil_empresa.html', context)


@login_required
def pizzaiolo(request, cnpj):
    cnpj_com_mascara = aplicar_mascara_cnpj(cnpj)    
    empresa = Empresa.objects.get(cnpj=cnpj_com_mascara)

    if not request.user.is_adm:
        empUsu = EmpresaUsuario.objects.get(empresa=empresa, usuario=request.user)
        if empUsu.usuario != request.user:
            usu = EmpresaUsuario.objects.get(usuario=request.user)
            cnpj_usuario = remover_mascara_cnpj(usu.empresa.cnpj)
            return redirect('dashboard', cnpj=cnpj_usuario)
        
    
    context = {
        'page_title': "Pizzaiolo",
        'empresa': empresa,
    }

    return render(request, 'appEmpresa/pizzaiolo.html', context)


@csrf_exempt
@login_required
def listar_pedidos(request, cnpj):
    cnpj_com_mascara = aplicar_mascara_cnpj(cnpj)    
    empresa = Empresa.objects.get(cnpj=cnpj_com_mascara)
    pedidos = Pedido.objects.filter(empresa=empresa)
    pedidos_data = []

    for pedido in pedidos:
        status_atual = pedido.historico.latest('data_alteracao').status if pedido.historico.exists() else 'pendente'
        pedidos_data.append({
            'id': pedido.id,
            'cliente': pedido.cliente.nome,
            'empresa': pedido.empresa.nome_fantasia,
            'total': pedido.total,
            'numero_pedido': pedido.numero_pedido,
            'status': status_atual,
            'itens': [
                f"{item.quantidade}x {item.cardapio_item.nome}" for item in pedido.itens.all()
            ]
        })

    return JsonResponse(pedidos_data, safe=False)


@csrf_exempt
@login_required
def atualizar_status_pedido(request, cnpj, pedido_id):
    if request.method == 'POST':
        pedido = Pedido.objects.get(id=pedido_id)
        data = json.loads(request.body)
        novo_status = data.get('status')
        usuario = request.user if request.user.is_authenticated else None

        if novo_status == 'preparando':
                    obs = 'Pedido em preparação'
        if novo_status == 'saiu_entrega':
                    obs = 'Pedido saiu para a entrega'
        if novo_status == 'entregue':
                    obs = 'Pedido entregue'

        # Atualizar o histórico
        HistoricoPedido.objects.create(
            pedido=pedido,
            status=novo_status,
            observacao=obs,
            alterado_por=usuario
        )

        return JsonResponse({'id': pedido.id, 'status': novo_status}, status=200)

    return JsonResponse({'error': 'Método não permitido'}, status=405)

@login_required
def receita_pedido(request, cnpj,pedido_id):
    pedido = Pedido.objects.get(id=pedido_id)
    itens_receita = []

    for item in pedido.itens.all():
        ingredientes = IngredienteCardapio.objects.filter(cardapio_item=item.cardapio_item)
        itens_receita.append({
            'nome': item.cardapio_item.nome,
            'ingredientes': [
                {
                    'nome': ing.ingrediente.nome,
                    'quantidade': ing.quantidade,
                    'unidade': ing.ingrediente.unidade
                } for ing in ingredientes
            ]
        })

    return JsonResponse(itens_receita, safe=False)



def relatorio_financeiro(request, cnpj):
    cnpj_com_mascara = aplicar_mascara_cnpj(cnpj)    
    empresa = Empresa.objects.get(cnpj=cnpj_com_mascara)

    if not request.user.is_adm:
        empUsu = EmpresaUsuario.objects.get(empresa=empresa, usuario=request.user)
        if empUsu.usuario != request.user:
            usu = EmpresaUsuario.objects.get(usuario=request.user)
            cnpj_usuario = remover_mascara_cnpj(usu.empresa.cnpj)
            return redirect('dashboard', cnpj=cnpj_usuario)
        

    rf = RelatorioFinanceiro.objects.filter(empresa=empresa)

        
    context = {
        'page_title': 'Relatório Financeiro',
        'empresa': empresa,
        'rf': rf,
    }

    return render(request, 'appEmpresa/relatorio_financeiro.html', context)