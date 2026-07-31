from django.contrib import admin
from .models import Project

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'developer', 'governorate', 'city', 'status', 'created_at')
    list_filter = ('type', 'status', 'governorate')
    search_fields = ('name', 'slug', 'city', 'district')
    prepopulated_fields = {'slug': ('name',)}
