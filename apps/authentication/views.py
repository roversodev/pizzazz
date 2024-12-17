import datetime
import locale
from django.shortcuts import redirect, render
from django.contrib.auth import get_user_model
from django.contrib import messages
from .models import Empresa, EmpresaUsuario, EnderecoEmpresa, CustomUser, Ingrediente, IngredienteCardapio, Cardapio, Estoque, Pedido, ItemPedido, Cliente, EnderecoCliente
from django.db import transaction
from django.contrib.auth import logout as auth_logout, authenticate, login as auth_login
import re

locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')


def remover_mascara_cnpj(cnpj):
    return re.sub(r'\D', '', cnpj)

def remover_mascara_preço(preco):
    formatado = preco.replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    return formatado



def login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, username=email, password=password)
        if user is not None:
            auth_login(request, user)


            if user.is_empresa:
                emp = EmpresaUsuario.objects.get(usuario=user.id)
                cnpj = remover_mascara_cnpj(emp.empresa.cnpj)
                return redirect('dashboard', cnpj=cnpj)
            return redirect('cliente')
        else:
            messages.error(request, "E-mail ou senha inválidos")
            return redirect('login')
        
    

    return render(request, 'auth/login.html')



def logout(request):
    auth_logout(request)
    messages.success(request, 'Deslogado com sucesso.')
    return redirect('login')



def cadastrar_parceiros(request):
    if request.method == 'POST':
        try:
            # Capturando os dados do formulário
            cnpj = request.POST.get('cnpj')
            razao = request.POST.get('razao')
            nome_fantasia = request.POST.get('fantasia')
            telefone = request.POST.get('telefone')
            data_abertura = request.POST.get('dataA')
            email = request.POST.get('email')
            password = request.POST.get('password')

            with transaction.atomic():
                user = CustomUser.objects.create_user(
                    email=email,
                    password=password,
                    is_empresa=True,
                    username=email
                )
                user.save()

                # Criando a empresa
                empresa = Empresa.objects.create(
                    nome_fantasia=nome_fantasia,
                    cnpj=cnpj,
                    razao=razao,
                    telefone=telefone,
                    data_abertura=data_abertura,
                    subdominio=f"{nome_fantasia.lower().replace(' ', '-')}"
                )


                EmpresaUsuario.objects.create(
                    empresa=empresa,
                    usuario=user,
                    papel='Dono'
                )

            messages.success(request, "Complete o cadastro na próxima etapa.")
            return redirect('cadastrar_parceiros_etapa2', empresa_id=empresa.id_empresa)

        except Exception as e:
            messages.error(request, f"Erro ao cadastrar empresa: {e}")
            return redirect('cadastrar_parceiros')

    return render(request, 'auth/cadastrar-parceiros.html')


#TO DO: Colocar login required e apenas acessar o dono do login em questão
def cadastrar_parceiros_etapa2(request, empresa_id):
    empresa = Empresa.objects.get(id_empresa=empresa_id)

    if request.method == 'POST':
        try:
            # Capturando os dados de endereço
            cep = request.POST.get('txtCep')
            endereco = request.POST.get('endereco')
            numero = request.POST.get('numero')
            complemento = request.POST.get('complemento')
            bairro = request.POST.get('bairro')
            estado = request.POST.get('estado')
            municipio = request.POST.get('municipio')

            # Criando o endereço da empresa
            endereco_empresa = EnderecoEmpresa.objects.create(
                empresa=empresa,
                cep=cep,
                endereco=endereco,
                numero=numero,
                complemento=complemento,
                bairro=bairro,
                estado=estado,
                municipio=municipio
            )

            messages.success(request, "Endereço cadastrado com sucesso!")
            return redirect('cadastrar_parceiros_etapa3', empresa_id=empresa_id)

        except Exception as e:
            messages.error(request, f"Erro ao cadastrar endereço: {e}")
            return redirect('cadastrar_parceiros_etapa2', empresa_id=empresa_id)

    return render(request, 'auth/cadastrar-parceiros-2.html', {'empresa': empresa})



def cadastrar_parceiros_etapa3(request, empresa_id):

    empresa = Empresa.objects.get(id_empresa=empresa_id)

    if request.method == 'POST':

        tempo_entrega_min = request.POST.get('tempMin')
        tempo_entrega_max = request.POST.get('tempMax')
        preco_frete = request.POST.get('frete')
        pedido_minimo = request.POST.get('pedido_minimo')

        if preco_frete:
            preco_frete = remover_mascara_preço(preco_frete)

        if pedido_minimo:
            pedido_minimo = remover_mascara_preço(pedido_minimo)

        logo = request.FILES.get('logo')
        perfil = request.FILES.get('perfil')
        banner = request.FILES.get('banner')

        # Validando os campos
        errors = []

        # Validação de campos numéricos
        try:
            tempo_entrega_min = int(tempo_entrega_min) if tempo_entrega_min else None
            tempo_entrega_max = int(tempo_entrega_max) if tempo_entrega_max else None
            preco_frete = float(preco_frete) if preco_frete else None
            pedido_minimo = float(pedido_minimo) if pedido_minimo else None
        except ValueError:
            errors.append("Valores numéricos inválidos.")

        if errors:
            # Se houver erros, exibe as mensagens e retorna o formulário
            for error in errors:
                messages.error(request, error)
            return render(request, 'auth/cadastrar-parceiros-3.html')

        # Criando a empresa no banco de dados
        try:
            empresa.tempo_entrega_min = tempo_entrega_min
            empresa.tempo_entrega_max = tempo_entrega_max
            empresa.preco_frete = preco_frete
            empresa.pedido_minimo = pedido_minimo
            empresa.logo = logo
            empresa.banner = banner
            empresa.perfil_empresa = perfil
            empresa.save()

            messages.success(request, "Empresa cadastrada com sucesso!")
            return redirect('login')
        except Exception as e:
            messages.error(request, f"Erro ao cadastrar a empresa: {e}")

    return render(request, 'auth/cadastrar-parceiros-3.html')



def cadastrar_clientes(request):
    if request.method == 'POST':
        try:
            # Capturando os dados do formulário
            nome = request.POST.get('nomeC')
            cpf = request.POST.get('cpf')
            telefone = request.POST.get('telefone')
            data_nascimento = request.POST.get('dataN')
            genero = request.POST.get('genero')
            email = request.POST.get('email')
            password = request.POST.get('password')

            dia, mes, ano = data_nascimento.split('/')

            nomes = nome.split()
            primeiro_nome = nomes[0]
            ultimo_nome = nomes[-1]

            # Formatar no formato ISO
            data_iso = f"{ano}-{mes}-{dia}"
            print(data_iso)

            with transaction.atomic():
                user = CustomUser.objects.create_user(
                    email=email,
                    password=password,
                    is_cliente=True,
                    username=email,
                    first_name=primeiro_nome,
                    last_name=ultimo_nome
                )
                user.save()

                # Criando a empresa
                cliente = Cliente.objects.create(
                    nome=nome,
                    cpf=cpf,
                    telefone=telefone,
                    dataN=data_iso,
                    genero=genero,
                    usuario=user,
                )

            messages.success(request, "Complete o cadastro na próxima etapa.")
            return redirect('cadastrar_clientes_etapa2', cliente_id=cliente.id_cliente)

        except Exception as e:
            messages.error(request, "Erro ao cadastrar, verifique os dados e tente novamente.")
            return redirect('cadastrar_clientes')
    return render(request, 'auth/cadastrar-clientes.html')


#TO DO: Colocar login required e apenas acessar o dono do login em questão
def cadastrar_clientes_etapa2(request, cliente_id):
    cliente = Cliente.objects.get(id_cliente=cliente_id)

    if request.method == 'POST':
        try:
            # Capturando os dados de endereço
            cep = request.POST.get('txtCep')
            endereco = request.POST.get('endereco')
            numero = request.POST.get('numero')
            complemento = request.POST.get('complemento')
            bairro = request.POST.get('bairro')
            estado = request.POST.get('estado')
            municipio = request.POST.get('municipio')

            local = request.POST.get('local')

            # Criando o endereço do cliente
            EnderecoCliente.objects.create(
                cliente=cliente,
                local=local,
                cep=cep,
                endereco=endereco,
                numero=numero,
                complemento=complemento,
                bairro=bairro,
                estado=estado,
                municipio=municipio
            )

            messages.success(request, "Cadastro feito por completo!")
            return redirect('login')

        except Exception as e:
            messages.error(request, "Erro ao cadastrar endereço, tente novamente")
            return redirect('cadastrar_clientes_etapa2', cliente_id=cliente.id_cliente)

    return render(request, 'auth/cadastrar-clientes-2.html', {'cliente': cliente})
