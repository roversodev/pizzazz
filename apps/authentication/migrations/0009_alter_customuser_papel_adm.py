# Generated by Django 4.2.16 on 2025-01-23 17:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0008_customuser_is_adm'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='papel_adm',
            field=models.CharField(choices=[('Master', 'Master'), ('Atendente', 'Atendente'), ('Gerente', 'Gerente')], max_length=50, null=True),
        ),
    ]
