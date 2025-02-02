# Generated by Django 4.2.16 on 2025-01-14 13:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='EnderecoPedido',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cep', models.CharField(max_length=9)),
                ('endereco', models.CharField(max_length=255)),
                ('numero', models.IntegerField(null=True)),
                ('complemento', models.CharField(blank=True, max_length=255, null=True)),
                ('bairro', models.CharField(max_length=255)),
                ('estado', models.CharField(max_length=255)),
                ('municipio', models.CharField(max_length=255)),
                ('pedido', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='endereco_pedido', to='authentication.pedido')),
            ],
        ),
    ]
