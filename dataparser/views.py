import json
import os
from datetime import datetime

from django.conf import settings
from rest_framework.views import APIView

from api import status
from api.response import custom_response
from dataparser.models import Report
from dataparser.serializers import ReportSerializer
from utils import constants
from utils.mt4_data_parser import mt4_extract_data_from_html_file
from utils.mt5_data_parser import mt5_extract_data_from_html_file


class HTMLParserApi(APIView):
    def post(self, request):
        email = request.data.get('email')

        if not email:
            return custom_response(error='Email is required.', status_code=status.BAD_REQUEST_400)

        reports = Report.objects.filter(email=email, url__isnull=False).exclude(url='')

        if not reports.exists():
            return custom_response(**{'status': constants.REPORT_STATUS_PENDING})

        data = []
        for report in reports:
            extraction_function = {
                constants.META_TRADER_VERSION_4: mt4_extract_data_from_html_file,
                constants.META_TRADER_VERSION_5: mt5_extract_data_from_html_file
            }.get(report.mt_version)

            if extraction_function:
                response = extraction_function(report.url)
                response.update({
                    'mt_version': report.mt_version,
                    'account_no': report.account_no
                })
                data.append(response)

                json_file_name = f'{report.email}-{report.account_no}-MT{report.mt_version}-{datetime.now().strftime("%Y%m%d%H%M%S")}.json'
                json_file_path = os.path.join(settings.BASE_DIR, 'JSONs', json_file_name)

                with open(json_file_path, 'w') as json_file:
                    json.dump(data, json_file, indent=4)
            else:
                return custom_response(error=f'Unsupported Meta Trader version {report.mt_version}.',
                                       status_code=status.BAD_REQUEST_400)

        return custom_response(data=data, status_code=status.OK_200)


class ReportUpdateApi(APIView):
    def post(self, request):
        email = request.data.get('email')
        account_no = request.data.get('account_no')
        mt_version = request.data.get('mt_version')

        try:
            mt_version = int(mt_version)
        except (TypeError, ValueError):
            return custom_response(error='Meta Trader version must be an integer', status_code=status.BAD_REQUEST_400)

        if mt_version not in [constants.META_TRADER_VERSION_4, constants.META_TRADER_VERSION_5]:
            return custom_response(error='Invalid Meta Trader version', status_code=status.BAD_REQUEST_400)

        if not email or not account_no:
            return custom_response(error='Email and account number are required', status_code=status.BAD_REQUEST_400)

        report = Report.objects.create(
            email=email,
            account_no=account_no,
            mt_version=mt_version,
        )

        return custom_response(data=ReportSerializer(report).data, status_code=status.CREATED_201)
