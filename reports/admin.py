from django.contrib import admin
from django.contrib import auth

from . import models


admin.site.site_header = "QA - reports / admin"


class PermissionsInline(admin.TabularInline):
    model = models.Permission
    extra = 1
    verbose_name_plural = "Permissions"


class UserAdmin(auth.admin.UserAdmin):
    inlines = (PermissionsInline,)
    list_display = ('username', 'email', 'is_superuser')
    readonly_fields = ('last_login', 'date_joined', 'groups')
    list_filter = ('is_superuser', 'is_active')
    fieldsets = (
        (None, {
            'fields': ('username', 'password', 'email', 'first_name',
                       'last_name', 'last_login', 'date_joined')
        }),
        ('Access rights', {'fields': ('groups', 'is_active', 'is_superuser')}),
    )

admin.site.unregister(auth.models.Group)
admin.site.unregister(auth.models.User)
admin.site.register(auth.models.User, UserAdmin)


class DefinitionAdmin(admin.ModelAdmin):
    list_display = ['name']
admin.site.register(models.Definition, DefinitionAdmin)


class TestExecutionAdmin(admin.ModelAdmin):
    list_display = ['build_id', 'board', 'tree', 'branch',
                    'kernel', 'defconfig', 'arch', 'created_at']
admin.site.register(models.TestExecution, TestExecutionAdmin)


class TestJobAdmin(admin.ModelAdmin):
    list_display = ['id', 'status', 'completed', 'created_at']
admin.site.register(models.TestJob, TestJobAdmin)
