from django.contrib import admin

from driven.db.users.models import UserDBO, DepartmentDBO


@admin.register(UserDBO)
class UserAdmin(admin.ModelAdmin):
    filter_horizontal = ('departments',)
    list_display = ('id', 'email', 'first_name', 'last_name', 'is_active')
    search_fields = ['id', 'email', 'first_name', 'last_name']
    list_filter = ['is_active']


@admin.register(DepartmentDBO)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created', 'modified')
    search_fields = ['name', 'description']
    list_filter = ['created', 'modified']
    readonly_fields = ('created', 'modified')
