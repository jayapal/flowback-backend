from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework import serializers

from flowback.common.pagination import LimitOffsetPagination
from flowback.kanban.models import KanbanEntry


class KanbanEntryListApi(APIView):
    class Pagination(LimitOffsetPagination):
        default_limit = 50
        max_limit = 100

    class FilterSerializer(serializers.Serializer):
        origin_type = serializers.CharField(required=False)
        origin_id = serializers.IntegerField(required=False)
        created_by = serializers.IntegerField(required=False)
        assignee = serializers.IntegerField(required=False)
        title__icontains = serializers.CharField(required=False)
        description__icontains = serializers.CharField(required=False)
        tag = serializers.ChoiceField((1, 2, 3, 4, 5), required=False)

    class OutputSerializer(serializers.ModelSerializer):
        class UserSerializer(serializers.Serializer):
            id = serializers.IntegerField(source='user.id')
            profile_image = serializers.ImageField(source='user.profile_image')
            username = serializers.CharField(source='user.username')

        assignee = UserSerializer(read_only=True, required=False)
        created_by = UserSerializer(read_only=True)

        class Meta:
            model = KanbanEntry
            fields = ('id', 'created_by', 'assignee', 'title', 'description', 'tag')


class KanbanEntryCreateAPI(APIView):
    class InputSerializer(serializers.ModelSerializer):
        assignee = serializers.CharField(source='assignee_id')

        class Meta:
            model = KanbanEntry
            fields = ('assignee', 'title', 'description', 'tag')


class KanbanEntryUpdateAPI(APIView):
    class InputSerializer(serializers.Serializer):
        entry_id = serializers.IntegerField()
        assignee = serializers.IntegerField(required=False, source='assignee_id')
        title = serializers.CharField(required=False)
        description = serializers.CharField(required=False)
        tag = serializers.ChoiceField((1, 2, 3, 4, 5), required=False)


class KanbanEntryDeleteAPI(APIView):
    class InputSerializer(serializers.Serializer):
        entry_id = serializers.IntegerField()
