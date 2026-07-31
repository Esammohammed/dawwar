import uuid
from django.db import models

class Developer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    commercial_register_no = models.CharField(max_length=50, blank=True, null=True)
    contact_phone = models.CharField(max_length=20)
    contact_email = models.EmailField(max_length=254, blank=True, null=True)
    logo = models.CharField(max_length=500, blank=True, null=True)
    verified = models.BooleanField(default=False)
    commission_terms = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'developers'

    def __str__(self):
        return f"{self.name} {'(Verified)' if self.verified else ''}"
