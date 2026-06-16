from django.contrib import admin
from .models import UserProfile, StudyTemplate, TemplateModule, DailyProgress, StudySession, TodoTask

@admin.register(TodoTask)
class TodoTaskAdmin(admin.ModelAdmin):
    list_display = ('content', 'user', 'priority', 'is_done')

@admin.register(StudyTemplate)
class StudyTemplateAdmin(admin.ModelAdmin):
    pass

@admin.register(TemplateModule)
class TemplateModuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'template', 'target_value')

admin.site.register(UserProfile)
admin.site.register(DailyProgress)
admin.site.register(StudySession)