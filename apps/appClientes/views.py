from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from math import radians, cos, sin, sqrt, atan2
from django.db.models import Avg
from apps.authentication.models import Cliente, Empresa

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Raio da Terra em km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c  # Retorna a distância em km

@login_required
def restaurantes(request):
    user = request.user
    cliente = Cliente.objects.get(usuario=user)
    endereco_cliente = cliente.enderecos.last()

    if endereco_cliente:
        lat_cliente = endereco_cliente.latitude
        lon_cliente = endereco_cliente.longitude

        pizzarias = Empresa.objects.all().annotate(media_avaliacoes=Avg('pedido__avaliacao__nota'))
        pizzarias_proximas = []

        for pizzaria in pizzarias:
            lat_pizzaria = pizzaria.endereco.latitude
            lon_pizzaria = pizzaria.endereco.longitude

            # Calcula a distância
            distancia = haversine(lat_cliente, lon_cliente, lat_pizzaria, lon_pizzaria)
            if distancia <= 10:
                pizzaria.distancia = distancia
                pizzarias_proximas.append(pizzaria)
    
    context = {
        'pizzarias': pizzarias_proximas,
        'page_title': 'Home'
    }
    return render(request, 'clientes/home.html', context)


@login_required
def busca(request):
    context = {
        'page_title': 'Busca'
    }
    return render(request, 'clientes/busca.html', context)



@login_required
def pedidos(request):
    context = {
        'page_title': 'Pedidos'
    }
    return render(request, 'clientes/pedidos.html', context)



@login_required
def perfil(request):
    context = {
        'page_title': 'Perfil'
    }
    return render(request, 'clientes/perfil.html', context)