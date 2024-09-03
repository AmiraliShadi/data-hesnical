from rest_framework import serializers
from .models import Prompt


class PromptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prompt
        fields = ['uuid', 'prompt', 'response', 'requested_time']
        read_only_fields = ['response', 'requested_time']
