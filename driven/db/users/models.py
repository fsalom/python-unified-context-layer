from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel


class DepartmentDBO(TimeStampedModel):
    """Department model"""
    name = models.CharField(_('name'), max_length=150)
    description = models.TextField(_('description'), blank=True)

    class Meta:
        app_label = 'users'
        verbose_name = _("Department")
        verbose_name_plural = _("Departments")

    def __str__(self):
        return self.name


class UserDBO(TimeStampedModel):
    """DISCLAIMER: This is a sample class. A UserDBO model must implement Django's User models"""

    first_name = models.CharField(_('first name'), max_length=150, blank=True)
    last_name = models.CharField(_('last name'), max_length=150, blank=True)
    email = models.EmailField()
    departments = models.ManyToManyField(
        "DepartmentDBO",
        related_name='users',
    )
    is_active = models.BooleanField(_('active'), default=True)

    class Meta:
        app_label = 'users'
        verbose_name = _("User")
        verbose_name_plural = _("Users")

    def __str__(self):
        return self.email
