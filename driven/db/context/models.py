"""Django models for Unified Context Layer"""
from django.db import models
from django.contrib.postgres.fields import JSONField
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
    technologies = JSONField(default=list, blank=True)
    team_members = JSONField(default=list, blank=True)
    documentation_urls = JSONField(default=list, blank=True)
    global_context = JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ucl_project_contexts'
        ordering = ['-last_updated']
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
    technologies = JSONField(default=list, blank=True)
    file_patterns = JSONField(default=list, blank=True)
    key_files = JSONField(default=list, blank=True)
    apis = JSONField(default=list, blank=True)
    dependencies = JSONField(default=list, blank=True)
    conventions = JSONField(default=dict, blank=True)
    metadata = JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ucl_domain_contexts'
        unique_together = [['project', 'domain_type']]
        ordering = ['domain_type']
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

    domains_accessed = JSONField(default=list, blank=True)
    queries_count = models.PositiveIntegerField(default=0)
    last_query = models.TextField(blank=True, null=True)
    context_hash = models.CharField(max_length=64, blank=True, null=True)
    metadata = JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ucl_ai_sessions'
        ordering = ['-session_start']
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
    domains_filter = JSONField(default=list, blank=True)
    response_format = models.CharField(
        max_length=20,
        choices=RESPONSE_FORMATS,
        default='structured'
    )
    include_history = models.BooleanField(default=False)
    max_results = models.PositiveIntegerField(default=100)

    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'ucl_context_queries'
        ordering = ['-timestamp']
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

    results = JSONField(default=list, blank=True)
    domains_found = JSONField(default=list, blank=True)
    total_results = models.PositiveIntegerField(default=0)
    processing_time_ms = models.FloatField(default=0.0)
    metadata = JSONField(default=dict, blank=True)

    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'ucl_context_responses'
        ordering = ['-timestamp']
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

    domains = JSONField(default=list, blank=True)
    webhook_url = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(default=timezone.now)
    last_notified = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'ucl_context_subscriptions'
        ordering = ['-created_at']
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
    metadata = JSONField(default=dict, blank=True)

    indexed_at = models.DateTimeField(default=timezone.now)
    last_modified = models.DateTimeField()

    class Meta:
        db_table = 'ucl_context_indices'
        unique_together = [['project', 'file_path']]
        ordering = ['-indexed_at']
        indexes = [
            models.Index(fields=['project', 'file_path']),
            models.Index(fields=['file_hash']),
            models.Index(fields=['last_modified']),
        ]

    def __str__(self):
        return f"Index: {self.file_path}"