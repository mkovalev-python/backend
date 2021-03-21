from datetime import datetime
from pathlib import Path

from django.shortcuts import render

# Create your views here.
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from model.models import PermissionUser, Profile, Permission, Team, Country
from model.serializer import PermissionUserSerializer, ProfileSerializer, PermissionSerializer, TeamSerializer, \
    CountrySerializer, UserSerializerWithToken


class CheckPermission(APIView):
    permissions_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request):
        queryset = PermissionUser.objects.filter(username=request.user.username)
        serializer = PermissionUserSerializer(queryset, many=True).data

        return Response(serializer)


class GetUserInfo(APIView):
    permissions_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request):
        queryset = Profile.objects.filter(username=request.user.username)
        serializer_user = ProfileSerializer(queryset, many=True).data
        get_permission_name = Permission.objects.filter(slug=request.query_params['permission'])
        serializer_permission = PermissionSerializer(get_permission_name, many=True).data

        return Response({'user': serializer_user, 'permission': serializer_permission})


class GetListOption(APIView):
    permissions_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request):
        queryset_permission = Permission.objects.all()
        queryset_team = Team.objects.all()
        queryset_country = Country.objects.all()

        serializer_permission = PermissionSerializer(queryset_permission, many=True).data
        serializer_team = TeamSerializer(queryset_team, many=True).data
        serializer_country = CountrySerializer(queryset_country, many=True).data
        return Response({'team': serializer_team, 'permission': serializer_permission, 'country': serializer_country})


class PostCreateUser(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def post(request):
        req = request.data

        serializer = UserSerializerWithToken(
            data={'username': request.data['username'], 'password': request.data['password']})
        if serializer.is_valid():
            #serializer.save()


        return Response()
