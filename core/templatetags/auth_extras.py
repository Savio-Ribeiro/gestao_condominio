from django import template

register = template.Library()

@register.filter(name='is_admin_or_sindico')
def check_user_type(user):
    if hasattr(user, 'tipo_usuario'):
        return (user.tipo_usuario in ['sindico', 'outro'] or 
                getattr(user, 'is_admin_user', False) or 
                user.is_superuser)
    return False