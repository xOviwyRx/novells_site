from rest_framework import serializers

from .models import Novell

class NovellListSerializer(serializers.ModelSerializer):


    class Meta:
        model = Novell
        fields = ('__all__')