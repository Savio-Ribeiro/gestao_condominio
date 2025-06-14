# Generated by Django 4.2.21 on 2025-05-25 06:22

from django.conf import settings
import django.contrib.auth.models
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Usuario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('email', models.EmailField(max_length=254, unique=True, verbose_name='email address')),
                ('cpf', models.CharField(max_length=14, unique=True)),
                ('tipo_usuario', models.CharField(choices=[('P', 'Proprietário'), ('I', 'Inquilino'), ('M', 'Imobiliária')], max_length=1)),
                ('nome_condominio', models.CharField(max_length=100)),
                ('numero_apartamento', models.CharField(max_length=10)),
                ('foto', models.ImageField(blank=True, null=True, upload_to='usuarios/')),
                ('is_verified', models.BooleanField(default=False)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Chamado',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('apartamento', models.CharField(max_length=10)),
                ('titulo', models.CharField(max_length=100)),
                ('descricao', models.TextField()),
                ('data_abertura', models.DateTimeField(auto_now_add=True)),
                ('data_fechamento', models.DateTimeField(blank=True, null=True)),
                ('status', models.CharField(choices=[('A', 'Aberto'), ('E', 'Em andamento'), ('F', 'Finalizado'), ('R', 'Reaberto')], default='A', max_length=1)),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Pagamento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descricao', models.CharField(max_length=200)),
                ('valor', models.DecimalField(decimal_places=2, max_digits=10)),
                ('data_vencimento', models.DateField()),
                ('data_pagamento', models.DateField(blank=True, null=True)),
                ('metodo_pagamento', models.CharField(blank=True, choices=[('P', 'PIX'), ('C', 'Cartão de Crédito'), ('F', 'Funcionário')], max_length=1, null=True)),
                ('status', models.CharField(choices=[('P', 'Pendente'), ('A', 'Aprovado'), ('R', 'Recusado')], default='P', max_length=1)),
                ('comprovante', models.FileField(blank=True, null=True, upload_to='comprovantes/')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='MensagemChamado',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mensagem', models.TextField()),
                ('data_envio', models.DateTimeField(auto_now_add=True)),
                ('is_resposta_tecnica', models.BooleanField(default=False)),
                ('chamado', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mensagens', to='core.chamado')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['data_envio'],
            },
        ),
    ]
