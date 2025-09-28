from django.contrib import admin

from driven.db.users.models import UserDBO


@admin.register(UserDBO)
class UserAdmin(admin.ModelAdmin):
    filter_horizontal = ('departments',)
    list_display = ('id',)
    search_fields = 'id'
