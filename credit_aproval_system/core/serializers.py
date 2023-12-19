# serializers.py

from rest_framework import serializers
from .models import Customer

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'
        extra_kwargs = {
            'approved_limit': {'read_only': True},
            'customer_number': {'read_only': True},
        }
