# Generated by Django 4.2.21 on 2025-05-27 13:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_alter_usuario_foto'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuario',
            name='bloco',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='usuario',
            name='foto',
            field=models.ImageField(blank=True, default='media/default.png', null=True, upload_to='media/'),
        ),
    ]
