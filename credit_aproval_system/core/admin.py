from django.contrib import admin
from core.models import Customer, Loan

# Register your models here.

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    pass


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    pass