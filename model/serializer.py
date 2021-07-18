from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.settings import api_settings

from model.models import PermissionUser, Profile, Permission, Team, Country, Polls, Questions, Rating, SessionTC, \
    LogPoint, PollsCheck, QuestionsCheck, RatingTeam, Test, QuestionsCheckTest


class ProfileSerializer(serializers.ModelSerializer):
    """Сериалайзер информации пользователя"""

    children = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = '__all__'

    @staticmethod
    def get_children(obj):
        return PollsCheckSerializer(PollsCheck.objects.filter(user_valuer_id=obj.id),
                                    many=True).data


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
        fields = ('token', 'username', 'password', 'email')


class PollsSerializer(serializers.ModelSerializer):
    """Сериалайзер опросов"""

    class Meta:
        model = Polls
        fields = ('id', 'title', 'description', 'points', 'session','datePosting')


class QuestionsSerializer(serializers.ModelSerializer):
    """Сериалайзер вопросов"""

    class Meta:
        model = Questions
        fields = '__all__'


class RatingSerializer(serializers.ModelSerializer):
    """Сериалайзер рейтинга"""

    user = serializers.SerializerMethodField()
    team = serializers.SerializerMethodField()
    session = serializers.SerializerMethodField()

    class Meta:
        model = Rating
        fields = ['rating', 'user', 'points', 'team', 'session']

    @staticmethod
    def get_user(obj):
        user = Profile.objects.get(username=obj.username)
        return user.first_name + ' ' + user.last_name

    @staticmethod
    def get_team(obj):
        user = Profile.objects.get(username=obj.username)
        return user.team_id

    @staticmethod
    def get_session(obj):
        user = Profile.objects.get(username=obj.username)
        return user.session.number_session


class SessionTCSerializer(serializers.ModelSerializer):
    """Сериалайзер смен"""

    class Meta:
        model = SessionTC
        fields = '__all__'


class LogPointSerializer(serializers.ModelSerializer):
    """Сериалайзер логов по баллам"""

    class Meta:
        model = LogPoint
        fields = ['username', 'points', 'poll', 'date']


class PollsCheckSerializer(serializers.ModelSerializer):
    """Сериалайзер пройденных опросов"""

    class Meta:
        model = PollsCheck
        fields = '__all__'


class QuestionsCheckSerializer(serializers.ModelSerializer):
    """Сериалайзер пройденных вопросов"""

    class Meta:
        model = QuestionsCheck
        fields = '__all__'


class RatingTeamSerializer(serializers.ModelSerializer):
    """Сериалайзер рейтинга команды"""

    class Meta:
        model = RatingTeam
        fields = '__all__'


class TestSerializer(serializers.ModelSerializer):
    """Сериалайзер теста"""

    class Meta:
        model = Test
        fields = '__all__'


class QuestionsCheckSerializerTest(serializers.ModelSerializer):
    """Сериалайзер пройденных вопросов"""

    class Meta:
        model = QuestionsCheckTest
        fields = '__all__'