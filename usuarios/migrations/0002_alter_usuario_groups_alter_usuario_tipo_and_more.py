# Generated by Django 5.1 on 2025-06-18 16:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('usuarios', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usuario',
            name='groups',
            field=models.ManyToManyField(blank=True, related_name='usuarios_groups', related_query_name='usuario', to='auth.group', verbose_name='groups'),
        ),
        migrations.AlterField(
            model_name='usuario',
            name='tipo',
            field=models.CharField(choices=[('terapeuta', 'Terapeuta'), ('paciente', 'Paciente')], default='paciente', max_length=20, verbose_name='Tipo de Usuário'),
        ),
        migrations.AlterField(
            model_name='usuario',
            name='user_permissions',
            field=models.ManyToManyField(blank=True, related_name='usuarios_permissions', related_query_name='usuario', to='auth.permission', verbose_name='user permissions'),
        ),
    ]
