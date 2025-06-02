# core/views.py
from django.utils import timezone
from urllib import request
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpResponse, HttpResponseForbidden

from core.admin import ComunicadoForm
from .models import Comunicado, Usuario, Chamado, MensagemChamado, Pagamento, Apartamento
from .forms import ComunicadoDashboardForm, UsuarioRegistrationForm, LoginForm, ChamadoForm, MensagemChamadoForm, PagamentoForm
import uuid
from django.templatetags.static import static
from .forms import UsuarioForm, ApartamentoFormSet
from django.core.exceptions import PermissionDenied
from django.contrib.auth.tokens import default_token_generator
from django.views.generic.edit import CreateView
from django.contrib.auth.forms import UserCreationForm

@login_required
def chamados_encerrados(request):
    chamados = Chamado.objects.filter(usuario=request.user, status='F').order_by('-data_fechamento')
    return render(request, 'core/chamados_encerrados.html', {'chamados': chamados})

@login_required
def encerrar_chamado(request, pk):
    chamado = get_object_or_404(Chamado, pk=pk, usuario=request.user)
    if chamado.status != 'F':
        chamado.status = 'F'
        chamado.data_fechamento = timezone.now()
        chamado.save()
        messages.success(request, 'Chamado encerrado com sucesso!')
    return redirect('core:chamados_encerrados')

def profile_view(request):
    return render(request, 'core/profile.html')

@login_required
@login_required
def dashboard(request):
    # Formulários de usuário e apartamento
    usuario_form = UsuarioRegistrationForm()
    formset = ApartamentoFormSet(queryset=Apartamento.objects.none())

    # Formulário de comunicado
    comunicado_form = ComunicadoDashboardForm(request.POST or None, request.FILES or None)
    
    # Processamento do formulário de comunicado
    if request.method == 'POST' and 'criar_comunicado' in request.POST:
        comunicado_form = ComunicadoDashboardForm(request.POST, request.FILES)
        if comunicado_form.is_valid():
            novo_comunicado = comunicado_form.save(commit=False)
            novo_comunicado.autor = request.user
            novo_comunicado.publicado = True
            novo_comunicado.save()
            messages.success(request, 'Comunicado publicado com sucesso!')
            return redirect('core:dashboard')
        else:
            messages.error(request, 'Por favor, corrija os erros no formulário de comunicado.')

    # Contagem de chamados
    chamados_ativos = Chamado.objects.filter(usuario=request.user, status__in=['A', 'R']).count()
    chamados_finalizados = Chamado.objects.filter(usuario=request.user, status='F').count()

    # Últimos chamados ativos
    ultimos_chamados_ativos = Chamado.objects.filter(
        usuario=request.user, status__in=['A', 'R']
    ).order_by('-id')[:3]

    # Últimos comunicados
    comunicados_recentes = Comunicado.objects.filter(publicado=True).order_by('-data_publicacao')[:3]

    # Primeiro nome do usuário
    primeiro_nome = request.user.nome.split()[0] if request.user.nome else "Usuário"

    # Processamento do formulário de usuário (para síndicos)
    if request.method == 'POST' and request.user.tipo_usuario == 'sindico' and 'registrar_usuario' in request.POST:
        usuario_form = UsuarioRegistrationForm(request.POST, request.FILES)
        tipo_usuario = request.POST.get('tipo_usuario', '')

        if tipo_usuario in ['proprietario', 'imobiliaria']:
            quantidade = int(request.POST.get('quantidade_apartamentos', 0))
            formsets_data = {
                'form-TOTAL_FORMS': str(quantidade),
                'form-INITIAL_FORMS': '0',
                'form-MIN_NUM_FORMS': '0',
                'form-MAX_NUM_FORMS': '1000',
            }
            for i in range(quantidade):
                formsets_data[f'form-{i}-numero_apartamento'] = request.POST.get(f'apartamento_numero_{i + 1}', '')
                formsets_data[f'form-{i}-bloco'] = request.POST.get(f'apartamento_bloco_{i + 1}', '')
            formset = ApartamentoFormSet(formsets_data, queryset=Apartamento.objects.none())
        else:
            formset = ApartamentoFormSet(queryset=Apartamento.objects.none())

        if usuario_form.is_valid() and formset.is_valid():
            usuario = usuario_form.save()
            if usuario.tipo_usuario in ['proprietario', 'imobiliaria']:
                for form in formset:
                    if form.cleaned_data.get('numero_apartamento'):
                        apartamento = form.save(commit=False)
                        apartamento.usuario = usuario
                        apartamento.save()
            messages.success(request, 'Usuário cadastrado com sucesso!')
            return redirect('core:dashboard')
        else:
            messages.error(request, 'Erro ao cadastrar usuário. Verifique os dados.')

    return render(request, 'core/dashboard.html', {
        'form': usuario_form,
        'formset': formset,
        'comunicado_form': comunicado_form,
        'chamados_ativos': chamados_ativos,
        'chamados_finalizados': chamados_finalizados,
        'ultimos_chamados_ativos': ultimos_chamados_ativos,
        'comunicados_recentes': comunicados_recentes,
        'primeiro_nome': primeiro_nome,
    })

@login_required
def registrar_usuario(request):
    if not (
        request.user.is_superuser or 
        request.user.is_staff or 
        getattr(request.user, 'is_admin_user', False) or
        request.user.tipo_usuario in ['sindico', 'imobiliaria', 'outro', 'A']
    ):
        return render(request, 'core/403.html', status=403)

    usuario_form = UsuarioRegistrationForm()
    formset = ApartamentoFormSet(queryset=Apartamento.objects.none())

    if request.method == 'POST':
        usuario_form = UsuarioRegistrationForm(request.POST, request.FILES)
        tipo_usuario = request.POST.get('tipo_usuario', '')
        formset_valid = True  # por padrão, assume que o formset é válido

        # Só processa apartamentos se necessário
        if tipo_usuario in ['proprietario', 'imobiliaria']:
            quantidade = int(request.POST.get('quantidade_apartamentos', 0))
            formsets_data = {
                'form-TOTAL_FORMS': str(quantidade),
                'form-INITIAL_FORMS': '0',
                'form-MIN_NUM_FORMS': '0',
                'form-MAX_NUM_FORMS': '1000',
            }
            for i in range(quantidade):
                formsets_data[f'form-{i}-numero_apartamento'] = request.POST.get(f'apartamento_numero_{i + 1}', '')
                formsets_data[f'form-{i}-bloco'] = request.POST.get(f'apartamento_bloco_{i + 1}', '')
            formset = ApartamentoFormSet(formsets_data, queryset=Apartamento.objects.none())
            formset_valid = formset.is_valid()
        else:
            formset = ApartamentoFormSet(queryset=Apartamento.objects.none())

        if usuario_form.is_valid() and formset_valid:
            usuario = usuario_form.save()

            if usuario.tipo_usuario in ['proprietario', 'imobiliaria']:
                for form in formset:
                    if form.cleaned_data.get('numero_apartamento'):
                        apartamento = form.save(commit=False)
                        apartamento.usuario = usuario
                        apartamento.save()

            messages.success(request, 'Usuário cadastrado com sucesso!')
            return redirect('core:registrar_usuario')
        else:
            print("Erros no formulário de usuário:")
            print(usuario_form.errors)
            print("Erros no formset de apartamentos:")
            print(formset.errors)
            messages.error(request, 'Erro ao cadastrar. Verifique os dados.')

    return render(request, 'core/register.html', {
        'form': usuario_form,
        'formset': formset
    })

def home(request):
    return render(request, 'core/home.html')

def register(request):
    if request.method == 'POST':
        form = UsuarioRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            current_site = get_current_site(request)
            mail_subject = 'Ative sua conta'
            message = render_to_string('core/acc_active_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            send_mail(
                mail_subject,
                message,
                'noreply@seudominio.com',
                [user.email],
                fail_silently=False,
                html_message=message
            )
            messages.success(request, 'Por favor, confirme seu email para completar o registro.')
            return redirect('core:login')
    else:
        form = UsuarioRegistrationForm()
    return render(request, 'core/register.html', {'form': form})

def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = Usuario.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Usuario.DoesNotExist):
        user = None
    if user is not None:
        user.is_active = True
        user.is_verified = True
        user.save()
        messages.success(request, 'Sua conta foi ativada com sucesso! Agora você pode fazer login.')
        return redirect('core:login')
    else:
        return HttpResponse('Link de ativação inválido!')

def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            cpf = form.cleaned_data['cpf']
            password = form.cleaned_data['password']
            user = authenticate(request, username=cpf, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    return redirect('core:dashboard')
                else:
                    messages.error(request, 'Sua conta está inativa.')
            else:
                messages.error(request, 'CPF ou senha incorretos.')
    else:
        form = LoginForm()
    return render(request, 'core/login.html', {'form': form})

@login_required
def user_logout(request):
    logout(request)
    return redirect('core:home')

@login_required
def abrir_chamado(request):
    if request.method == 'POST':
        form = ChamadoForm(request.POST, user=request.user)
        if form.is_valid():
            chamado = form.save(commit=False)
            chamado.usuario = request.user
            chamado.save()
            MensagemChamado.objects.create(
                chamado=chamado,
                usuario=request.user,
                mensagem=f"Descrição inicial do chamado:\n{chamado.descricao}",
                is_resposta_tecnica=False
            )
            messages.success(request, 'Chamado aberto com sucesso!')
            return redirect('core:acompanhar_chamados')
    else:
        form = ChamadoForm(user=request.user)
    return render(request, 'core/abrir_chamado.html', {
        'form': form,
    })

@login_required
def acompanhar_chamados(request):
    chamados = Chamado.objects.filter(
        usuario=request.user
    ).filter(
        status__in=['A', 'E', 'R']
    ).order_by('-data_abertura')
    return render(request, 'core/acompanhar_chamados.html', {
        'chamados': chamados
    })

@login_required
def detalhe_chamado(request, chamado_id):
    if request.user.is_staff:
        chamado = get_object_or_404(Chamado, id=chamado_id)
    else:
        chamado = get_object_or_404(Chamado, id=chamado_id, usuario=request.user)
    if request.method == 'POST':
        mensagem = request.POST.get('mensagem', '').strip()
        if mensagem:
            MensagemChamado.objects.create(
                chamado=chamado,
                usuario=request.user,
                mensagem=mensagem,
                is_resposta_tecnica=request.user.is_staff
            )
            if chamado.status == 'F':
                chamado.status = 'R'
                chamado.save()
            return redirect('core:detalhe_chamado', chamado_id=chamado.id)
    mensagens = chamado.mensagens.all().order_by('-data_envio')
    return render(request, 'core/detalhe_chamado.html', {
        'chamado': chamado,
        'mensagens': mensagens
    })

@login_required
def encerrar_chamado(request, pk):
    chamado = get_object_or_404(Chamado, pk=pk, usuario=request.user)
    if chamado.status != 'F':
        chamado.status = 'F'
        chamado.data_fechamento = timezone.now()
        chamado.save()
        messages.success(request, 'Chamado encerrado com sucesso!')
    return redirect('core:acompanhar_chamados')

@login_required
def historico_chamados(request):
    chamados = Chamado.objects.filter(usuario=request.user, status='F').order_by('-data_fechamento')
    return render(request, 'core/historico_chamados.html', {'chamados': chamados})

@login_required
def reabrir_chamado(request, pk):
    chamado = get_object_or_404(Chamado, pk=pk, usuario=request.user)
    if chamado.status == 'F':
        chamado.status = 'R'
        chamado.data_fechamento = None
        chamado.save()
        messages.success(request, 'Chamado reaberto com sucesso!')
    return redirect('core:acompanhar_chamados')

@login_required
def financeiro(request):
    pagamentos = Pagamento.objects.filter(usuario=request.user).order_by('-data_vencimento')
    return render(request, 'core/financeiro.html', {'pagamentos': pagamentos})

@login_required
def pagar_conta(request, pk):
    pagamento = get_object_or_404(Pagamento, pk=pk, usuario=request.user)
    if request.method == 'POST':
        form = PagamentoForm(request.POST, request.FILES, instance=pagamento)
        if form.is_valid():
            pagamento = form.save(commit=False)
            pagamento.status = 'A'
            pagamento.data_pagamento = timezone.now().date()
            pagamento.save()
            messages.success(request, 'Pagamento registrado com sucesso!')
            return redirect('core:financeiro')
    else:
        form = PagamentoForm(instance=pagamento)
    return render(request, 'core/pagar_conta.html', {
        'pagamento': pagamento,
        'form': form,
    })

@login_required
def baixar_nota_fiscal(request, pk):
    pagamento = get_object_or_404(Pagamento, pk=pk, usuario=request.user)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="nota_fiscal_{pk}.pdf"'
    return response

def bad_request(request, exception):
    return render(request, '400.html', status=400)

def permission_denied(request, exception):
    return render(request, '403.html', status=403)

def page_not_found(request, exception):
    return render(request, '404.html', status=404)

def server_error(request):
    return render(request, '500.html', status=500)

@login_required
def perfil(request):
    usuario = request.user
    context = {
        'usuario': usuario,
        'foto_url': get_user_photo_url(usuario)
    }
    return render(request, 'core/perfil.html', context)

def get_user_photo_url(user):
    if user.foto and hasattr(user.foto, 'url'):
        return user.foto.url
    return static('images/default.jpg')


@login_required
def perfil(request):
    usuario = request.user
    context = {
        'usuario': usuario,
        'foto_url': get_user_photo_url(usuario)
    }
    return render(request, 'core/perfil.html', context)

def get_user_photo_url(user):
    """Função auxiliar para obter a URL da foto do usuário com fallback"""
    if user.foto and hasattr(user.foto, 'url'):
        return user.foto.url
    return static('images/default.jpg')

def lista_comunicados(request):
    comunicados = Comunicado.objects.filter(publicado=True).order_by('-data_publicacao')
    return render(request, 'core/comunicados.html', {'comunicados': comunicados})

def detalhe_comunicado(request, pk):
    comunicado = get_object_or_404(Comunicado, pk=pk, publicado=True)
    return render(request, 'core/detalhe_comunicado.html', {'comunicado': comunicado})

@login_required
def comunicado_action(request):
    if request.method == 'POST' and request.user.tipo_usuario == 'sindico':
        action = request.POST.get('action')
        comunicado_id = request.POST.get('comunicado_id')
        
        if action and comunicado_id:
            comunicado = get_object_or_404(Comunicado, id=comunicado_id, autor=request.user)
            
            if action == 'delete':
                comunicado.delete()
                messages.success(request, 'Comunicado removido com sucesso!')
            elif action == 'toggle':
                comunicado.publicado = not comunicado.publicado
                comunicado.save()
                
            return redirect('core:dashboard')
    
    return redirect('core:dashboard')