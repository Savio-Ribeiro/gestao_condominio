# core/context_processors.py

from django.templatetags.static import static

def user_info(request):
    if request.user.is_authenticated:
        foto = request.user.foto
        if foto and hasattr(foto, 'url'):
            foto_url = foto.url
        else:
            foto_url = static('img/foto-perfil.png')  # Caminho padrão correto

        primeiro_nome = request.user.get_full_name()

        return {
            'foto_url': foto_url,
            'primeiro_nome': primeiro_nome,
        }
    return {}

