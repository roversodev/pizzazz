# Generated by Django 4.2.16 on 2024-12-13 16:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0007_remove_ingredientecardapio_unidade_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='ingredientecardapio',
            name='empresa',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='ingredienteCardapio', to='authentication.empresa'),
            preserve_default=False,
        ),
    ]