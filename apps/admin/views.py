from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from apps.appEmpresa.views import resumir_user_agent
from apps.authentication.views import logout
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from apps.authentication.models import AvaliacaoPedido, Cardapio, Categoria, Cliente, CustomUser, Empresa, EmpresaUsuario, EnderecoCliente, EnderecoPedido, Estoque, HistoricoPedido, Ingrediente, IngredienteCardapio, ItemPedido, MovimentacaoEstoque, Pagamento, Pedido, AvaliacaoPedido, Sequencia 
from django.contrib.sessions.models import Session
from django.utils import timezone
import locale
from django.contrib.auth.forms import PasswordChangeForm
from django.db import transaction
from django.db.models import Count, Sum
locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')



def isadmin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_adm:
            return view_func(request, *args, **kwargs)
        else:
            logout(request)
            messages.error(request, 'Não tem acesso a admin, por favor faça seu login novamente.')
            return redirect('login')
    return wrapper

def masteruser_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.papel_adm == 'Master':
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, 'Não tem acesso a esse recurso.')
            return redirect('admin_empresas')
    return wrapper

@login_required
@isadmin_required
def deslogar_usuarios_empresa(request, empresa_id):
        try:
            empresa = Empresa.objects.get(id_empresa=empresa_id)
            usuarios = list(EmpresaUsuario.objects.filter(empresa=empresa).values_list('usuario_id', flat=True))  # Obtenha os IDs dos usuários

            # Filtra as sessões que correspondem aos usuários da empresa
            sessions_to_delete = Session.objects.filter(session_key__in=[
                session.session_key for session in Session.objects.all()
                if session.get_decoded().get('_auth_user_id') in map(str, usuarios)
            ])

            # Deleta as sessões filtradas
            sessions_to_delete.delete()

            messages.success(request, 'Todos os usuários da empresa foram deslogados com sucesso.')
        except Empresa.DoesNotExist:
            messages.error(request, 'Empresa não encontrada.')
        except Exception as e:
            messages.error(request, f'Erro: {e}')



class Dashboard:
    @login_required
    @isadmin_required
    def adminDashboard(request):
        if not request.user.papel_adm == 'Master':
            messages.error(request, 'Apenas usuários Master tem a permissão de ver a dashboard.')
            return redirect('admin_empresas')

        bairros = (
            Pedido.objects
            .values('endereco_cliente__bairro')
            .annotate(
                total_pedidos=Count('id'),
                total_valor=Sum('total'),
                total_clientes=Count('cliente', distinct=True)
            ).order_by('-total_pedidos')[:4])
        
        numero_pedidos = Pedido.objects.all().count()
        context = {
            'page_title': 'Dashboard',
            'bairros': bairros,
            'numero_pedidos': numero_pedidos,
        }
        return render(request, 'admin/dashboard.html', context)



class Empresas_Admin:
    
    @login_required
    @isadmin_required
    def empresas(request):
        empresas = Empresa.objects.all()
        context = {
            'page_title': 'Empresas',
            'empresas': empresas,
        }
        return render(request, 'admin/empresas.html', context)



    @login_required
    @isadmin_required
    def toggle_ativo_empresa(request, empresa_id):
        try:
            empresa = Empresa.objects.get(id_empresa=empresa_id)
            empresa.ativo = not empresa.ativo  # Alterna o valor de ativo
            empresa.save()
            
            if empresa.ativo:
                messages.success(request, 'Agora todos os usuários dessa empresa poderão acessar novamente.')
            else:
                deslogar_usuarios_empresa(request, empresa_id)
                messages.success(request, 'Todos os usuarios foram deslogados e impossibilitados de logar novamente.')
        except Empresa.DoesNotExist:
            messages.error(request, 'Empresa não encontrada.')
        except Exception as e:
            messages.error(request, f'Erro: {e}')
        
        return redirect('admin_empresas')



class Perfil:

    @login_required
    @isadmin_required
    def perfil_admin(request):
        user = request.user
        sessoes = []

        if request.method == "POST" and 'old_password' in request.POST:
            form_senha = PasswordChangeForm(user, request.POST)
            if form_senha.is_valid():
                user = form_senha.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Sua senha foi atualizada com sucesso!')
                return redirect('perfil_admin')
            else:
                messages.error(request, 'Por favor, corrija os erros abaixo.')
        else:
            form_senha = PasswordChangeForm(user)

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

        if request.method == 'POST' and 'deslogar_todas_sessoes' in request.POST:
            for session in Session.objects.all():
                data = session.get_decoded()
                if data.get('_auth_user_id') == str(request.user.id):
                    session.delete()  # Deleta a sessão
            logout(request)  # Desloga o usuário da sessão atual
            return redirect('perfil_admin')
                
        context = {
            'page_title': 'Perfil',
            'sessoes': sessoes,
            'user': user,
            'form_senha': form_senha,
        }
        return render(request, 'admin/perfil.html', context)
    
    @login_required
    @isadmin_required
    def editar_imagem_perfil_admin(request, user_id):
        if request.method == "POST" and request.FILES.get('profile_image'):
            user = CustomUser.objects.get(id=user_id)
            user.profile_image = request.FILES['profile_image']
            user.save()
            return JsonResponse({'new_image_url': user.profile_image.url})
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    @login_required
    @isadmin_required
    def change_password(request):
        if request.method == "POST":
            form_senha = PasswordChangeForm(request.user, request.POST)
            if form_senha.is_valid():
                user = form_senha.save()
                update_session_auth_hash(request, user)
                return render(request, 'senha_alterada.html')
        else:
            user = CustomUser.objects.get(pk=request.user.id)
            form_senha = PasswordChangeForm(request.user)
        return render(request, 'X', {'form_senha': form_senha})



class Controle_Users:
    
    @login_required
    @isadmin_required
    @masteruser_required
    def controle_usuarios_admin(request):
        usuarios = CustomUser.objects.filter(is_adm=True)
        context = {
            'page_title': 'Controle de Usuários',
            'usuarios': usuarios,
        }

        return render(request, 'admin/controle_users.html', context)



    @login_required
    @isadmin_required
    @masteruser_required
    def toggle_ativo_user(request, user_id):
        try:
            user = CustomUser.objects.get(id=user_id)
            if user.papel_adm == 'Master':
                messages.error(request, f'Não é possivel inativar um usuário com papel de {user.papel_adm} do sistema, favor contatar o Administrador do sistema.')
                return redirect('controle_usuarios_admin')
            user.ativo = not user.ativo  # Alterna o valor de ativo
            user.save()
            
            if user.ativo:
                messages.success(request, 'Agora o usuário poderá acessar novamente.')
            else:
                user = get_object_or_404(CustomUser, id=user_id)
                sessions = Session.objects.filter(expire_date__gte=timezone.now())
                
                for session in sessions:
                    data = session.get_decoded()
                    if data.get('_auth_user_id') == str(user.id):
                        session.delete()
                messages.success(request, 'O usuario foi deslogado e impossibilitado de logar novamente.')
        except CustomUser.DoesNotExist:
            messages.error(request, 'Usuário não encontrado.')
        except Exception as e:
            messages.error(request, f'Erro: {e}')
        
        return redirect('controle_usuarios_admin')
    


    @login_required
    @isadmin_required
    @masteruser_required
    def create_user_admin(request):
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
                    return redirect('controle_usuarios_admin')

                if password != confirm_password:
                    messages.error(request, "Erro ao cadastrar, senhas não coincidem.")
                    return redirect('controle_usuarios_admin')


                with transaction.atomic():
                    # Criando o ingrediente
                    custom_user = CustomUser(
                            first_name=first_name,
                            last_name=last_name,
                            email=email,
                            is_adm=True,
                            username=email,
                            password=password,
                            papel_adm=papel,
                        )
                    custom_user.set_password(password)
                    custom_user.save()

                messages.success(request, f'{first_name} Cadastrado com Sucesso!')
                return redirect('controle_usuarios_admin')
            except Exception as e:
                messages.error(request, "Erro ao cadastrar, verifique os dados e tente novamente.")
                return redirect('controle_usuarios_admin')
            
        return redirect('controle_usuarios_admin')