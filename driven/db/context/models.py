"""Django models for Unified Context Layer"""
from django.db import models
from django.core.validators import URLValidator
from django.utils import timezone
import uuid


class ProjectContextDBO(models.Model):
    """Django model for project context"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    version = models.CharField(max_length=50, blank=True, null=True)
    repository_url = models.URLField(
        blank=True, null=True,
        validators=[URLValidator()]
    )
    technologies = models.JSONField(default=list, blank=True)
    team_members = models.JSONField(default=list, blank=True)
    documentation_urls = models.JSONField(default=list, blank=True)
    global_context = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'context'
        db_table = 'ucl_project_contexts'
        ordering = ['-last_updated']
        verbose_name = 'Proyecto'
        verbose_name_plural = 'Proyectos'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['last_updated']),
        ]

    def __str__(self):
        return f"ProjectContext: {self.name}"


class DomainContextDBO(models.Model):
    """Django model for domain context"""
    DOMAIN_TYPES = [
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
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        ProjectContextDBO,
        on_delete=models.CASCADE,
        related_name='domains'
    )
    domain_type = models.CharField(max_length=50, choices=DOMAIN_TYPES)
    technologies = models.JSONField(default=list, blank=True)
    file_patterns = models.JSONField(default=list, blank=True)
    key_files = models.JSONField(default=list, blank=True)
    apis = models.JSONField(default=list, blank=True)
    dependencies = models.JSONField(default=list, blank=True)
    conventions = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'context'
        db_table = 'ucl_domain_contexts'
        unique_together = [['project', 'domain_type']]
        ordering = ['domain_type']
        verbose_name = 'Dominio'
        verbose_name_plural = 'Dominios'
        indexes = [
            models.Index(fields=['project', 'domain_type']),
            models.Index(fields=['domain_type']),
            models.Index(fields=['last_updated']),
        ]

    def __str__(self):
        return f"DomainContext: {self.project.name} - {self.domain_type}"


class AISessionDBO(models.Model):
    """Django model for AI sessions"""
    AI_TYPES = [
        ('claude', 'Claude'),
        ('chatgpt', 'ChatGPT'),
        ('copilot', 'GitHub Copilot'),
        ('bard', 'Google Bard'),
        ('custom', 'Custom AI'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        ProjectContextDBO,
        on_delete=models.CASCADE,
        related_name='ai_sessions'
    )
    ai_type = models.CharField(max_length=50, choices=AI_TYPES)
    ai_instance_id = models.CharField(max_length=255, blank=True)

    session_start = models.DateTimeField(default=timezone.now)
    session_end = models.DateTimeField(blank=True, null=True)

    domains_accessed = models.JSONField(default=list, blank=True)
    queries_count = models.PositiveIntegerField(default=0)
    last_query = models.TextField(blank=True, null=True)
    context_hash = models.CharField(max_length=64, blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'context'
        db_table = 'ucl_ai_sessions'
        ordering = ['-session_start']
        verbose_name = 'Sesión de IA'
        verbose_name_plural = 'Sesiones de IA'
        indexes = [
            models.Index(fields=['project', 'ai_type']),
            models.Index(fields=['session_start']),
            models.Index(fields=['session_end']),
            models.Index(fields=['ai_instance_id']),
        ]

    def __str__(self):
        return f"AISession: {self.ai_type} - {self.project.name}"

    @property
    def is_active(self):
        return self.session_end is None

    @property
    def duration(self):
        if self.session_end:
            return self.session_end - self.session_start
        return timezone.now() - self.session_start


class ContextQueryDBO(models.Model):
    """Django model for context queries"""
    RESPONSE_FORMATS = [
        ('structured', 'Structured'),
        ('markdown', 'Markdown'),
        ('json', 'JSON'),
        ('text', 'Plain Text'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        ProjectContextDBO,
        on_delete=models.CASCADE,
        related_name='queries'
    )
    ai_session = models.ForeignKey(
        AISessionDBO,
        on_delete=models.CASCADE,
        related_name='queries',
        blank=True,
        null=True
    )

    query_text = models.TextField()
    domains_filter = models.JSONField(default=list, blank=True)
    response_format = models.CharField(
        max_length=20,
        choices=RESPONSE_FORMATS,
        default='structured'
    )
    include_history = models.BooleanField(default=False)
    max_results = models.PositiveIntegerField(default=100)

    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        app_label = 'context'
        db_table = 'ucl_context_queries'
        ordering = ['-timestamp']
        verbose_name = 'Consulta'
        verbose_name_plural = 'Consultas'
        indexes = [
            models.Index(fields=['project', 'timestamp']),
            models.Index(fields=['ai_session']),
            models.Index(fields=['query_text']),
        ]

    def __str__(self):
        return f"Query: {self.query_text[:50]}..."


class ContextResponseDBO(models.Model):
    """Django model for context responses"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    query = models.OneToOneField(
        ContextQueryDBO,
        on_delete=models.CASCADE,
        related_name='response'
    )
    project = models.ForeignKey(
        ProjectContextDBO,
        on_delete=models.CASCADE,
        related_name='responses'
    )

    results = models.JSONField(default=list, blank=True)
    domains_found = models.JSONField(default=list, blank=True)
    total_results = models.PositiveIntegerField(default=0)
    processing_time_ms = models.FloatField(default=0.0)
    metadata = models.JSONField(default=dict, blank=True)

    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        app_label = 'context'
        db_table = 'ucl_context_responses'
        ordering = ['-timestamp']
        verbose_name = 'Respuesta'
        verbose_name_plural = 'Respuestas'
        indexes = [
            models.Index(fields=['project', 'timestamp']),
            models.Index(fields=['query']),
            models.Index(fields=['processing_time_ms']),
        ]

    def __str__(self):
        return f"Response: {self.total_results} results"


class ContextSubscriptionDBO(models.Model):
    """Django model for context subscriptions"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        ProjectContextDBO,
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    ai_session = models.ForeignKey(
        AISessionDBO,
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )

    domains = models.JSONField(default=list, blank=True)
    webhook_url = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(default=timezone.now)
    last_notified = models.DateTimeField(blank=True, null=True)

    class Meta:
        app_label = 'context'
        db_table = 'ucl_context_subscriptions'
        ordering = ['-created_at']
        verbose_name = 'Suscripción'
        verbose_name_plural = 'Suscripciones'
        indexes = [
            models.Index(fields=['project', 'is_active']),
            models.Index(fields=['ai_session']),
        ]

    def __str__(self):
        return f"Subscription: {self.ai_session.ai_type} - {self.project.name}"


class ContextIndexDBO(models.Model):
    """Django model for context indexing metadata"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        ProjectContextDBO,
        on_delete=models.CASCADE,
        related_name='indices'
    )
    domain = models.ForeignKey(
        DomainContextDBO,
        on_delete=models.CASCADE,
        related_name='indices',
        blank=True,
        null=True
    )

    file_path = models.TextField()
    file_hash = models.CharField(max_length=64)
    content_type = models.CharField(max_length=50)
    metadata = models.JSONField(default=dict, blank=True)

    indexed_at = models.DateTimeField(default=timezone.now)
    last_modified = models.DateTimeField()

    class Meta:
        app_label = 'context'
        db_table = 'ucl_context_indices'
        unique_together = [['project', 'file_path']]
        ordering = ['-indexed_at']
        verbose_name = 'Índice de Archivo'
        verbose_name_plural = 'Índices de Archivos'
        indexes = [
            models.Index(fields=['project', 'file_path']),
            models.Index(fields=['file_hash']),
            models.Index(fields=['last_modified']),
        ]

    def __str__(self):
        return f"Index: {self.file_path}"


class TechnicalDecisionDBO(models.Model):
    """Django model for Architecture Decision Records (ADRs)"""
    STATUS_CHOICES = [
        ('proposed', 'Propuesta'),
        ('accepted', 'Aceptada'),
        ('rejected', 'Rechazada'),
        ('deprecated', 'Deprecada'),
        ('superseded', 'Reemplazada'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        ProjectContextDBO,
        on_delete=models.CASCADE,
        related_name='technical_decisions'
    )

    title = models.CharField(max_length=255)
    decision_number = models.PositiveIntegerField()  # ADR-001, ADR-002, etc.
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='proposed')

    # Contexto y problema
    context = models.TextField(help_text="¿Qué circunstancias motivaron esta decisión?")
    problem = models.TextField(help_text="¿Qué problema estamos resolviendo?")

    # Decisión y consecuencias
    decision = models.TextField(help_text="¿Qué decidimos hacer?")
    rationale = models.TextField(help_text="¿Por qué elegimos esta opción?")
    alternatives_considered = models.JSONField(
        default=list,
        blank=True,
        help_text="Alternativas que se consideraron"
    )
    consequences = models.TextField(
        blank=True,
        help_text="¿Qué implicaciones tiene esta decisión?"
    )

    # Metadata
    decided_by = models.JSONField(default=list, blank=True, help_text="Quién tomó la decisión")
    tags = models.JSONField(default=list, blank=True)
    related_decisions = models.ManyToManyField('self', blank=True, symmetrical=False)
    superseded_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='supersedes'
    )

    created_at = models.DateTimeField(default=timezone.now)
    decided_at = models.DateTimeField(blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'context'
        db_table = 'ucl_technical_decisions'
        ordering = ['-decision_number']
        unique_together = [['project', 'decision_number']]
        verbose_name = 'Decisión Técnica (ADR)'
        verbose_name_plural = 'Decisiones Técnicas (ADRs)'
        indexes = [
            models.Index(fields=['project', 'status']),
            models.Index(fields=['decision_number']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"ADR-{self.decision_number:03d}: {self.title}"


class ClientRequirementDBO(models.Model):
    """Django model for client requirements and features"""
    REQUIREMENT_TYPES = [
        ('feature', 'Feature'),
        ('bug', 'Bug'),
        ('enhancement', 'Enhancement'),
        ('task', 'Task'),
        ('epic', 'Epic'),
    ]

    PRIORITY_LEVELS = [
        ('critical', 'Crítica'),
        ('high', 'Alta'),
        ('medium', 'Media'),
        ('low', 'Baja'),
    ]

    STATUS_CHOICES = [
        ('backlog', 'Backlog'),
        ('analysis', 'En Análisis'),
        ('ready', 'Lista'),
        ('in_progress', 'En Progreso'),
        ('review', 'En Revisión'),
        ('testing', 'En Testing'),
        ('done', 'Completada'),
        ('blocked', 'Bloqueada'),
        ('cancelled', 'Cancelada'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        ProjectContextDBO,
        on_delete=models.CASCADE,
        related_name='requirements'
    )

    requirement_number = models.CharField(max_length=50, help_text="Ej: REQ-001, US-123")
    title = models.CharField(max_length=255)
    description = models.TextField()
    requirement_type = models.CharField(max_length=20, choices=REQUIREMENT_TYPES)

    # Cliente y negocio
    client_request = models.TextField(blank=True, help_text="Solicitud original del cliente")
    business_value = models.TextField(blank=True, help_text="Valor de negocio esperado")
    acceptance_criteria = models.JSONField(
        default=list,
        blank=True,
        help_text="Criterios de aceptación"
    )

    # Priorización
    priority = models.CharField(max_length=20, choices=PRIORITY_LEVELS, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='backlog')

    # Planificación
    estimated_effort = models.CharField(max_length=50, blank=True, help_text="Ej: 3 días, 2 sprints")
    assigned_to = models.JSONField(default=list, blank=True)
    domains = models.ManyToManyField(DomainContextDBO, blank=True, related_name='requirements')

    # Relaciones
    parent_requirement = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sub_requirements'
    )
    blocked_by = models.ManyToManyField('self', blank=True, symmetrical=False)
    related_decisions = models.ManyToManyField(TechnicalDecisionDBO, blank=True)

    # Metadata
    tags = models.JSONField(default=list, blank=True)
    attachments = models.JSONField(default=list, blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        app_label = 'context'
        db_table = 'ucl_client_requirements'
        ordering = ['-created_at']
        unique_together = [['project', 'requirement_number']]
        verbose_name = 'Requisito del Cliente'
        verbose_name_plural = 'Requisitos del Cliente'
        indexes = [
            models.Index(fields=['project', 'status']),
            models.Index(fields=['requirement_type', 'status']),
            models.Index(fields=['priority']),
        ]

    def __str__(self):
        return f"{self.requirement_number}: {self.title}"


class TeamDocumentationDBO(models.Model):
    """Django model for team documentation and guides"""
    DOC_TYPES = [
        ('guide', 'Guía'),
        ('workflow', 'Workflow'),
        ('tutorial', 'Tutorial'),
        ('reference', 'Referencia'),
        ('runbook', 'Runbook'),
        ('onboarding', 'Onboarding'),
        ('api_doc', 'Documentación API'),
        ('architecture', 'Arquitectura'),
        ('other', 'Otro'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        ProjectContextDBO,
        on_delete=models.CASCADE,
        related_name='documentation'
    )

    title = models.CharField(max_length=255)
    doc_type = models.CharField(max_length=20, choices=DOC_TYPES)
    slug = models.SlugField(max_length=255)

    # Contenido
    content = models.TextField(help_text="Markdown o texto enriquecido")
    summary = models.TextField(blank=True, help_text="Resumen breve")

    # Organización
    category = models.CharField(max_length=100, blank=True)
    tags = models.JSONField(default=list, blank=True)
    related_domains = models.ManyToManyField(DomainContextDBO, blank=True)

    # Control de versiones
    version = models.CharField(max_length=50, default='1.0')
    is_current = models.BooleanField(default=True)
    previous_version = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='next_versions'
    )

    # Metadata
    authors = models.JSONField(default=list, blank=True)
    reviewers = models.JSONField(default=list, blank=True)
    external_url = models.URLField(blank=True, null=True)

    created_at = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)
    last_reviewed = models.DateTimeField(blank=True, null=True)

    class Meta:
        app_label = 'context'
        db_table = 'ucl_team_documentation'
        ordering = ['-last_updated']
        unique_together = [['project', 'slug']]
        verbose_name = 'Documentación del Equipo'
        verbose_name_plural = 'Documentación del Equipo'
        indexes = [
            models.Index(fields=['project', 'doc_type']),
            models.Index(fields=['slug']),
            models.Index(fields=['is_current']),
        ]

    def __str__(self):
        return f"{self.title} (v{self.version})"


class ProjectConventionDBO(models.Model):
    """Django model for project conventions and standards"""
    CONVENTION_TYPES = [
        ('coding_style', 'Estilo de Código'),
        ('naming', 'Nomenclatura'),
        ('git_workflow', 'Workflow Git'),
        ('testing', 'Testing'),
        ('documentation', 'Documentación'),
        ('security', 'Seguridad'),
        ('performance', 'Performance'),
        ('deployment', 'Deployment'),
        ('code_review', 'Code Review'),
        ('other', 'Otro'),
    ]

    ENFORCEMENT_LEVELS = [
        ('required', 'Requerida'),
        ('recommended', 'Recomendada'),
        ('optional', 'Opcional'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        ProjectContextDBO,
        on_delete=models.CASCADE,
        related_name='conventions'
    )

    title = models.CharField(max_length=255)
    convention_type = models.CharField(max_length=20, choices=CONVENTION_TYPES)
    enforcement_level = models.CharField(max_length=20, choices=ENFORCEMENT_LEVELS, default='recommended')

    # Descripción
    description = models.TextField(help_text="Descripción de la convención")
    rationale = models.TextField(blank=True, help_text="Por qué seguimos esta convención")

    # Ejemplos
    examples_good = models.JSONField(
        default=list,
        blank=True,
        help_text="Ejemplos de código/uso correcto"
    )
    examples_bad = models.JSONField(
        default=list,
        blank=True,
        help_text="Ejemplos de qué NO hacer"
    )

    # Aplicabilidad
    applies_to_domains = models.ManyToManyField(DomainContextDBO, blank=True)
    file_patterns = models.JSONField(
        default=list,
        blank=True,
        help_text="Patrones de archivos donde aplica (*.js, *.py, etc)"
    )

    # Automatización
    automated_check = models.BooleanField(default=False)
    tooling = models.JSONField(
        default=dict,
        blank=True,
        help_text="Herramientas que verifican esta convención (ESLint, Prettier, etc)"
    )

    # Metadata
    tags = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'context'
        db_table = 'ucl_project_conventions'
        ordering = ['convention_type', 'title']
        verbose_name = 'Convención del Proyecto'
        verbose_name_plural = 'Convenciones del Proyecto'
        indexes = [
            models.Index(fields=['project', 'convention_type']),
            models.Index(fields=['is_active']),
            models.Index(fields=['enforcement_level']),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_convention_type_display()})"


class BusinessKnowledgeDBO(models.Model):
    """Django model for business domain knowledge and rules"""
    KNOWLEDGE_TYPES = [
        ('business_rule', 'Regla de Negocio'),
        ('process', 'Proceso'),
        ('glossary', 'Glosario'),
        ('workflow', 'Flujo de Trabajo'),
        ('policy', 'Política'),
        ('calculation', 'Cálculo/Fórmula'),
        ('integration', 'Integración Externa'),
        ('constraint', 'Restricción'),
        ('other', 'Otro'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        ProjectContextDBO,
        on_delete=models.CASCADE,
        related_name='business_knowledge'
    )

    title = models.CharField(max_length=255)
    knowledge_type = models.CharField(max_length=20, choices=KNOWLEDGE_TYPES)

    # Contenido
    description = models.TextField(help_text="Descripción detallada")
    business_context = models.TextField(
        blank=True,
        help_text="Contexto de negocio relevante"
    )

    # Detalles específicos
    rules = models.JSONField(
        default=list,
        blank=True,
        help_text="Reglas específicas"
    )
    examples = models.JSONField(
        default=list,
        blank=True,
        help_text="Ejemplos de casos de uso"
    )
    edge_cases = models.JSONField(
        default=list,
        blank=True,
        help_text="Casos especiales o edge cases"
    )

    # Implementación
    implementation_notes = models.TextField(
        blank=True,
        help_text="Notas sobre cómo está implementado"
    )
    code_references = models.JSONField(
        default=list,
        blank=True,
        help_text="Referencias a código que implementa esto"
    )

    # Relaciones
    related_domains = models.ManyToManyField(DomainContextDBO, blank=True)
    related_requirements = models.ManyToManyField(ClientRequirementDBO, blank=True)

    # Metadata
    stakeholders = models.JSONField(
        default=list,
        blank=True,
        help_text="Stakeholders relevantes"
    )
    tags = models.JSONField(default=list, blank=True)
    source = models.CharField(
        max_length=255,
        blank=True,
        help_text="Fuente de esta información"
    )
    is_current = models.BooleanField(default=True)

    created_at = models.DateTimeField(default=timezone.now)
    last_validated = models.DateTimeField(blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'context'
        db_table = 'ucl_business_knowledge'
        ordering = ['knowledge_type', 'title']
        verbose_name = 'Conocimiento de Negocio'
        verbose_name_plural = 'Conocimientos de Negocio'
        indexes = [
            models.Index(fields=['project', 'knowledge_type']),
            models.Index(fields=['is_current']),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_knowledge_type_display()})"