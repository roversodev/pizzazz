# Generated by Django 4.2.16 on 2025-01-23 16:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0005_empresa_ativo'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='papel_adm',
            field=models.CharField(choices=[('Master', 'Master'), ('Atendente', 'Atendente'), ('Gerente', 'Gerente')], max_length=50, null=True),
        ),
    ]
