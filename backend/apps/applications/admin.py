from django.contrib import admin
from .models import Application

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'project', 'status', 'service_fee', 'paid', 'submitted_at', 'created_at')
    list_filter = ('status', 'paid')
    search_fields = ('user__phone', 'user__full_name', 'project__name')
