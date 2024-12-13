from decimal import Decimal
import locale
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from apps.authentication.models import Cardapio, Categoria, Empresa, EmpresaUsuario, Estoque, Ingrediente, MovimentacaoEstoque
import re
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction

locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')

def aplicar_mascara_cnpj(cnpj):
    cnpj = re.sub(r'\D', '', cnpj)
    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:14]}"

def remover_mascara_cnpj(cnpj):
    return re.sub(r'\D', '', cnpj)

def remover_mascara_preço(preco):
    formatado = preco.replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    return formatado

@login_required
def dashboard(request, cnpj):
    cnpj_com_mascara = aplicar_mascara_cnpj(cnpj)    
    empresa = Empresa.objects.get(cnpj=cnpj_com_mascara)
    empUsu = EmpresaUsuario.objects.get(empresa=empresa)

    if not request.user.is_superuser:
        if empUsu.usuario != request.user:
            usu = EmpresaUsuario.objects.get(usuario=request.user)
            cnpj_usuario = remover_mascara_cnpj(usu.empresa.cnpj)
            return redirect('dashboard', cnpj=cnpj_usuario)

    context = {
        'page_title': 'Dashboard',
        'empresa': empresa
    }
    return render(request, 'appEmpresa/dashboard.html', context)



#
# INGREDIENTES
#



@login_required
def ingredientes(request, cnpj):
    cnpj_com_mascara = aplicar_mascara_cnpj(cnpj)    
    empresa = Empresa.objects.get(cnpj=cnpj_com_mascara)
    empUsu = EmpresaUsuario.objects.get(empresa=empresa)

    if not request.user.is_superuser:
        if empUsu.usuario != request.user:
            usu = EmpresaUsuario.objects.get(usuario=request.user)
            cnpj_usuario = remover_mascara_cnpj(usu.empresa.cnpj)
            return redirect('dashboard', cnpj=cnpj_usuario)

    # Recupera os ingredientes da empresa
    ingredientes = Ingrediente.objects.filter(empresa=empresa).order_by('-preco_unitario')

    context = {
        'empresa': empresa,
        'ingredientes': ingredientes,
        'page_title': 'Ingredientes'
    }

    return render(request, 'appEmpresa/ingredientes.html', context)



@login_required
def adicionar_ingredientes(request, cnpj):

    cnpj_com_mascara = aplicar_mascara_cnpj(cnpj)    
    empresa = Empresa.objects.get(cnpj=cnpj_com_mascara)
    empUsu = EmpresaUsuario.objects.get(empresa=empresa)

    if not request.user.is_superuser:
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
    empUsu = EmpresaUsuario.objects.get(empresa=empresa)

    if not request.user.is_superuser:
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
    empUsu = EmpresaUsuario.objects.get(empresa=empresa)

    if not request.user.is_superuser:
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
    empUsu = EmpresaUsuario.objects.get(empresa=empresa)

    if not request.user.is_superuser:
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



def cadastrar_movimentacao(request, cnpj):
    cnpj_com_mascara = aplicar_mascara_cnpj(cnpj)    
    empresa = Empresa.objects.get(cnpj=cnpj_com_mascara)
    empUsu = EmpresaUsuario.objects.get(empresa=empresa)

    if not request.user.is_superuser:
        if empUsu.usuario != request.user:
            usu = EmpresaUsuario.objects.get(usuario=request.user)
            cnpj_usuario = remover_mascara_cnpj(usu.empresa.cnpj)
            return redirect('dashboard', cnpj=cnpj_usuario)

    if request.method == 'POST':
        ingrediente_id = request.POST.get('ingrediente')
        tipo = request.POST.get('tipo')
        quantidade = Decimal(request.POST.get('quantidade_inicial'))
        preco_unitario = request.POST.get('preco_unitario')
        observacao = request.POST.get('observacao', '')
        preco_unitario = remover_mascara_preço(preco_unitario)

        try:
            ingrediente = Ingrediente.objects.get(id_ingrediente=ingrediente_id, empresa=empresa)
            estoque, created = Estoque.objects.get_or_create(empresa=empresa, ingrediente=ingrediente)

            with transaction.atomic():

                # Calcula o novo estoque
                if tipo == 'entrada':
                    estoque.quantidade_disponivel += quantidade
                    # Registra o preço unitário se fornecido
                    #if preco_unitario:
                        #estoque.preco_medio = calcular_preco_medio(estoque, quantidade, float(preco_unitario))
                elif tipo == 'saida':
                    if quantidade > estoque.quantidade_disponivel:
                        messages.error(request, 'Quantidade insuficiente no estoque!')
                        return redirect('estoque_view')
                    estoque.quantidade_disponivel -= quantidade

                # Salva a movimentação
                MovimentacaoEstoque.objects.create(
                    empresa=empresa,
                    ingrediente=ingrediente,
                    tipo=tipo,
                    quantidade=quantidade,
                    preco_unitario=float(preco_unitario) if preco_unitario else None,
                    observacao=observacao,
                    atendente=request.user,
                )

                # Salva as alterações no estoque
                estoque.save()
                messages.success(request, 'Movimentação registrada com sucesso!')

        except Exception as e:
            messages.error(request, 'Erro no cadastro, verifique os dados e tente novamente.')

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



def movimentacoes(request, cnpj):
    cnpj_com_mascara = aplicar_mascara_cnpj(cnpj)    
    empresa = Empresa.objects.get(cnpj=cnpj_com_mascara)
    empUsu = EmpresaUsuario.objects.get(empresa=empresa)

    if not request.user.is_superuser:
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
# MOVIMENTAÇÕES
#



def cardapio(request, cnpj):
    cnpj_com_mascara = aplicar_mascara_cnpj(cnpj)    
    empresa = Empresa.objects.get(cnpj=cnpj_com_mascara)
    empUsu = EmpresaUsuario.objects.get(empresa=empresa)

    if not request.user.is_superuser:
        if empUsu.usuario != request.user:
            usu = EmpresaUsuario.objects.get(usuario=request.user)
            cnpj_usuario = remover_mascara_cnpj(usu.empresa.cnpj)
            return redirect('dashboard', cnpj=cnpj_usuario)
        
    categorias = Categoria.objects.filter(empresa=empresa)
    cardapios = Cardapio.objects.filter(empresa=empresa)
        
    context = {
        'page_title': 'Cardápio',
        'empresa': empresa,
        'categorias': categorias,
        'cardapios': cardapios,
    }
        
    return render(request, 'appEmpresa/cardapio.html', context)



def adicionar_categoria(request, cnpj):

    cnpj_com_mascara = aplicar_mascara_cnpj(cnpj)    
    empresa = Empresa.objects.get(cnpj=cnpj_com_mascara)
    empUsu = EmpresaUsuario.objects.get(empresa=empresa)

    if not request.user.is_superuser:
        if empUsu.usuario != request.user:
            usu = EmpresaUsuario.objects.get(usuario=request.user)
            cnpj_usuario = remover_mascara_cnpj(usu.empresa.cnpj)
            return redirect('dashboard', cnpj=cnpj_usuario)


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

                messages.success(request, f'Categoria "{categoria.nome}" criada com sucesso!')
                return redirect('cardapio', cnpj=cnpj)
        
        except Exception as e:
            messages.error(request, 'Erro ao cadastrar, verifique os dados e tente novamente.') 
            return redirect('cardapio', cnpj=cnpj)

    return render(request, 'cardapio/adicionar_categoria.html')



def deletar_categoria(request, cnpj, item_id):
    item = get_object_or_404(Categoria, id=item_id)

    item.delete()
    messages.success(request, f'Categoria "{item.nome}" deletada com sucesso!')
    return redirect('cardapio', cnpj=cnpj)


# Adicionar item do cardápio
def adicionar_item(request, cnpj, categoria_id):
    categoria = get_object_or_404(Categoria, id=categoria_id)

    cnpj_com_mascara = aplicar_mascara_cnpj(cnpj)    
    empresa = Empresa.objects.get(cnpj=cnpj_com_mascara)
    empUsu = EmpresaUsuario.objects.get(empresa=empresa)

    if not request.user.is_superuser:
        if empUsu.usuario != request.user:
            usu = EmpresaUsuario.objects.get(usuario=request.user)
            cnpj_usuario = remover_mascara_cnpj(usu.empresa.cnpj)
            return redirect('dashboard', cnpj=cnpj_usuario)

    if request.method == 'POST':
        
        try:
            nome = request.POST.get(f'nome{categoria.id}')
            descricao = request.POST.get(f'descricao{categoria.id}')
            preco = request.POST.get(f'preco_unitario{categoria.id}')
            preco = remover_mascara_preço(preco)
            imagem = request.FILES.get(f'imagem{categoria.id}')
            ativo = True  # O item estará sempre ativo (por enquanto)
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

                messages.success(request, f'Item "{novo_item.nome}" adicionado ao cardápio com sucesso!')
                return redirect('cardapio', cnpj=cnpj)
        
        except Exception as e:
            messages.error(request, 'Erro ao cadastrar, verifique os dados e tente novamente.') 
            return redirect('cardapio', cnpj=cnpj)
    


# Editar item do cardápio
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
def deletar_item(request, cnpj, item_id):
    item = get_object_or_404(Cardapio, id_cardapio=item_id)

    item.delete()
    messages.success(request, f'Item "{item.nome}" deletado com sucesso!')
    return redirect('cardapio', cnpj=cnpj)


def toggle_ativo_item(request, cnpj, item_id):
    item = get_object_or_404(Cardapio, id_cardapio=item_id)
    item.ativo = not item.ativo
    item.save()

    return JsonResponse({'status': 'success', 'ativo': item.ativo})
