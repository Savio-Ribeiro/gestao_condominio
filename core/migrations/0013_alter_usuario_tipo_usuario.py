# Generated by Django 5.2.1 on 2025-05-29 19:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_chamado_apartamento'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usuario',
            name='tipo_usuario',
            field=models.CharField(choices=[('sindico', 'Síndico'), ('proprietario', 'Proprietário'), ('inquilino', 'Inquilino'), ('imobiliaria', 'Imobiliária'), ('outro', 'Outro')], default='proprietario', max_length=20),
        ),
    ]
