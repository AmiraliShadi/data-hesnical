from rest_framework import serializers

from dataparser.models import Report, BalanceHistory


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = "__all__"


class BalanceHistorySerializer(serializers.ModelSerializer):
    timestamp = serializers.DateTimeField(format='%Y-%m-%dT%H:%M:%S.%fZ')  # ISO 8601 format

    class Meta:
        model = BalanceHistory
        fields = ['balance', 'timestamp']
