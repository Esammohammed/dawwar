import uuid
from django.db import models
from django.conf import settings
from apps.listings.models import Listing

class VerificationStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    VERIFIED = 'verified', 'Verified'
    REJECTED = 'rejected', 'Rejected'

class CommissionPayer(models.TextChoices):
    BUYER = 'buyer', 'Buyer'
    SELLER = 'seller', 'Seller'

class ExitListing(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    listing = models.OneToOneField(Listing, related_name='exit_profile', on_delete=models.CASCADE)
    
    developer_current_price = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    owner_confirmed_no_markup = models.BooleanField(default=False)
    
    verification_status = models.CharField(
        max_length=20, 
        choices=VerificationStatus.choices, 
        default=VerificationStatus.PENDING
    )
    verification_notes = models.TextField(blank=True, null=True)
    
    commission_payer = models.CharField(
        max_length=20, 
        choices=CommissionPayer.choices, 
        default=CommissionPayer.BUYER
    )
    commission_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=settings.EXIT_DEFAULT_COMMISSION_RATE
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'exit_listings'
        
    def __str__(self):
        return f"Exit Profile for {self.listing.title}"

class DocumentType(models.TextChoices):
    CONTRACT = 'contract', 'Contract'
    PAYMENT_RECEIPT = 'payment_receipt', 'Payment Receipt'
    OTHER = 'other', 'Other'

class ExitDocument(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exit_listing = models.ForeignKey(ExitListing, related_name='documents', on_delete=models.CASCADE)
    
    doc_type = models.CharField(
        max_length=20, 
        choices=DocumentType.choices, 
        default=DocumentType.OTHER
    )
    file = models.FileField(upload_to='exit_docs/%Y/%m/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'exit_documents'
        ordering = ['-uploaded_at']
        
    @property
    def url(self) -> str:
        return self.file.url if self.file else ''

    def __str__(self):
        return f"{self.doc_type} for {self.exit_listing.listing.title}"

class ExitLead(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone = models.CharField(max_length=20, null=True, blank=True)
    contract_price = models.DecimalField(max_digits=14, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=14, decimal_places=2)
    years_paid = models.DecimalField(max_digits=4, decimal_places=2)
    computed_result = models.JSONField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'exit_leads'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Lead: {self.phone or 'Anonymous'} at {self.created_at}"
