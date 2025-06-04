from django.contrib import admin
from .models import Comunicado, Usuario
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from .forms import MensagemChamadoForm
from .models import Chamado, MensagemChamado
from django import forms
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.db.models import Q
from .models import Despesa, ItemDespesa, Receita, ItemReceita
from .models import Apartamento, Usuario, Chamado, Pagamento, ClienteProxy, AdministradorProxy

# Desregistrar o modelo padrão se já estiver registrado
if admin.site.is_registered(Usuario):
    admin.site.unregister(Usuario)

# Formulário simplificado para Usuario (removida a lógica de apartamentos dinâmicos)
class UsuarioAdminForm(BaseUserAdmin.form):
    quantidade_apartamentos = forms.IntegerField(
        min_value=1,
        max_value=10,
        required=False,
        label="Quantidade de Apartamentos",
        widget=forms.NumberInput(attrs={'id': 'id_quantidade_apartamentos', 'class': 'form-control'})
    )

    class Meta:
        model = Usuario
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qtd = self.initial.get('quantidade_apartamentos') or self.data.get('quantidade_apartamentos', 0)
        try:
            qtd = int(qtd)
        except (TypeError, ValueError):
            qtd = 0

        for i in range(1, qtd + 1):
            self.fields[f'apartamento_numero_{i}'] = forms.CharField(
                label=f'Apartamento {i} - Número',
                required=False
            )
            self.fields[f'apartamento_bloco_{i}'] = forms.CharField(
                label=f'Apartamento {i} - Bloco',
                required=False
            )

# Inline do modelo Apartamento
class ApartamentoInline(admin.TabularInline):
    model = Apartamento
    extra = 0
    can_delete = True
    fields = ['numero_apartamento', 'bloco']
    classes = ['collapse']

# Admin para Usuario
@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin):
    form = UsuarioAdminForm
    inlines = [ApartamentoInline]
    list_display = ('nome', 'cpf', 'tipo_usuario', 'email', 'get_apartamentos_display')
    list_filter = ('tipo_usuario', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('cpf', 'email', 'nome')
    ordering = ('nome',)

    fieldsets = (
        (None, {
            'fields': ('cpf', 'password')
        }),
        ('Informações pessoais', {
            'fields': (
                'tipo_usuario', 'nome', 'email', 'nome_condominio',
                'foto', 'quantidade_apartamentos'
            )
        }),
        ('Status', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'is_admin_user')
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'cpf', 'password1', 'password2',
                'tipo_usuario', 'nome', 'email', 'nome_condominio',
                'foto', 'quantidade_apartamentos'
            ),
        }),
    )

    class Media:
        js = ('admin/js/apartamentos.js',)
        css = {
            'all': ('admin/css/custom.css',)
        }

    def get_apartamentos_display(self, obj):
        return obj.get_apartamentos_display()
    get_apartamentos_display.short_description = 'Apartamentos'

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        
        # Processar apartamentos dinâmicos
        qtd = form.cleaned_data.get('quantidade_apartamentos', 0)
        for i in range(1, qtd + 1):
            numero = form.cleaned_data.get(f'apartamento_numero_{i}')
            bloco = form.cleaned_data.get(f'apartamento_bloco_{i}')
            if numero:
                Apartamento.objects.get_or_create(
                    usuario=obj,
                    numero_apartamento=numero,
                    defaults={'bloco': bloco}
                )

# Admin para ClienteProxy
class ClienteAdminForm(UsuarioAdminForm):
    pass

class ClienteAdmin(admin.ModelAdmin):
    form = ClienteAdminForm
    inlines = [ApartamentoInline]
    list_display = ('email', 'cpf', 'tipo_usuario', 'nome_condominio', 'is_active', 'foto_preview')
    list_filter = ('tipo_usuario', 'is_active', 'nome_condominio')
    search_fields = ('email', 'cpf', 'nome', 'nome_condominio')
    ordering = ('email',)
    readonly_fields = ('foto_preview',)

    fieldsets = (
        (None, {
            'fields': ('email', 'password')
        }),
        ('Informações pessoais', {
            'fields': (
                'cpf', 'tipo_usuario', 'nome', 'nome_condominio',
                'foto', 'foto_preview', 'quantidade_apartamentos'
            )
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'cpf', 'password1', 'password2',
                'email', 'tipo_usuario', 'nome', 'nome_condominio',
                'foto', 'quantidade_apartamentos'
            ),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).filter(
            is_admin_user=False, is_superuser=False
        ).exclude(tipo_usuario='A')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        
        # Processar apartamentos dinâmicos
        qtd = form.cleaned_data.get('quantidade_apartamentos', 0)
        for i in range(1, qtd + 1):
            numero = form.cleaned_data.get(f'apartamento_numero_{i}')
            bloco = form.cleaned_data.get(f'apartamento_bloco_{i}')
            if numero:
                Apartamento.objects.get_or_create(
                    usuario=obj,
                    numero_apartamento=numero,
                    defaults={'bloco': bloco}
                )

    def foto_preview(self, obj):
        if obj.foto and obj.foto.url:
            return format_html('<img src="{}" style="max-height: 100px; border-radius: 50%;" />', obj.foto.url)
        return format_html('<img src="/static/images/default.jpg" style="max-height: 100px; border-radius: 50%;" />')
    foto_preview.short_description = "Foto"

# Admin para AdministradorProxy
class AdministradorAdmin(BaseUserAdmin):
    inlines = [ApartamentoInline]
    list_display = ('email', 'cpf', 'tipo_usuario', 'is_active', 'is_staff', 'is_superuser', 'is_admin_display')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'is_admin_user', 'tipo_usuario')
    search_fields = ('email', 'cpf', 'nome')
    ordering = ('email',)
    readonly_fields = ('foto_preview',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informações pessoais', {
            'fields': ('cpf', 'tipo_usuario', 'nome', 'foto_preview', 'foto')
        }),
        ('Permissões', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'is_admin_user', 'groups', 'user_permissions')
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'cpf', 'password1', 'password2', 'tipo_usuario',
                       'is_staff', 'is_active', 'is_superuser', 'is_admin_user'),
        }),
    )

    def is_admin_display(self, obj):
        return obj.is_admin_user or obj.is_superuser or obj.tipo_usuario == 'A'
    is_admin_display.boolean = True
    is_admin_display.short_description = 'É Admin?'

    def get_queryset(self, request):
        return super().get_queryset(request).filter(
            Q(is_admin_user=True) | Q(is_superuser=True) | Q(tipo_usuario='A')
        )

    def foto_preview(self, obj):
        if obj.foto and obj.foto.url:
            return format_html('<img src="{}" style="max-height: 100px; border-radius: 50%;" />', obj.foto.url)
        return format_html('<img src="/static/images/default.jpg" style="max-height: 100px; border-radius: 50%;" />')
    foto_preview.short_description = "Foto"

# ChamadoAdmin
@admin.register(Chamado)
class ChamadoAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'titulo', 'status', 'data_abertura', 'data_fechamento')
    list_filter = ('status',)
    search_fields = ('titulo', 'descricao', 'usuario__cpf', 'usuario__email')
    ordering = ('-data_abertura',)
    raw_id_fields = ('usuario',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.GET.get('status') == 'F':
            return qs.filter(status='F')
        elif request.GET.get('status') == 'A':
            return qs.exclude(status='F')
        return qs

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['custom_tabs'] = [
            {'title': 'Chamados Abertos', 'url': '?status=A'},
            {'title': 'Chamados Encerrados', 'url': '?status=F'},
        ]
        return super().changelist_view(request, extra_context=extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        chamado = get_object_or_404(Chamado, pk=object_id)
        mensagens = chamado.mensagens.all().order_by('-data_envio')
        for m in mensagens:
            m.css_classe = (
                "bg-warning-subtle border border-warning"
                if m.usuario.tipo_usuario == "sindico" else
                "bg-light border"
            )

        if request.method == 'POST' and 'mensagem' in request.POST:
            form = MensagemChamadoForm(request.POST)
            if form.is_valid():
                mensagem = form.save(commit=False)
                mensagem.usuario = request.user
                mensagem.chamado = chamado
                mensagem.is_resposta_tecnica = True
                mensagem.save()
                return HttpResponseRedirect(request.path_info)
        else:
            form = MensagemChamadoForm()

        extra_context = extra_context or {}
        extra_context.update({
            'mensagens': mensagens,
            'mensagem_form': form,
            'custom_view': True,
        })

        return super().change_view(request, object_id, form_url, extra_context=extra_context)

# PagamentoAdmin
@admin.register(Pagamento)
class PagamentoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'descricao', 'valor_formatado', 'data_vencimento', 'status', 'metodo_pagamento')
    list_filter = ('status', 'metodo_pagamento', 'data_vencimento')
    search_fields = ('usuario__cpf', 'usuario__email', 'descricao')
    ordering = ('-data_vencimento',)
    raw_id_fields = ('usuario',)

    fieldsets = (
        (None, {'fields': ('usuario', 'descricao', 'valor', 'comprovante')}),
        ('Datas', {'fields': ('data_vencimento', 'data_pagamento')}),
        ('Status', {'fields': ('status', 'metodo_pagamento')}),
    )

    def valor_formatado(self, obj):
        return f"R$ {obj.valor:,.2f}"
    valor_formatado.short_description = 'Valor'

# Registro dos Proxies
admin.site.register(ClienteProxy, ClienteAdmin)
admin.site.register(AdministradorProxy, AdministradorAdmin)


class ComunicadoForm(forms.ModelForm):
    class Meta:
        model = Comunicado
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configuração definitiva para o campo autor
        self.fields['autor'].required = True  # Torna o campo obrigatório
        self.fields['autor'].empty_label = None  # Remove completamente a opção None
        self.fields['autor'].label_from_instance = lambda obj: f"{obj.nome} (Síndico)"
        self.fields['autor'].queryset = Usuario.objects.filter(
            tipo_usuario='sindico'
        ).exclude(nome__isnull=True).exclude(nome__exact='').order_by('nome')

@admin.register(Comunicado)
class ComunicadoAdmin(admin.ModelAdmin):
    form = ComunicadoForm
    list_display = ('titulo', 'autor', 'data_publicacao', 'publicado')
    list_filter = ('publicado', 'autor')
    search_fields = ('titulo', 'conteudo')

    # Permite edição rápida no list view
    list_editable = ('publicado',)
    
    def display_autor(self, obj):
        if obj.autor:
            return f"{obj.autor.nome} (Síndico)"
        return "Não definido"
    display_autor.short_description = "Responsável"
    
    def save_model(self, request, obj, form, change):
        if not obj.autor_id:
            obj.autor = request.user
        super().save_model(request, obj, form, change)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "autor":
            kwargs["queryset"] = Usuario.objects.filter(
                tipo_usuario='sindico'
            ).exclude(nome__isnull=True).exclude(nome__exact='').order_by('nome')
            kwargs["empty_label"] = None  # Remove a opção vazia
            kwargs["required"] = True  # Torna o campo obrigatório
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
#DESPESAS E RECEITAS

class ItemDespesaInline(admin.TabularInline):
    model = ItemDespesa
    extra = 1

class DespesaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'usuario', 'data', 'valor_total_display')
    search_fields = ('titulo', 'usuario__nome')
    list_filter = ('data',)
    inlines = [ItemDespesaInline]

    def valor_total_display(self, obj):
        return f'R$ {obj.valor_total():.2f}'
    valor_total_display.short_description = 'Valor Total'

class ItemReceitaInline(admin.TabularInline):
    model = ItemReceita
    extra = 1

class ReceitaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'usuario', 'data', 'valor_total_display')
    search_fields = ('titulo', 'usuario__nome')
    list_filter = ('data',)
    inlines = [ItemReceitaInline]

    def valor_total_display(self, obj):
        return f'R$ {obj.valor_total():.2f}'
    valor_total_display.short_description = 'Valor Total'

admin.site.register(Despesa, DespesaAdmin)
admin.site.register(Receita, ReceitaAdmin)