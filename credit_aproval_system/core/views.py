# core/views.py
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Customer
from .serializers import CustomerSerializer
from .models import Loan

class CustomerRegistration(APIView):
    def post(self, request, *args, **kwargs):
        # Extract data from the request, ensure customer_number is included
        data = request.data
        data['customer_number'] = get_next_customer_number()

        # Calculate the approved limit based on the provided relation
        monthly_salary = float(data.get('monthly_salary', 0))
        data['approved_limit'] = round(36 * monthly_salary, -5)

        # Exclude 'approved_limit' from the serializer's output
        serializer = CustomerSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def get_next_customer_number():
    # Replace this with your logic to get the next customer number,
    # for example, finding the last customer number in the database and adding 1
    last_customer = Customer.objects.last()
    if last_customer:
        return last_customer.customer_number + 1
    return 1  # If there are no existing customers, start with 1

class CustomerDetailsView(APIView):
    def get(self, request, customer_id):
        try:
            customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            return Response({'error': 'Customer not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = CustomerSerializer(customer)
        return Response(serializer.data)
    

class CheckEligibilityView(APIView):
    def get(self, request, customer_id):
        try:
            customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            return Response({'error': 'Customer not found'}, status=status.HTTP_404_NOT_FOUND)

        # Calculate credit score based on the specified components
        credit_score = self.calculate_credit_score(customer)

        # Check loan eligibility based on credit score
        approval, interest_rate, corrected_interest_rate, tenure, monthly_installment = self.check_loan_eligibility(
            credit_score, customer)

        # Calculate monthly installment
        monthly_installment = self.calculate_monthly_installment(customer.approved_limit, corrected_interest_rate, tenure)

        # Prepare response data
        response_data = {
            'customer_id': customer_id,
            'approval': approval,
            'interest_rate': interest_rate,
            'corrected_interest_rate': corrected_interest_rate,
            'tenure': tenure,
            'monthly_installment': monthly_installment
        }

        return Response(response_data)

    def calculate_credit_score(self, customer):
        # Calculate credit score based on the specified components
        emis_paid_on_time = sum([loan.emis_paid_on_time for loan in customer.loan_set.all()])
        total_loans = customer.loan_set.count()
        current_year_loans = customer.loan_set.filter(start_date__year=2023).count()
        loan_approved_volume = sum([loan.loan_amount for loan in customer.loan_set.all()])
        current_loans_sum = sum([loan.monthly_repayment for loan in customer.loan_set.all()])

        # Calculate credit score based on the specified components
        credit_score = 0
        if emis_paid_on_time > 0:
            credit_score += 20
        if total_loans == 0:
            credit_score += 10
        elif 0 < total_loans <= 2:
            credit_score += 5
        elif total_loans > 2:
            credit_score += 2

        if current_year_loans > 0:
            credit_score += 15

        if current_loans_sum > customer.approved_limit:
            credit_score = 0

        return credit_score

    def check_loan_eligibility(self, credit_score, customer):
        # Check loan eligibility based on credit score
        if credit_score > 50:
            approval = True
            interest_rate = customer.approved_limit * 0.1  # You can replace this with your logic
        elif 30 < credit_score <= 50:
            approval = True
            interest_rate = max(12, customer.approved_limit * 0.08)  # You can replace this with your logic
        elif 10 < credit_score <= 30:
            approval = True
            interest_rate = max(16, customer.approved_limit * 0.06)  # You can replace this with your logic
        else:
            approval = False
            interest_rate = 0

        corrected_interest_rate = max(16, interest_rate)
        tenure = 12  # You can replace this with your logic
        monthly_installment = self.calculate_monthly_installment(customer.approved_limit, corrected_interest_rate, tenure)

        return approval, interest_rate, corrected_interest_rate, tenure, monthly_installment

    @staticmethod
    def calculate_monthly_installment(loan_amount, interest_rate, tenure):
        # Convert annual interest rate to monthly and percentage to decimal
        r = (interest_rate / 12) / 100

        # Calculate monthly installment using the EMI formula
        monthly_installment = (loan_amount * r * (1 + r) ** tenure) / ((1 + r) ** tenure - 1)

        return round(monthly_installment, 2)

class ViewLoanDetails(APIView):
    def get(self, request, loan_id):
        try:
            loan = Loan.objects.get(pk=loan_id)
        except Loan.DoesNotExist:
            return Response({'error': 'Loan not found'}, status=status.HTTP_404_NOT_FOUND)

        # Get customer details using the foreign key relationship
        customer = loan.customer
        customer_data = {
            'customer_number': customer.customer_number,  # Replace 'id' with 'customer_number'
            'first_name': customer.first_name,
            'last_name': customer.last_name,
            'phone_number': customer.phone_number,
            'age': customer.age
        }

        # Prepare response data
        response_data = {
            'loan_id': loan.id,
            'customer': customer_data,
            'loan_amount': loan.loan_amount,
            'interest_rate': loan.interest_rate,
            'monthly_repayment': loan.monthly_repayment,
            'tenure': loan.tenure
        }

        return Response(response_data)


class ViewLoansByCustomerId(APIView):
    def get(self, request, customer_id):
        try:
            customer = Customer.objects.get(customer_number=customer_id)
            loans = Loan.objects.filter(customer=customer)

            loan_data = []
            for loan in loans:
                loan_item = {
                    'loan_id': loan.id,  # Use the default id field as the loan_id
                    'loan_amount': loan.loan_amount,
                    'interest_rate': loan.interest_rate,
                    'monthly_installment': loan.monthly_repayment,
                    'repayments_left': loan.tenure - loan.emis_paid_on_time,
                }
                loan_data.append(loan_item)

            return Response(loan_data, status=status.HTTP_200_OK)

        except Customer.DoesNotExist:
            return Response({'error': 'Customer not found'}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Customer, Loan
from datetime import datetime, timedelta

class CreateLoan(APIView):
    def post(self, request):
        try:
            customer_id = request.data.get('customer_id')
            loan_amount = request.data.get('loan_amount')
            interest_rate = request.data.get('interest_rate')
            tenure = request.data.get('tenure')

            customer = Customer.objects.get(customer_number=customer_id)

            # Rest of your loan creation logic
            loan_number = self.generate_unique_loan_number(customer_id)

            loan = Loan.objects.create(
                customer=customer,
                loan_number=loan_number,
                loan_amount=loan_amount,
                tenure=tenure,
                interest_rate=interest_rate,
                monthly_repayment=self.calculate_monthly_repayment(loan_amount, tenure, interest_rate),
                emis_paid_on_time=0,
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=tenure * 30),  # Assuming 30 days per month
            )

            return Response({
                'loan_id': loan.id,
                'customer_id': customer_id,
                'loan_approved': True,
                'message': 'Loan approved',
                'monthly_installment': loan.monthly_repayment,
            }, status=status.HTTP_201_CREATED)

        except Customer.DoesNotExist:
            return Response({'error': 'Customer not found'}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def generate_unique_loan_number(self, customer_id):
        # Logic to generate a unique loan number by incrementing the last row's loan number
        last_loan = Loan.objects.filter(customer_id=customer_id).order_by('-loan_number').first()
        if last_loan:
            return last_loan.loan_number + 1
        else:
            return 1

    def calculate_monthly_repayment(self, loan_amount, tenure, interest_rate):
        # Common logic to calculate the monthly repayment amount
        # Replace this with your actual calculation logic
        # For example, you can use a formula based on loan_amount, tenure, and interest_rate
        return (loan_amount * interest_rate * (1 + interest_rate) ** tenure) / ((1 + interest_rate) ** tenure - 1)
