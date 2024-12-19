from django import template
import re

register = template.Library()  # This line registers the filter library

@register.filter
def split(value):
    """Dividir a string por espaços"""
    return value.split()

@register.filter
def capitalize_words(value):
    """Capitaliza a primeira letra de cada palavra e transforma o resto em minúsculas"""
    return ' '.join(word.capitalize() for word in value.split())

@register.filter
def truncate_text(value, arg):
    """Trunca o texto para o número de caracteres especificado."""
    if isinstance(value, str) and len(value) > arg:
        return value[:arg] + '...'
    return value

@register.filter(name='remove_mask')
def remove_mask(cnpj):
    """Remove a máscara do CNPJ (ex: 12.345.678/0001-90 -> 12345678000190)."""
    return re.sub(r'\D', '', cnpj)

@register.filter
def get_item(dictionary, key):
    """Retorna o valor do dicionário para a chave especificada."""
    return dictionary.get(key)

@register.filter
def total_bruto(pedidos):
    return sum(p.total for p in pedidos if p.total)

@register.filter
def filter_by_date(pedidos, data):
    """Filtra pedidos pela data específica"""
    return [p for p in pedidos if p.data_pedido.date() == data.date()]