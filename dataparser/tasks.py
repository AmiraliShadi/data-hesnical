import requests
from celery import shared_task
from django.conf import settings

from dataparser.models import Report


@shared_task
def send_request():
    api_url = settings.MAIN_SERVER_URL

    reports = Report.objects.filter(url__isnull=True).filter(url='')

    data_to_send = [{'email': report.email, 'account_no': report.account_no} for report in reports]

    for data in data_to_send:
        response = requests.post(api_url, json=data)
        response.raise_for_status()

        if not response.status_code == 404:
            response_data = response.json()
            url = response_data.get('url')

            if url:
                Report.objects.filter(id=data['report_id']).update(url=url)
            else:
                continue
