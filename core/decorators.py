from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

def sindico_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.tipo_usuario in ['sindico', 'imobiliaria', 'administrador']:
            return view_func(request, *args, **kwargs)
        raise PermissionDenied("Acesso restrito a síndicos, imobiliárias e administradores.")
    return _wrapped_view