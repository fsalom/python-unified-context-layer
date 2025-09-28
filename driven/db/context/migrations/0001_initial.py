"""Initial migration for UCL context models"""
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='ProjectContextDBO',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('version', models.CharField(blank=True, max_length=50, null=True)),
                ('repository_url', models.URLField(blank=True, null=True)),
                ('technologies', models.JSONField(blank=True, default=list)),
                ('team_members', models.JSONField(blank=True, default=list)),
                ('documentation_urls', models.JSONField(blank=True, default=list)),
                ('global_context', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('last_updated', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'ucl_project_contexts',
                'ordering': ['-last_updated'],
            },
        ),
        migrations.CreateModel(
            name='DomainContextDBO',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('domain_type', models.CharField(choices=[
                    ('frontend', 'Frontend'),
                    ('backend', 'Backend'),
                    ('design', 'Design'),
                    ('infrastructure', 'Infrastructure'),
                    ('testing', 'Testing'),
                    ('documentation', 'Documentation'),
                    ('data', 'Data'),
                    ('mobile', 'Mobile'),
                    ('desktop', 'Desktop'),
                    ('api', 'API'),
                    ('database', 'Database'),
                    ('security', 'Security'),
                    ('devops', 'DevOps'),
                    ('analytics', 'Analytics'),
                    ('other', 'Other'),
                ], max_length=50)),
                ('technologies', models.JSONField(blank=True, default=list)),
                ('file_patterns', models.JSONField(blank=True, default=list)),
                ('key_files', models.JSONField(blank=True, default=list)),
                ('apis', models.JSONField(blank=True, default=list)),
                ('dependencies', models.JSONField(blank=True, default=list)),
                ('conventions', models.JSONField(blank=True, default=dict)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('last_updated', models.DateTimeField(auto_now=True)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='domains', to='context.projectcontextdbo')),
            ],
            options={
                'db_table': 'ucl_domain_contexts',
                'ordering': ['domain_type'],
            },
        ),
        migrations.CreateModel(
            name='AISessionDBO',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('ai_type', models.CharField(choices=[
                    ('claude', 'Claude'),
                    ('chatgpt', 'ChatGPT'),
                    ('copilot', 'GitHub Copilot'),
                    ('bard', 'Google Bard'),
                    ('custom', 'Custom AI'),
                    ('other', 'Other'),
                ], max_length=50)),
                ('ai_instance_id', models.CharField(blank=True, max_length=255)),
                ('session_start', models.DateTimeField(default=django.utils.timezone.now)),
                ('session_end', models.DateTimeField(blank=True, null=True)),
                ('domains_accessed', models.JSONField(blank=True, default=list)),
                ('queries_count', models.PositiveIntegerField(default=0)),
                ('last_query', models.TextField(blank=True, null=True)),
                ('context_hash', models.CharField(blank=True, max_length=64, null=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ai_sessions', to='context.projectcontextdbo')),
            ],
            options={
                'db_table': 'ucl_ai_sessions',
                'ordering': ['-session_start'],
            },
        ),
        migrations.CreateModel(
            name='ContextQueryDBO',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('query_text', models.TextField()),
                ('domains_filter', models.JSONField(blank=True, default=list)),
                ('response_format', models.CharField(choices=[
                    ('structured', 'Structured'),
                    ('markdown', 'Markdown'),
                    ('json', 'JSON'),
                    ('text', 'Plain Text'),
                ], default='structured', max_length=20)),
                ('include_history', models.BooleanField(default=False)),
                ('max_results', models.PositiveIntegerField(default=100)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('ai_session', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='queries', to='context.aisessiondbo')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='queries', to='context.projectcontextdbo')),
            ],
            options={
                'db_table': 'ucl_context_queries',
                'ordering': ['-timestamp'],
            },
        ),
        migrations.CreateModel(
            name='ContextResponseDBO',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('results', models.JSONField(blank=True, default=list)),
                ('domains_found', models.JSONField(blank=True, default=list)),
                ('total_results', models.PositiveIntegerField(default=0)),
                ('processing_time_ms', models.FloatField(default=0.0)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='responses', to='context.projectcontextdbo')),
                ('query', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='response', to='context.contextquerydbo')),
            ],
            options={
                'db_table': 'ucl_context_responses',
                'ordering': ['-timestamp'],
            },
        ),
        migrations.CreateModel(
            name='ContextSubscriptionDBO',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('domains', models.JSONField(blank=True, default=list)),
                ('webhook_url', models.URLField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('last_notified', models.DateTimeField(blank=True, null=True)),
                ('ai_session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subscriptions', to='context.aisessiondbo')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subscriptions', to='context.projectcontextdbo')),
            ],
            options={
                'db_table': 'ucl_context_subscriptions',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ContextIndexDBO',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('file_path', models.TextField()),
                ('file_hash', models.CharField(max_length=64)),
                ('content_type', models.CharField(max_length=50)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('indexed_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('last_modified', models.DateTimeField()),
                ('domain', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='indices', to='context.domaincontextdbo')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='indices', to='context.projectcontextdbo')),
            ],
            options={
                'db_table': 'ucl_context_indices',
                'ordering': ['-indexed_at'],
            },
        ),
        # Add indexes
        migrations.AddIndex(
            model_name='projectcontextdbo',
            index=models.Index(fields=['name'], name='ucl_project_contexts_name_idx'),
        ),
        migrations.AddIndex(
            model_name='projectcontextdbo',
            index=models.Index(fields=['last_updated'], name='ucl_project_contexts_last_updated_idx'),
        ),
        migrations.AddIndex(
            model_name='domaincontextdbo',
            index=models.Index(fields=['project', 'domain_type'], name='ucl_domain_contexts_project_domain_idx'),
        ),
        migrations.AddIndex(
            model_name='domaincontextdbo',
            index=models.Index(fields=['domain_type'], name='ucl_domain_contexts_domain_type_idx'),
        ),
        migrations.AddIndex(
            model_name='domaincontextdbo',
            index=models.Index(fields=['last_updated'], name='ucl_domain_contexts_last_updated_idx'),
        ),
        migrations.AddIndex(
            model_name='aisessiondbo',
            index=models.Index(fields=['project', 'ai_type'], name='ucl_ai_sessions_project_ai_type_idx'),
        ),
        migrations.AddIndex(
            model_name='aisessiondbo',
            index=models.Index(fields=['session_start'], name='ucl_ai_sessions_session_start_idx'),
        ),
        migrations.AddIndex(
            model_name='aisessiondbo',
            index=models.Index(fields=['session_end'], name='ucl_ai_sessions_session_end_idx'),
        ),
        migrations.AddIndex(
            model_name='aisessiondbo',
            index=models.Index(fields=['ai_instance_id'], name='ucl_ai_sessions_ai_instance_id_idx'),
        ),
        migrations.AddIndex(
            model_name='contextquerydbo',
            index=models.Index(fields=['project', 'timestamp'], name='ucl_context_queries_project_timestamp_idx'),
        ),
        migrations.AddIndex(
            model_name='contextquerydbo',
            index=models.Index(fields=['ai_session'], name='ucl_context_queries_ai_session_idx'),
        ),
        migrations.AddIndex(
            model_name='contextresponsedbo',
            index=models.Index(fields=['project', 'timestamp'], name='ucl_context_responses_project_timestamp_idx'),
        ),
        migrations.AddIndex(
            model_name='contextresponsedbo',
            index=models.Index(fields=['query'], name='ucl_context_responses_query_idx'),
        ),
        migrations.AddIndex(
            model_name='contextresponsedbo',
            index=models.Index(fields=['processing_time_ms'], name='ucl_context_responses_processing_time_idx'),
        ),
        migrations.AddIndex(
            model_name='contextsubscriptiondbo',
            index=models.Index(fields=['project', 'is_active'], name='ucl_context_subscriptions_project_active_idx'),
        ),
        migrations.AddIndex(
            model_name='contextsubscriptiondbo',
            index=models.Index(fields=['ai_session'], name='ucl_context_subscriptions_ai_session_idx'),
        ),
        migrations.AddIndex(
            model_name='contextindexdbo',
            index=models.Index(fields=['project', 'file_path'], name='ucl_context_indices_project_file_path_idx'),
        ),
        migrations.AddIndex(
            model_name='contextindexdbo',
            index=models.Index(fields=['file_hash'], name='ucl_context_indices_file_hash_idx'),
        ),
        migrations.AddIndex(
            model_name='contextindexdbo',
            index=models.Index(fields=['last_modified'], name='ucl_context_indices_last_modified_idx'),
        ),
        # Add unique constraints
        migrations.AddConstraint(
            model_name='domaincontextdbo',
            constraint=models.UniqueConstraint(fields=['project', 'domain_type'], name='unique_project_domain_type'),
        ),
        migrations.AddConstraint(
            model_name='contextindexdbo',
            constraint=models.UniqueConstraint(fields=['project', 'file_path'], name='unique_project_file_path'),
        ),
    ]