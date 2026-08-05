"""
Template tags personalizados para mejorar el renderizado de formularios.
Agrega la clase 'is-invalid' de Bootstrap a campos con errores.
"""
from django import template

register = template.Library()


@register.filter(name='add_invalid')
def add_invalid(field):
    """
    Agrega la clase CSS 'is-invalid' de Bootstrap al widget del campo
    cuando éste tiene errores de validación.
    Uso en template: {{ field|add_invalid }}
    """
    if field.errors:
        css_classes = field.field.widget.attrs.get('class', '')
        if 'is-invalid' not in css_classes:
            field.field.widget.attrs['class'] = css_classes + ' is-invalid'
    return field


@register.filter(name='add_valid')
def add_valid(field):
    """
    Agrega la clase 'is-valid' cuando el campo fue procesado sin errores
    (solo si el formulario fue enviado, es decir si el campo tiene datos).
    """
    if field.html_name in field.form.data and not field.errors:
        css_classes = field.field.widget.attrs.get('class', '')
        if 'is-valid' not in css_classes:
            field.field.widget.attrs['class'] = css_classes + ' is-valid'
    return field
