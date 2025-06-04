# core/forms.py

from django import forms
from .models import Despesa, ItemDespesa, Receita, ItemReceita
from django.forms import modelformset_factory
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import Comunicado, Usuario, Apartamento, Chamado, MensagemChamado, Pagamento


# Formulário usado no admin para criar/editar usuários com campo extra
class UsuarioAdminForm(UserChangeForm):
    quantidade_apartamentos = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=20,
        label='Quantidade de apartamentos',
        help_text='Preencha apenas se desejar adicionar novos apartamentos.'
    )

    class Meta:
        model = Usuario
        fields = '__all__'


# Formulário de registro de usuário para uso no frontend
class UsuarioRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    confirmar_email = forms.EmailField(required=True)
    foto = forms.ImageField(required=False)
    quantidade_apartamentos = forms.IntegerField(
    required=False,
    min_value=0,
    max_value=10,
    label='Quantidade de Apartamentos',
    widget=forms.NumberInput(attrs={
        'class': 'form-control',
        'id': 'id_quantidade_apartamentos'
    })
)

    class Meta:
        model = Usuario
        fields = (
            'tipo_usuario', 'nome', 'nome_condominio', 'cpf',
            'email', 'confirmar_email', 'password1', 'password2', 'foto', 'quantidade_apartamentos'
        )
        field_order = [
            'tipo_usuario', 'cpf', 'nome', 'nome_condominio',
            'email', 'confirmar_email', 'password1', 'password2', 'foto', 'quantidade_apartamentos'
        ]

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        confirmar_email = cleaned_data.get('confirmar_email')

        if email and confirmar_email and email != confirmar_email:
            self.add_error('confirmar_email', 'Os emails não coincidem.')

        # Remover campo extra que não existe no model antes do save
        cleaned_data.pop('confirmar_email', None)
        return cleaned_data

# Formulário de login por CPF
class LoginForm(forms.Form):
    cpf = forms.CharField(max_length=14, label='CPF')
    password = forms.CharField(widget=forms.PasswordInput, label='Senha')


# Formulário de criação de chamado
class ChamadoForm(forms.ModelForm):
    class Meta:
        model = Chamado
        fields = ['titulo', 'descricao', 'apartamento']
        
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['apartamento'].queryset = Apartamento.objects.filter(usuario=user)
            self.fields['apartamento'].label_from_instance = lambda obj: str(obj)


# Formulário para adicionar mensagens aos chamados
class MensagemChamadoForm(forms.ModelForm):
    class Meta:
        model = MensagemChamado
        fields = ['mensagem']
        widgets = {
            'mensagem': forms.Textarea(attrs={'rows': 3}),
        }


# Formulário de upload de pagamento
class PagamentoForm(forms.ModelForm):
    class Meta:
        model = Pagamento
        fields = ['metodo_pagamento', 'comprovante']


# Formulário padrão de usuário (manual)
class UsuarioForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label='Senha')

    class Meta:
        model = Usuario
        fields = ['cpf', 'email', 'nome', 'foto', 'tipo_usuario', 'nome_condominio', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])  # Criptografa a senha
        if commit:
            user.save()
        return user


# Formulário de apartamento
class ApartamentoForm(forms.ModelForm):
    class Meta:
        model = Apartamento
        fields = ['numero_apartamento', 'bloco']


# Formset de apartamento
ApartamentoFormSet = modelformset_factory(Apartamento, form=ApartamentoForm, extra=0)

class ComunicadoDashboardForm(forms.ModelForm):
    class Meta:
        model = Comunicado
        fields = ['titulo', 'conteudo', 'imagem']
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título do comunicado'
            }),
            'conteudo': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Digite o conteúdo do comunicado...'
            }),
            'imagem': forms.FileInput(attrs={
                'class': 'form-control-file',
                'accept': 'image/*'
            })
        }
        labels = {
            'imagem': 'Imagem (Opcional)'
        }

#FORMULÁRIO DE DESPESAS E RECEITAS

class DespesaForm(forms.ModelForm):
    class Meta:
        model = Despesa
        fields = ['titulo', 'comprovantes', 'detalhamento']
        widgets = {
            'detalhamento': forms.Textarea(attrs={'rows': 3})
        }

class ReceitaForm(forms.ModelForm):
    class Meta:
        model = Receita
        fields = ['titulo']