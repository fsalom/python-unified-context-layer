from django.contrib import admin
from driven.db.context.models import (
    ProjectContextDBO,
    DomainContextDBO,
    AISessionDBO,
    ContextQueryDBO,
    ContextResponseDBO,
    ContextSubscriptionDBO,
    ContextIndexDBO,
    TechnicalDecisionDBO,
    ClientRequirementDBO,
    TeamDocumentationDBO,
    ProjectConventionDBO,
    BusinessKnowledgeDBO,
)


@admin.register(ProjectContextDBO)
class ProjectContextAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'version', 'repository_url', 'created_at', 'last_updated')
    search_fields = ['name', 'description', 'repository_url']
    list_filter = ['created_at', 'last_updated']
    readonly_fields = ('id', 'created_at', 'last_updated')
    fieldsets = (
        ('Información del Proyecto', {
            'fields': ('id', 'name', 'description', 'version', 'repository_url')
        }),
        ('Configuración y Equipo', {
            'fields': ('technologies', 'team_members', 'documentation_urls', 'global_context')
        }),
        ('Auditoría', {
            'fields': ('created_at', 'last_updated')
        }),
    )


@admin.register(DomainContextDBO)
class DomainContextAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'domain_type', 'created_at', 'last_updated')
    search_fields = ['project__name', 'domain_type']
    list_filter = ['domain_type', 'created_at', 'last_updated']
    readonly_fields = ('id', 'created_at', 'last_updated')
    autocomplete_fields = ['project']
    fieldsets = (
        ('Dominio del Proyecto', {
            'fields': ('id', 'project', 'domain_type')
        }),
        ('Configuración Técnica', {
            'fields': ('technologies', 'file_patterns', 'key_files', 'apis', 'dependencies', 'conventions', 'metadata')
        }),
        ('Auditoría', {
            'fields': ('created_at', 'last_updated')
        }),
    )


@admin.register(AISessionDBO)
class AISessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'ai_type', 'ai_instance_id', 'session_start', 'session_end', 'queries_count', 'is_active')
    search_fields = ['project__name', 'ai_type', 'ai_instance_id']
    list_filter = ['ai_type', 'session_start', 'session_end']
    readonly_fields = ('id', 'created_at', 'updated_at', 'is_active', 'duration')
    autocomplete_fields = ['project']
    fieldsets = (
        ('Sesión de IA', {
            'fields': ('id', 'project', 'ai_type', 'ai_instance_id')
        }),
        ('Estado de la Sesión', {
            'fields': ('session_start', 'session_end', 'is_active', 'duration')
        }),
        ('Actividad y Métricas', {
            'fields': ('domains_accessed', 'queries_count', 'last_query', 'context_hash', 'metadata')
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(ContextQueryDBO)
class ContextQueryAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'ai_session', 'query_text_short', 'response_format', 'timestamp')
    search_fields = ['project__name', 'query_text']
    list_filter = ['response_format', 'timestamp', 'include_history']
    readonly_fields = ('id', 'timestamp')
    autocomplete_fields = ['project', 'ai_session']
    fieldsets = (
        ('Consulta de Contexto', {
            'fields': ('id', 'project', 'ai_session', 'query_text', 'timestamp')
        }),
        ('Configuración de Búsqueda', {
            'fields': ('domains_filter', 'response_format', 'include_history', 'max_results')
        }),
    )

    def query_text_short(self, obj):
        return obj.query_text[:50] + '...' if len(obj.query_text) > 50 else obj.query_text
    query_text_short.short_description = 'Consulta'


@admin.register(ContextResponseDBO)
class ContextResponseAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'query', 'total_results', 'processing_time_ms', 'timestamp')
    search_fields = ['project__name', 'query__query_text']
    list_filter = ['timestamp', 'processing_time_ms']
    readonly_fields = ('id', 'timestamp')
    autocomplete_fields = ['project', 'query']
    fieldsets = (
        ('Respuesta de Contexto', {
            'fields': ('id', 'project', 'query', 'timestamp')
        }),
        ('Resultados y Métricas', {
            'fields': ('results', 'domains_found', 'total_results', 'processing_time_ms', 'metadata')
        }),
    )


@admin.register(ContextSubscriptionDBO)
class ContextSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'ai_session', 'webhook_url', 'is_active', 'created_at', 'last_notified')
    search_fields = ['project__name', 'ai_session__ai_type', 'webhook_url']
    list_filter = ['is_active', 'created_at', 'last_notified']
    readonly_fields = ('id', 'created_at')
    autocomplete_fields = ['project', 'ai_session']
    fieldsets = (
        ('Suscripción de Webhooks', {
            'fields': ('id', 'project', 'ai_session')
        }),
        ('Configuración de Notificaciones', {
            'fields': ('domains', 'webhook_url', 'is_active')
        }),
        ('Auditoría', {
            'fields': ('created_at', 'last_notified')
        }),
    )


@admin.register(ContextIndexDBO)
class ContextIndexAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'domain', 'file_path_short', 'content_type', 'file_hash', 'indexed_at', 'last_modified')
    search_fields = ['project__name', 'file_path', 'file_hash', 'content_type']
    list_filter = ['content_type', 'indexed_at', 'last_modified']
    readonly_fields = ('id', 'indexed_at')
    autocomplete_fields = ['project', 'domain']
    fieldsets = (
        ('Índice de Archivos', {
            'fields': ('id', 'project', 'domain')
        }),
        ('Información del Archivo', {
            'fields': ('file_path', 'file_hash', 'content_type', 'metadata')
        }),
        ('Auditoría', {
            'fields': ('indexed_at', 'last_modified')
        }),
    )

    def file_path_short(self, obj):
        return obj.file_path[:80] + '...' if len(obj.file_path) > 80 else obj.file_path
    file_path_short.short_description = 'Ruta del Archivo'


@admin.register(TechnicalDecisionDBO)
class TechnicalDecisionAdmin(admin.ModelAdmin):
    list_display = ('decision_number_formatted', 'title', 'project', 'status', 'decided_at', 'last_updated')
    search_fields = ['title', 'context', 'decision', 'problem']
    list_filter = ['status', 'decided_at', 'created_at']
    readonly_fields = ('id', 'created_at', 'last_updated')
    autocomplete_fields = ['project', 'superseded_by']
    filter_horizontal = ('related_decisions',)
    fieldsets = (
        ('Identificación', {
            'fields': ('id', 'project', 'decision_number', 'title', 'status')
        }),
        ('Contexto y Problema', {
            'fields': ('context', 'problem')
        }),
        ('Decisión', {
            'fields': ('decision', 'rationale', 'alternatives_considered', 'consequences')
        }),
        ('Metadatos', {
            'fields': ('decided_by', 'tags', 'related_decisions', 'superseded_by')
        }),
        ('Auditoría', {
            'fields': ('created_at', 'decided_at', 'last_updated')
        }),
    )

    def decision_number_formatted(self, obj):
        return f"ADR-{obj.decision_number:03d}"
    decision_number_formatted.short_description = 'Número'
    decision_number_formatted.admin_order_field = 'decision_number'


@admin.register(ClientRequirementDBO)
class ClientRequirementAdmin(admin.ModelAdmin):
    list_display = ('requirement_number', 'title', 'requirement_type', 'priority', 'status', 'created_at')
    search_fields = ['requirement_number', 'title', 'description', 'client_request']
    list_filter = ['requirement_type', 'priority', 'status', 'created_at']
    readonly_fields = ('id', 'created_at', 'updated_at', 'completed_at')
    autocomplete_fields = ['project', 'parent_requirement']
    filter_horizontal = ('domains', 'blocked_by', 'related_decisions')
    fieldsets = (
        ('Identificación', {
            'fields': ('id', 'project', 'requirement_number', 'title', 'requirement_type')
        }),
        ('Descripción', {
            'fields': ('description', 'client_request', 'business_value', 'acceptance_criteria')
        }),
        ('Gestión', {
            'fields': ('priority', 'status', 'estimated_effort', 'assigned_to')
        }),
        ('Relaciones', {
            'fields': ('domains', 'parent_requirement', 'blocked_by', 'related_decisions')
        }),
        ('Metadatos', {
            'fields': ('tags', 'attachments', 'notes')
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at', 'completed_at')
        }),
    )


@admin.register(TeamDocumentationDBO)
class TeamDocumentationAdmin(admin.ModelAdmin):
    list_display = ('title', 'doc_type', 'category', 'version', 'is_current', 'last_updated')
    search_fields = ['title', 'summary', 'content', 'slug']
    list_filter = ['doc_type', 'is_current', 'category', 'last_updated']
    readonly_fields = ('id', 'created_at', 'last_updated')
    autocomplete_fields = ['project', 'previous_version']
    filter_horizontal = ('related_domains',)
    prepopulated_fields = {'slug': ('title',)}
    fieldsets = (
        ('Identificación', {
            'fields': ('id', 'project', 'title', 'slug', 'doc_type')
        }),
        ('Contenido', {
            'fields': ('summary', 'content')
        }),
        ('Organización', {
            'fields': ('category', 'tags', 'related_domains')
        }),
        ('Versiones', {
            'fields': ('version', 'is_current', 'previous_version')
        }),
        ('Metadatos', {
            'fields': ('authors', 'reviewers', 'external_url')
        }),
        ('Auditoría', {
            'fields': ('created_at', 'last_updated', 'last_reviewed')
        }),
    )


@admin.register(ProjectConventionDBO)
class ProjectConventionAdmin(admin.ModelAdmin):
    list_display = ('title', 'convention_type', 'enforcement_level', 'automated_check', 'is_active', 'last_updated')
    search_fields = ['title', 'description', 'rationale']
    list_filter = ['convention_type', 'enforcement_level', 'automated_check', 'is_active']
    readonly_fields = ('id', 'created_at', 'last_updated')
    autocomplete_fields = ['project']
    filter_horizontal = ('applies_to_domains',)
    fieldsets = (
        ('Identificación', {
            'fields': ('id', 'project', 'title', 'convention_type', 'enforcement_level', 'is_active')
        }),
        ('Descripción', {
            'fields': ('description', 'rationale')
        }),
        ('Ejemplos', {
            'fields': ('examples_good', 'examples_bad')
        }),
        ('Aplicabilidad', {
            'fields': ('applies_to_domains', 'file_patterns')
        }),
        ('Automatización', {
            'fields': ('automated_check', 'tooling')
        }),
        ('Metadatos', {
            'fields': ('tags',)
        }),
        ('Auditoría', {
            'fields': ('created_at', 'last_updated')
        }),
    )


@admin.register(BusinessKnowledgeDBO)
class BusinessKnowledgeAdmin(admin.ModelAdmin):
    list_display = ('title', 'knowledge_type', 'is_current', 'last_validated', 'last_updated')
    search_fields = ['title', 'description', 'business_context']
    list_filter = ['knowledge_type', 'is_current', 'last_validated']
    readonly_fields = ('id', 'created_at', 'last_updated')
    autocomplete_fields = ['project']
    filter_horizontal = ('related_domains', 'related_requirements')
    fieldsets = (
        ('Identificación', {
            'fields': ('id', 'project', 'title', 'knowledge_type', 'is_current')
        }),
        ('Contenido', {
            'fields': ('description', 'business_context')
        }),
        ('Detalles', {
            'fields': ('rules', 'examples', 'edge_cases')
        }),
        ('Implementación', {
            'fields': ('implementation_notes', 'code_references')
        }),
        ('Relaciones', {
            'fields': ('related_domains', 'related_requirements')
        }),
        ('Metadatos', {
            'fields': ('stakeholders', 'tags', 'source')
        }),
        ('Auditoría', {
            'fields': ('created_at', 'last_validated', 'last_updated')
        }),
    )
