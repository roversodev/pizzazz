import uuid
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.utils.timezone import localtime
from django.contrib.sessions.models import Session

@receiver(user_logged_in)
def salvar_informacoes_sessao(sender, request, user, **kwargs):
    session_key = request.session.session_key

    # Gerar um identificador único para o dispositivo
    device_id = str(uuid.uuid4())  # ID único para o dispositivo

    # Salva as informações de dispositivo na sessão
    request.session['device_info'] = request.META.get('HTTP_USER_AGENT', 'Desconhecido')
    request.session['is_active'] = True
    request.session['device_id'] = device_id  # Associa o dispositivo à sessão
    request.session['location'] = 'Brasil'  # Você pode usar geolocalização aqui

    # Atualiza a sessão
    session = Session.objects.get(session_key=session_key)
    session.save()
