import locale, re, random, string
from datetime import timezone, timedelta
from django.core.mail import EmailMessage
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.contrib.auth import get_user_model
from django.contrib import messages
from .models import Empresa, EmpresaUsuario, EnderecoEmpresa, CustomUser, Ingrediente, IngredienteCardapio, Cardapio, Estoque, PasswordResetVerification, Pedido, ItemPedido, Cliente, EnderecoCliente
from django.db import transaction
from django.contrib.auth import logout as auth_logout, authenticate, login as auth_login
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.timezone import now
locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')


def remover_mascara_cnpj(cnpj):
    return re.sub(r'\D', '', cnpj)

def remover_mascara_preço(preco):
    formatado = preco.replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    return formatado

def generate_verification_code():
    # Gera um código aleatório de 6 dígitos
    code = ''.join(random.choices(string.digits, k=6))
    return code

def generate_expiration_time():
    # Define um tempo de expiração para o código de verificação (ex: 15 minutos)
    return now() + timedelta(minutes=15)

def send_verification_email(user, verification_code):

    html_content = render_to_string('auth/mail/2step.html', {
        'username': user.get_full_name,
        'verification_code': verification_code,
        'reset_password_url': 'https://app.pizzazzz.com.br/reset-password/' + str(user.id) + '/' + verification_code
    })
    send_mail(
                    subject="Código de Verificação para Alteração de Senha",
                    message='Código de Verificação para Alteração de Senha',
                    from_email="no-reply@pizzazzz.com.br",
                    recipient_list=[user.email],
                    html_message=html_content
                    )


def login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, username=email, password=password)
        if user is not None:
            if user.is_empresa:
                emp = EmpresaUsuario.objects.get(usuario=user.id)
                empresa = Empresa.objects.get(cnpj=emp.empresa.cnpj)
                if empresa.ativo == False:
                    messages.error(request, 'A empresa está desativada. Entre em contato com o administrador da plataforma.')
                    return redirect('login')
                if emp.ativo == False:
                    messages.error(request, 'O seu usuário está desativado. Entre em contato com o administrador da empresa.')
                    return redirect('login')
            auth_login(request, user)

            context = {
                'nome': user.get_full_name
            }
            html_content = render_to_string('auth/mail/boas-vindas-emp.html', context)
            html_content_c = render_to_string('auth/mail/em-breve.html', context)


            if user.is_adm:
                if user.ativo:
                    return redirect('adminD')
                else:
                    messages.error(request, 'O seu usuário está desativado. Entre em contato com o administrador da plataforma.')
                    auth_logout(request)
                    return redirect('login')


            if user.is_empresa:
                emp = EmpresaUsuario.objects.get(usuario=user.id)
                cnpj = remover_mascara_cnpj(emp.empresa.cnpj)

                if user.is_first_login == True:
                    send_mail(
                    subject="Boas Vindas ao PizzazzZ!",
                    message='Boas Vindas ao PizzazzZ!',
                    from_email="no-reply@pizzazzz.com.br",
                    recipient_list=[email],
                    html_message=html_content
                    )

                    user.is_first_login = False
                    user.save()
                
                if emp.papel == 'Pizzaiolo':
                    return redirect('pizzaiolo', cnpj=cnpj)

                return redirect('dashboard', cnpj=cnpj)
            
            send_mail(
                    subject="Em Breve PizzazzZ!",
                    message='Em Breve PizzazzZ!',
                    from_email="no-reply@pizzazzz.com.br",
                    recipient_list=[email],
                    html_message=html_content_c
                    )
            return redirect('em_breve')
        else:
            messages.error(request, "E-mail ou senha inválidos")
            return redirect('login')
        
    

    return render(request, 'auth/login.html')



def em_breve(request):
    auth_logout(request)
    return render(request, 'auth/em-breve.html')



def logout(request):
    auth_logout(request)
    messages.success(request, 'Deslogado com sucesso.')
    return redirect('login')



def cadastrar_parceiros(request):
    try:
        if request.user.is_superuser:
    
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
                    first_name = request.POST.get('first_name')
                    last_name = request.POST.get('last_name')

                    with transaction.atomic():
                        user = CustomUser.objects.create_user(
                            email=email,
                            password=password,
                            is_empresa=True,
                            username=email,
                            last_name=last_name,
                            first_name=first_name,
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
    except Exception as e:
        messages.error(request, f'Sem permissão para acessar essa pagina. Apenas administradores {e}')
        return redirect('login')


#TO DO: Colocar login required e apenas acessar o dono do login em questão
def cadastrar_parceiros_etapa2(request, empresa_id):
    try:
        if request.user.is_superuser:
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
    except Exception as e:
        messages.error(request, 'Sem permissão para acessar essa pagina. Apenas administradores')
        return redirect('login')



def cadastrar_parceiros_etapa3(request, empresa_id):

    try:
        if request.user.is_superuser:
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
    except Exception as e:
        messages.error(request, 'Sem permissão para acessar essa pagina. Apenas administradores')
        return redirect('login')



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

            if CustomUser.objects.filter(email=email).exists():
                messages.error(request, "Já existe um usuário com este e-mail.")
                return redirect('cadastrar_clientes')

            if Cliente.objects.filter(cpf=cpf).exists():
                user = CustomUser.objects.create_user(
                    email=email,
                    password=password,
                    is_cliente=True,
                    username=email,
                    first_name=primeiro_nome,
                    last_name=ultimo_nome
                )
                user.save()
                messages.success(request, "Cadastro completo! Faça seu login.")
                return redirect('login', cliente_id=cliente.id_cliente)


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



def request_reset_password(request):
    if request.method == 'POST':
        try:
            email = request.POST.get('email')
            user = CustomUser.objects.get(email=email)
            verification_code = generate_verification_code()
            expiration_time = generate_expiration_time()

            if PasswordResetVerification.objects.filter(user=user).exists():
                PasswordResetVerification.objects.filter(user=user).delete()

            passdb = PasswordResetVerification.objects.create(
                user=user,
                code=verification_code,
                expiration_time=expiration_time
            )
            # Enviando o e-mail
            send_verification_email(user, verification_code)
            
            return redirect('verificar_codigo', user_id=str(user.id))
        except Exception as e:
            messages.error(request, f'Usuário não encontrado. Por favor verifique os dados digitados. {e}')
            return redirect('request_reset_password')

    return render(request, 'auth/request_reset_password.html')



def verificar_codigo(request, user_id):
    usuario = PasswordResetVerification.objects.get(user__id=user_id)
    if request.method == 'POST':
        code1 = request.POST.get('code_1')
        code2 = request.POST.get('code_2')
        code3 = request.POST.get('code_3')
        code4 = request.POST.get('code_4')
        code5 = request.POST.get('code_5')
        code6 = request.POST.get('code_6')

        code = code1 + code2 + code3 + code4 + code5 + code6

        return redirect('reset_password', user_id=user_id, verification_code=code)

    context = {
        'usuario': usuario
    }
    return render(request, 'auth/2step-verify.html', context)



def reset_password(request, user_id, verification_code):
    try:
        # Obtém o usuário
        user = CustomUser.objects.get(id=user_id)

        # Busca o código de verificação no banco de dados
        verification = PasswordResetVerification.objects.get(user=user, code=verification_code)

        # Verifica se o código expirou
        if verification.is_expired():
            verification.delete()
            messages.error(request, 'O código de verificação expirou. Solicite um novo código.')
            return redirect('request_reset_password')

        if request.method == 'POST':
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')

            if new_password != confirm_password:
                messages.error(request, 'As senhas não coincidem. Tente novamente.')
                return redirect('reset_password', user_id=user.id, verification_code=verification_code)

            # Alterando a senha do usuário
            user.set_password(new_password)
            user.save()

            # Deleta o código de verificação após o uso
            verification.delete()

            messages.success(request, 'Sua senha foi alterada com sucesso!')
            return redirect('login')

        context = {
            'user': user,
            'verification_code': verification_code,
        }

        return render(request, 'auth/reset-password.html', context)

    except PasswordResetVerification.DoesNotExist:
        messages.error(request, 'Código de verificação inválido ou expirado.')
        return redirect('verificar_codigo', user_id=user_id)

    except Exception as e:
        messages.error(request, f'Ocorreu um erro: {str(e)}')
        return redirect('request_reset_password')