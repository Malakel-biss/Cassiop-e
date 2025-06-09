from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Filtre pour accéder aux éléments d'un dictionnaire par clé dans un template.
    """
    return dictionary.get(key)

@register.filter
def divisibleby(value, arg):
    """Retourne la division entière de value par arg"""
    try:
        return int(int(value) // int(arg))
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def modulo(value, arg):
    """Retourne le modulo de value par arg"""
    try:
        return int(int(value) % int(arg))
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def multiply(value, arg):
    """Multiplie value par arg"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0 