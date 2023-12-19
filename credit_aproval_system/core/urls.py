# urls.py

from django.urls import path
from .views import CustomerRegistration, CustomerDetailsView, CheckEligibilityView, ViewLoansByCustomerId
from .views import ViewLoanDetails, CreateLoan  # Import the CreateLoan view

urlpatterns = [
    path('register/', CustomerRegistration.as_view(), name='customer-registration'),
    path('register/<int:customer_id>/', CustomerDetailsView.as_view(), name='customer-details'),
    path('check-eligibility/<int:customer_id>/', CheckEligibilityView.as_view(), name='check-eligibility'),
    path('view-loan/<int:loan_id>/', ViewLoanDetails.as_view(), name='view_loan_details'),
    path('view-loans/<int:customer_id>/', ViewLoansByCustomerId.as_view(), name='view_loans_by_customer_id'),
    
    # Add the path for create-loan
    path('create-loan/', CreateLoan.as_view(), name='create-loan'),

    # Add other URLs as needed
]
