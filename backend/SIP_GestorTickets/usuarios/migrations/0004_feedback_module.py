# Generated manually for the feedback module.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0003_remove_usuario_domicilio_remove_usuario_pais_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='usuario',
            name='rol',
            field=models.CharField(
                choices=[
                    ('admin_cliente', 'Administrador de Empresa'),
                    ('cliente', 'Cliente'),
                    ('soporte', 'Soporte'),
                    ('jefe', 'Jefe de Soporte'),
                    ('platform_admin', 'Administrador de Plataforma'),
                ],
                max_length=20,
            ),
        ),
        migrations.CreateModel(
            name='FeedbackPlatform',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('rating', models.PositiveSmallIntegerField()),
                ('comment', models.TextField(blank=True, null=True)),
                (
                    'category',
                    models.CharField(
                        choices=[
                            ('BUG', 'Bug'),
                            ('MEJORA', 'Sugerencia de mejora'),
                            ('UX_UI', 'UX/UI'),
                            ('RENDIMIENTO', 'Rendimiento'),
                            ('FUNCIONALIDAD', 'Funcionalidad faltante'),
                            ('OTRO', 'Otro'),
                        ],
                        default='OTRO',
                        max_length=20,
                    ),
                ),
                ('is_critical', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                (
                    'ticket',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='feedback_plataforma',
                        to='usuarios.infoticket',
                    ),
                ),
                (
                    'user',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='feedback_plataforma_realizado',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'db_table': 'feedback_platform',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='FeedbackService',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('rating', models.PositiveSmallIntegerField()),
                ('comment', models.TextField(blank=True, null=True)),
                ('is_critical', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                (
                    'technician',
                    models.ForeignKey(
                        blank=True,
                        limit_choices_to={'rol': 'soporte'},
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='feedback_servicio_recibido',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    'ticket',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='feedback_servicio',
                        to='usuarios.infoticket',
                    ),
                ),
                (
                    'user',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='feedback_servicio_realizado',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'db_table': 'feedback_service',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='FeedbackSupportInternal',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                (
                    'difficulty',
                    models.CharField(
                        choices=[('BAJA', 'Baja'), ('MEDIA', 'Media'), ('ALTA', 'Alta')],
                        max_length=10,
                    ),
                ),
                ('comment', models.TextField(blank=True, null=True)),
                ('problems_found', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                (
                    'technician',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='feedback_interno_realizado',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    'ticket',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='feedback_interno_soporte',
                        to='usuarios.infoticket',
                    ),
                ),
            ],
            options={
                'db_table': 'feedback_support_internal',
                'ordering': ['-created_at'],
            },
        ),
    ]
