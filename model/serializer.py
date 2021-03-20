from django.contrib.auth.models import User
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    """Сериалайзер авторизации пользователя"""

    class Meta:
        model = User
        fields = '__all__'
