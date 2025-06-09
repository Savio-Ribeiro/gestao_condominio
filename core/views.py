# core/views.py
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.utils.text import slugify
from urllib import request
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpResponse, HttpResponseForbidden
from core.admin import ComunicadoForm
from .models import Comunicado, Usuario, Chamado, MensagemChamado, Pagamento, Apartamento, Votacao, Voto
from .forms import ComunicadoDashboardForm, UsuarioRegistrationForm, LoginForm, ChamadoForm, MensagemChamadoForm, PagamentoForm, VotacaoForm
import uuid
from django.templatetags.static import static
from .forms import UsuarioForm, ApartamentoFormSet
from django.core.exceptions import PermissionDenied
from django.contrib.auth.tokens import default_token_generator
from django.views.generic.edit import CreateView
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q
from .models import Despesa, ItemDespesa, Receita, ItemReceita
from .forms import DespesaForm, ReceitaForm
from django.contrib import messages
from django.db.models import Sum
import calendar
import csv
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from datetime import datetime
from .models import Despesa, Receita
from .models import Votacao, Voto

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
def dashboard(request):
    total_despesas = Despesa.objects.aggregate(Sum('itens__valor'))['itens__valor__sum'] or 0
    total_receitas = Receita.objects.aggregate(Sum('itens__valor'))['itens__valor__sum'] or 0
    saldo_liquido = total_receitas - total_despesas
    # Obter o mês e ano atual
    hoje = timezone.now()
    mes_atual = hoje.month
    ano_atual = hoje.year
    nome_mes_atual = _(hoje.strftime('%B'))  # Isso usará a tradução do Django
    # Filtrar despesas e receitas pelo mês atual
    total_despesas = Despesa.objects.filter(
        data__month=mes_atual,
        data__year=ano_atual
    ).aggregate(Sum('itens__valor'))['itens__valor__sum'] or 0

    total_receitas = Receita.objects.filter(
        data__month=mes_atual,
        data__year=ano_atual
    ).aggregate(Sum('itens__valor'))['itens__valor__sum'] or 0
    
    saldo_liquido = total_receitas - total_despesas

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

    # Contagem de pagamentos pendentes
    pendentes = Pagamento.objects.filter(usuario=request.user, status='P').count()

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
        'pendentes': pendentes,
        'total_despesas': total_despesas,
        'total_receitas': total_receitas,
        'saldo_liquido': saldo_liquido,
        'nome_mes_atual': nome_mes_atual,  # Adicionando o nome do mês ao contexto
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
        formset_valid = True

        # Prepara o formset com os dados inseridos dinamicamente
        if tipo_usuario in ['proprietario', 'imobiliaria']:
            # Captura todos os campos de apartamento enviados
            apartamentos_data = []
            i = 1
            while f'apartamento_numero_{i}' in request.POST:
                numero = request.POST.get(f'apartamento_numero_{i}', '').strip()
                bloco = request.POST.get(f'apartamento_bloco_{i}', '').strip()
                if numero:  # Só adiciona se tiver número
                    apartamentos_data.append({
                        'numero_apartamento': numero,
                        'bloco': bloco if bloco else None
                    })
                i += 1

            # Prepara o formset com os dados capturados
            formsets_data = {
                'form-TOTAL_FORMS': str(len(apartamentos_data)),
                'form-INITIAL_FORMS': '0',
                'form-MIN_NUM_FORMS': '0',
                'form-MAX_NUM_FORMS': '1000',
            }
            for i, apt_data in enumerate(apartamentos_data):
                formsets_data[f'form-{i}-numero_apartamento'] = apt_data['numero_apartamento']
                formsets_data[f'form-{i}-bloco'] = apt_data['bloco']
            
            formset = ApartamentoFormSet(formsets_data, queryset=Apartamento.objects.none())
            formset_valid = formset.is_valid()
        else:
            formset_valid = True  # Não precisa validar formset para outros tipos de usuário

        if usuario_form.is_valid() and formset_valid:
            usuario = usuario_form.save()

            if tipo_usuario in ['proprietario', 'imobiliaria']:
                for form in formset:
                    if form.cleaned_data.get('numero_apartamento'):
                        apartamento = form.save(commit=False)
                        apartamento.usuario = usuario
                        apartamento.save()

            messages.success(request, 'Usuário cadastrado com sucesso!')
            return redirect('core:registrar_usuario')
        else:
            print("Erros no formulário de usuário:", usuario_form.errors)
            if tipo_usuario in ['proprietario', 'imobiliaria']:
                print("Erros no formset de apartamentos:", formset.errors)
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

#FINANCEIRO

@login_required
# Adicione esta view no views.py
@login_required
def painel_financeiro(request):
    # Dados para os cards
    total_despesas = Despesa.objects.aggregate(Sum('itens__valor'))['itens__valor__sum'] or 0
    total_receitas = Receita.objects.aggregate(Sum('itens__valor'))['itens__valor__sum'] or 0
    saldo_liquido = total_receitas - total_despesas

    # Dados para o relatório
    registros = []
    for d in Despesa.objects.all():
        registros.append({
            'id': d.id,
            'titulo': d.titulo,
            'data': d.data,
            'tipo': 'despesa',
            'valor_total': d.valor_total()
        })
    
    for r in Receita.objects.all():
        registros.append({
            'id': r.id,
            'titulo': r.titulo,
            'data': r.data,
            'tipo': 'receita',
            'valor_total': r.valor_total()
        })

    registros.sort(key=lambda x: x['data'], reverse=True)

    return render(request, 'core/painel_financeiro.html', {
        'total_despesas': total_despesas,
        'total_receitas': total_receitas,
        'saldo_liquido': saldo_liquido,
        'registros': registros
    })

@login_required
def exportar_pagamentos_excel(request):
    pagamentos = Pagamento.objects.filter(usuario=request.user)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="pagamentos.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Método', 'Status', 'Data Vencimento', 'Data Pagamento', 'Valor'])

    for p in pagamentos:
        writer.writerow([
            p.id, p.get_metodo_pagamento_display(), p.get_status_display(),
            p.data_vencimento, p.data_pagamento, f"R$ {p.valor:.2f}"
        ])

    return response

@login_required
def exportar_pagamentos_pdf(request):
    pagamentos = Pagamento.objects.filter(usuario=request.user)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="pagamentos.pdf"'

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 50

    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Relatório de Pagamentos")
    y -= 30

    p.setFont("Helvetica", 10)
    for pagamento in pagamentos:
        linha = f"ID {pagamento.id} - {pagamento.get_status_display()} - R$ {pagamento.valor:.2f} - Venc: {pagamento.data_vencimento}"
        p.drawString(50, y, linha)
        y -= 20
        if y < 50:
            p.showPage()
            y = height - 50

    p.save()
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response

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
            return redirect('core:painel_financeiro')
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
    return static('img/foto-perfil.png')

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

@login_required
def chamados_moradores(request):
    if request.user.tipo_usuario != 'sindico':
        return HttpResponseForbidden("Acesso restrito ao síndico.")

    termo = request.GET.get('termo', '')
    chamados = Chamado.objects.select_related('usuario', 'apartamento')

    if termo:
        chamados = chamados.filter(
            Q(usuario__nome__icontains=termo) |
            Q(apartamento__numero_apartamento__icontains=termo) |
            Q(apartamento__bloco__icontains=termo)
        )
    chamados = chamados.order_by('-data_abertura')

    for chamado in chamados:
        chamado.slug_nome = slugify(chamado.usuario.nome or "")
        chamado.slug_bloco = slugify(chamado.apartamento.bloco or "")

    return render(request, 'core/chamados_moradores.html', {
        'chamados': chamados,
        'termo': termo
    })

@login_required
def detalhe_chamado_slug(request, nome, numero, bloco):
    if request.user.tipo_usuario != 'sindico':
        return HttpResponseForbidden("Acesso restrito ao síndico.")

    chamados = Chamado.objects.select_related('usuario', 'apartamento')

    for chamado in chamados:
        if (
            slugify(chamado.usuario.nome or "") == nome and
            chamado.apartamento.numero_apartamento == numero and
            slugify(chamado.apartamento.bloco or "") == bloco
        ):
            break
    else:
        raise Http404("Chamado não encontrado com os parâmetros fornecidos.")

    # Formulário de resposta
    if request.method == 'POST':
        mensagem = request.POST.get('mensagem', '').strip()
        if mensagem:
            MensagemChamado.objects.create(
                chamado=chamado,
                usuario=request.user,
                mensagem=mensagem,
                is_resposta_tecnica=True
            )
            if chamado.status == 'F':
                chamado.status = 'R'
                chamado.save()
            return redirect('core:detalhe_chamado_slug',
                            nome=slugify(chamado.usuario.nome or ""),
                            numero=numero,
                            bloco=slugify(chamado.apartamento.bloco or ""))

    mensagens = chamado.mensagens.all().order_by('-data_envio')
    return render(request, 'core/detalhe_chamado.html', {
        'chamado': chamado,
        'mensagens': mensagens
    })

#VIEWS DESPESAS E RECEITAS

from django.urls import reverse
from django.utils.http import urlencode

@login_required
def relatorio_despesas_receitas(request):
    filtro_mes = request.GET.get('mes')
    filtro_tipo = request.GET.get('tipo')

    despesas = Despesa.objects.all()
    receitas = Receita.objects.all()

    if filtro_mes:
        despesas = despesas.filter(data__month=filtro_mes)
        receitas = receitas.filter(data__month=filtro_mes)

    registros = []
    if filtro_tipo in [None, '', 'todos', 'despesas']:
        for d in despesas:
            registros.append({
                'id': d.id,
                'titulo': d.titulo,
                'data': d.data,
                'tipo': 'despesa',
                'valor_total': d.valor_total()
            })
    if filtro_tipo in [None, '', 'todos', 'receitas']:
        for r in receitas:
            registros.append({
                'id': r.id,
                'titulo': r.titulo,
                'data': r.data,
                'tipo': 'receita',
                'valor_total': r.valor_total()
            })

    registros.sort(key=lambda x: x['data'], reverse=True)

    meses = [calendar.month_abbr[m] for m in range(1, 13)]
    grafico_receitas = [
        Receita.objects.filter(data__month=m).aggregate(Sum('itens__valor'))['itens__valor__sum'] or 0
        for m in range(1, 13)
    ]
    grafico_despesas = [
        Despesa.objects.filter(data__month=m).aggregate(Sum('itens__valor'))['itens__valor__sum'] or 0
        for m in range(1, 13)
    ]

    return render(request, 'core/relatorio_de_despesas_e_receitas.html', {
        'registros': registros,
        'meses': meses,
        'receitas': grafico_receitas,
        'despesas': grafico_despesas,
    })

@login_required
def incluir_despesa(request):
    if request.user.tipo_usuario != 'sindico':
        return redirect('core:dashboard')

    if request.method == 'POST':
        form = DespesaForm(request.POST, request.FILES)
        if form.is_valid():
            despesa = form.save(commit=False)
            despesa.usuario = request.user
            despesa.save()

            descricoes = request.POST.getlist('item_descricao[]')
            valores = request.POST.getlist('item_valor[]')

            for desc, val in zip(descricoes, valores):
                if desc and val:
                    ItemDespesa.objects.create(
                        despesa=despesa,
                        descricao=desc,
                        valor=val
                    )

            messages.success(request, 'Despesa registrada com sucesso!')
        return redirect('core:relatorio_despesas_receitas')

@login_required
def incluir_receita(request):
    if request.user.tipo_usuario != 'sindico':
        return redirect('core:dashboard')

    if request.method == 'POST':
        form = ReceitaForm(request.POST)
        if form.is_valid():
            receita = form.save(commit=False)
            receita.usuario = request.user
            receita.save()

            descricoes = request.POST.getlist('item_descricao[]')
            valores = request.POST.getlist('item_valor[]')

            for desc, val in zip(descricoes, valores):
                if desc and val:
                    ItemReceita.objects.create(
                        receita=receita,
                        descricao=desc,
                        valor=val
                    )

            messages.success(request, 'Receita registrada com sucesso!')

        # Redireciona para relatorio com filtro tipo=receitas
        url = reverse('core:relatorio_despesas_receitas')
        query_string = urlencode({'tipo': 'receitas'})
        full_url = f'{url}?{query_string}'
        return redirect(full_url)

@login_required
def detalhe_registro(request, tipo, id):
    if tipo == 'despesa':
        registro = get_object_or_404(Despesa, id=id)
        return render(request, 'core/detalhe_despesa.html', {'despesa': registro})
    elif tipo == 'receita':
        registro = get_object_or_404(Receita, id=id)
        return render(request, 'core/detalhe_receita.html', {'receita': registro})
    else:
        messages.error(request, 'Tipo de registro inválido.')
        return redirect('core:relatorio_despesas_receitas')

@login_required
def criar_votacao(request):
    if request.user.tipo_usuario != 'sindico':
        raise PermissionDenied()

    form = VotacaoForm(request.POST or None)
    if form.is_valid():
        votacao = form.save(commit=False)
        votacao.criado_por = request.user
        votacao.save()
        messages.success(request, 'Votação criada com sucesso!')
        return redirect('core:lista_votacoes')
    
    return render(request, 'core/criar_votacao.html', {'form': form})


@login_required
def lista_votacoes(request):
    votacoes = Votacao.objects.filter(data_limite__gte=timezone.now()).order_by('-data_inicio')
    return render(request, 'core/lista_votacoes.html', {'votacoes': votacoes})


@login_required
@login_required
def sala_de_reuniao(request, pk):
    votacao = get_object_or_404(Votacao, pk=pk)

    if request.method == 'POST' and not votacao.encerrada():
        voto_valor = request.POST.get('voto')
        Voto.objects.update_or_create(
            votacao=votacao,
            usuario=request.user,
            defaults={'voto': voto_valor}
        )
        return redirect('core:sala_de_reuniao', pk=votacao.pk)


    votos = votacao.votos.all()
    favor = votos.filter(voto='a_favor').count()
    contra = votos.filter(voto='contra').count()
    ja_votou = votos.filter(usuario=request.user).first()

    return render(request, 'core/sala_de_reuniao.html', {
        'votacao': votacao,
        'favor': favor,
        'contra': contra,
        'ja_votou': ja_votou,
    })

@login_required
def votar(request, pk):
    votacao = get_object_or_404(Votacao, pk=pk)
    if votacao.encerrada():
        messages.error(request, 'A votação já foi encerrada.')
        return redirect('core:detalhe_votacao', pk=pk)

    voto_valor = request.POST.get('voto')
    if voto_valor in ['a_favor', 'contra']:
        Voto.objects.update_or_create(
            votacao=votacao,
            usuario=request.user,
            defaults={'voto': voto_valor}
        )
        messages.success(request, 'Seu voto foi registrado!')
    return redirect('core:detalhe_votacao', pk=pk)

@login_required
def relatorio_votacao(request, pk):
    if request.user.tipo_usuario != 'sindico':
        raise PermissionDenied()
    votacao = get_object_or_404(Votacao, pk=pk)
    votos = votacao.votos.select_related('usuario')
    return render(request, 'core/relatorio_votacao.html', {'votos': votos})

@login_required
def editar_votacao(request, pk):
    votacao = get_object_or_404(Votacao, pk=pk, criado_por=request.user)

    if request.user.tipo_usuario != 'sindico':
        raise PermissionDenied()

    if request.method == 'POST':
        form = VotacaoForm(request.POST, instance=votacao)
        if form.is_valid():
            form.save()
            messages.success(request, 'Votação atualizada com sucesso!')
            return redirect('core:sala_de_reuniao', pk=votacao.pk)
    else:
        form = VotacaoForm(instance=votacao)

    return render(request, 'core/editar_votacao.html', {'form': form, 'votacao': votacao})

