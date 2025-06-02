from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.core.validators import RegexValidator
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from PIL import Image

class UsuarioManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, cpf, password, **extra_fields):
        if not cpf:
            raise ValueError('O CPF deve ser informado')
        user = self.model(cpf=cpf, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, cpf, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('is_admin_user', False)
        return self._create_user(cpf, password, **extra_fields)

    def create_superuser(self, cpf, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_admin_user', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser precisa ter is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser precisa ter is_superuser=True.')

        return self._create_user(cpf, password, **extra_fields)

class Usuario(AbstractBaseUser, PermissionsMixin):
    TIPO_USUARIO_CHOICES = [        
        ('sindico', 'Síndico'),
        ('proprietario', 'Proprietário'),
        ('inquilino', 'Inquilino'),
        ('imobiliaria', 'Imobiliária'),
        ('outro', 'Outro'),
    ]

    cpf = models.CharField(
        max_length=11,
        unique=True,
        validators=[RegexValidator(regex=r'^[0-9]{11}$', message='CPF deve conter exatamente 11 dígitos numéricos')]
    )
    email = models.EmailField(_('email address'), blank=True, null=True)
    nome = models.CharField(max_length=100, blank=True, null=True)
    quantidade_apartamentos = models.PositiveIntegerField(null=True, blank=True)

    tipo_usuario = models.CharField(
        max_length=20,
        choices=TIPO_USUARIO_CHOICES,
        default='proprietario'
    )

    is_admin_user = models.BooleanField(
        'Usuário Admin',
        default=False,
        help_text='Designa se este usuário tem acesso ao painel administrativo'
    )

    nome_condominio = models.CharField(max_length=100, null=True, blank=True)

    is_verified = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    foto = models.ImageField(upload_to='usuarios/', blank=True, null=True, default='usuarios/avatar.png')

    USERNAME_FIELD = 'cpf'
    REQUIRED_FIELDS = []

    objects = UsuarioManager()

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'

    def __str__(self):
        return self.get_full_name()

    def get_full_name(self):
        return self.nome or self.email.split('@')[0] if self.email else self.cpf

    def get_short_name(self):
        return self.get_full_name()

    @property
    def is_admin(self):
        return self.is_admin_user or self.is_superuser or self.tipo_usuario == 'outro'

    def get_apartamentos_display(self):
        return ", ".join([
            f"Apto {apt.numero_apartamento} (Bloco {apt.bloco or '-'})"
            for apt in self.apartamentos.all()
        ])
    get_apartamentos_display.short_description = "Apartamentos"

    def save(self, *args, **kwargs):
        creating = self._state.adding
        super().save(*args, **kwargs)

        # Redimensionar a imagem
        if self.foto and self.foto.name != 'usuarios/avatar.png':
            try:
                img = Image.open(self.foto.path)
                img.thumbnail((50, 50))
                img.save(self.foto.path)
            except:
                pass

        # Criar apartamentos automaticamente ao salvar pela primeira vez
        if creating and self.quantidade_apartamentos:
            for i in range(1, self.quantidade_apartamentos + 1):
                Apartamento.objects.get_or_create(
                    usuario=self,
                    numero_apartamento=str(i),
                    defaults={'bloco': 'A'}
                )

# models.py
class Apartamento(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='apartamentos')
    numero_apartamento = models.CharField(max_length=10)
    bloco = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        if self.bloco:
            return f"Apto {self.numero_apartamento} - Bloco {self.bloco}"
        return f"Apto {self.numero_apartamento}"


class Chamado(models.Model):
    STATUS_CHOICES = [
        ('A', 'Aberto'),
        ('E', 'Em andamento'),
        ('F', 'Finalizado'),
        ('R', 'Reaberto'),
    ]

    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="chamados")
    titulo = models.CharField(max_length=100)
    descricao = models.TextField()
    data_abertura = models.DateTimeField(auto_now_add=True)
    data_fechamento = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    apartamento = models.ForeignKey(Apartamento, on_delete=models.CASCADE, related_name="chamados", null=True, blank=True)

    def __str__(self):
        return f"{self.titulo} - {self.get_status_display()}"

    class Meta:
        verbose_name = 'Chamado'
        verbose_name_plural = 'Chamados'

class MensagemChamado(models.Model):
    chamado = models.ForeignKey(Chamado, on_delete=models.CASCADE, related_name='mensagens')
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    mensagem = models.TextField()
    data_envio = models.DateTimeField(auto_now_add=True)
    is_resposta_tecnica = models.BooleanField(default=False)

    def __str__(self):
        return f"Mensagem #{self.id} - {self.chamado.titulo[:20]}"

    class Meta:
        verbose_name = 'Mensagem de Chamado'
        verbose_name_plural = 'Mensagens de Chamado'
        ordering = ['data_envio']

class Pagamento(models.Model):
    METODO_CHOICES = [
        ('P', 'PIX'),
        ('C', 'Cartão de Crédito'),
        ('F', 'Funcionário'),
    ]

    STATUS_CHOICES = [
        ('P', 'Pendente'),
        ('A', 'Aprovado'),
        ('R', 'Recusado'),
    ]

    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    descricao = models.CharField(max_length=200)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    data_vencimento = models.DateField()
    data_pagamento = models.DateField(null=True, blank=True)
    metodo_pagamento = models.CharField(max_length=1, choices=METODO_CHOICES, null=True, blank=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='P')
    comprovante = models.FileField(upload_to='comprovantes/', null=True, blank=True)

    def __str__(self):
        return f"Pagamento #{self.id} - {self.usuario.email if self.usuario.email else 'Usuário'}"

    class Meta:
        verbose_name = 'Pagamento'
        verbose_name_plural = 'Pagamentos'
        ordering = ['-data_vencimento']

class ClienteProxy(Usuario):
    class Meta:
        proxy = True
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'

class AdministradorProxy(Usuario):
    class Meta:
        proxy = True
        verbose_name = 'Administrador'
        verbose_name_plural = 'Administradores'

class Comunicado(models.Model):
    titulo = models.CharField(max_length=200)
    conteudo = models.TextField()
    imagem = models.ImageField(upload_to='comunicados/', blank=True, null=True)
    data_publicacao = models.DateTimeField(auto_now_add=True)
    autor = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True)
    publicado = models.BooleanField(default=True)

    autor = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Síndico Responsável",
        limit_choices_to={'tipo_usuario': 'sindico'}  # Filtra apenas síndicos
    )
    
    def get_autor_nome(self):
        return self.autor.nome if self.autor else "Não definido"
    get_autor_nome.short_description = "Síndico"

    class Meta:
        verbose_name = 'Comunicado'
        verbose_name_plural = 'Comunicados'
        ordering = ['-data_publicacao']
    
    @property
    def nome_autor(self):
        return self.autor.nome if self.autor else "Não definido"

    def __str__(self):
        return f"{self.titulo} (por {self.autor.nome if self.autor else 'sem autor'})"

    def get_absolute_url(self):
        return reverse('core:detalhe_comunicado', args=[str(self.id)])