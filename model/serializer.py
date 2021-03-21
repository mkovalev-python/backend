from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.settings import api_settings

from model.models import PermissionUser, Profile, Permission, Team, Country


class ProfileSerializer(serializers.ModelSerializer):
    """Сериалайзер информации пользователя"""

    class Meta:
        model = Profile
        fields = '__all__'


class PermissionUserSerializer(serializers.ModelSerializer):
    """Сериалайзер ролей пользователя системы"""

    class Meta:
        model = PermissionUser
        fields = '__all__'


class PermissionSerializer(serializers.ModelSerializer):
    """Сериалайзер ролей системы"""

    class Meta:
        model = Permission
        fields = '__all__'


class TeamSerializer(serializers.ModelSerializer):
    """Сериалайзер команд"""

    class Meta:
        model = Team
        fields = '__all__'


class CountrySerializer(serializers.ModelSerializer):
    """Сериалайзер команд"""

    class Meta:
        model = Country
        fields = '__all__'


class UserSerializerWithToken(serializers.ModelSerializer):
    token = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True)

    @staticmethod
    def get_token(obj):
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(obj)
        token = jwt_encode_handler(payload)
        return token

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance

    class Meta:
        model = User
        fields = ('token', 'username', 'password')
