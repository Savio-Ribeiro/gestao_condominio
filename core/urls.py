from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views
from django.views.generic.base import RedirectView

app_name = 'core'

handler400 = 'core.views.bad_request'
handler403 = 'core.views.permission_denied'
handler404 = 'core.views.page_not_found'
handler500 = 'core.views.server_error'

urlpatterns = [
    #path('', views.home, name='home'),
    path('', views.user_login, name='home'),
    path('sair/', views.user_logout, name='user_logout'),
    path('perfil/', views.perfil, name='perfil'),
    path('login/', views.user_login, name='login'),
    path('registrar-usuario/', views.registrar_usuario, name='register'),
    path('registrar-usuario/', views.registrar_usuario, name='registrar_usuario'),
    path('chamados-encerrados/', views.chamados_encerrados, name='chamados_encerrados'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('abrir_chamado/', views.abrir_chamado, name='abrir_chamado'),
    path('reabrir-chamado/<int:pk>/', views.reabrir_chamado, name='reabrir_chamado'),
    path('profile/', views.profile_view, name='profile'),
    path('acompanhar_chamados/', views.acompanhar_chamados, name='acompanhar_chamados'),
    path('chamado/<int:chamado_id>/', views.detalhe_chamado, name='detalhe_chamado'),
    path('financeiro/', views.financeiro, name='financeiro'),
    path('historico_chamados/', views.historico_chamados, name='historico_chamados'),
    path('encerrar-chamado/<int:pk>/', views.encerrar_chamado, name='encerrar_chamado'),
    path('ativar/<uidb64>/<token>/', views.activate, name='activate'),
    path('comunicados/', views.lista_comunicados, name='lista_comunicados'),
    path('comunicado/<int:pk>/', views.detalhe_comunicado, name='detalhe_comunicado'),
    path('comunicado/action/', views.comunicado_action, name='comunicado_action'),
    path('chamado-<slug:nome>-<str:numero>-<slug:bloco>.html', views.detalhe_chamado_slug, name='detalhe_chamado_slug'),
    path('sindico/chamados/', views.chamados_moradores, name='chamados_moradores'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)