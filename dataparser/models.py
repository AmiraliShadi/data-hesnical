from django.db import models

from utils import constants


class Report(models.Model):
    MT_VERSION_CHOICES = [
        (constants.META_TRADER_VERSION_4, 'MT4'),
        (constants.META_TRADER_VERSION_5, 'MT5'),
    ]

    email = models.EmailField()
    account_no = models.CharField(max_length=10, unique=True)
    mt_version = models.PositiveSmallIntegerField(choices=MT_VERSION_CHOICES)
    url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.email


class BalanceHistory(models.Model):
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='balance_history')
    balance = models.CharField(max_length=20)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.report.email} - {self.balance} - {self.timestamp}'
