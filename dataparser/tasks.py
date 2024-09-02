import requests
from celery import shared_task
from django.conf import settings
from django.db.models import Q

from dataparser.models import Report, BalanceHistory
from utils import constants
from utils.mt4_data_parser import mt4_extract_data_from_html_file
from utils.mt5_data_parser import mt5_extract_data_from_html_file


@shared_task
def send_request():
    api_url = settings.MAIN_SERVER_URL
    reports = Report.objects.filter(Q(url__isnull=True) | Q(url=''))
    data_to_send = [{'email': report.email, 'account_no': report.account_no, 'report_id': report.id} for report in reports]

    for data in data_to_send:
        response = requests.post(api_url, data=data)
        response.raise_for_status()

        if not response.status_code == 404:
            response_data = response.json()
            url = response_data.get('url')

            if url:
                Report.objects.filter(id=data['report_id']).update(url=url)
            else:
                continue


@shared_task
def update_balance_history():
    reports = Report.objects.filter(url__isnull=False).exclude(url='')

    for report in reports:
        extraction_function = {
            constants.META_TRADER_VERSION_4: mt4_extract_data_from_html_file,
            constants.META_TRADER_VERSION_5: mt5_extract_data_from_html_file
        }.get(report.mt_version)

        if extraction_function:
            response = extraction_function(report.url)
            balance = response.get('balance')

            if balance:
                print('kir 1')
                BalanceHistory.objects.create(report=report, balance=balance)
                print('kir 2')
                print('='*30)
