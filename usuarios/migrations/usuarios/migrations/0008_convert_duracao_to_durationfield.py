# usuarios/migrations/0008_convert_duracao_to_durationfield.py
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0007_alter_usuario_email'), # Depende da última migração boa
    ]

    operations = [
        # Primeiro, um passo de RunSQL para converter os dados existentes
        migrations.RunSQL(
            sql="""
                ALTER TABLE usuarios_sessao
                ALTER COLUMN duracao TYPE interval
                USING make_interval(secs => duracao * 60);
            """,
            reverse_sql="""
                ALTER TABLE usuarios_sessao
                ALTER COLUMN duracao TYPE integer
                USING EXTRACT(epoch FROM duracao)::integer / 60;
            """
        ),
        # O Django não vai gerar automaticamente um AlterField para DurationField aqui
        # porque estamos fazendo a conversão via SQL. O próximo makemigrations
        # após ajustar o models.py é que vai adicionar o AlterField se necessário.
    ]