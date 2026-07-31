from django.contrib import admin
from .models import Developer

@admin.register(Developer)
class DeveloperAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_phone', 'verified', 'created_at')
    list_filter = ('verified',)
    search_fields = ('name', 'contact_phone', 'commercial_register_no')
