# Generated by Django 4.2.21 on 2025-05-25 07:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_usuario_foto'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usuario',
            name='foto',
            field=models.ImageField(blank=True, default='usuarios/default.png', null=True, upload_to='usuarios/'),
        ),
    ]
