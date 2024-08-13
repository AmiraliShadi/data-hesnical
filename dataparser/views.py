import os

import requests
from django.conf import settings
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView

from api import status
from api.response import custom_response
from utils import constants
from utils.data_parser import extract_data_from_html_file
from utils.validators import transform_email


class HTMLParserApi(APIView):
    def post(self, request):
        email = request.data.get('email')

        if not email:
            return custom_response(error='Email is required.', status_code=status.BAD_REQUEST_400)

        directory = os.path.join(settings.BASE_DIR, 'HTMLs', transform_email(email))
        report_file_path = os.path.join(directory, f'{transform_email(email)}-report.html')

        if os.path.exists(report_file_path):
            data = extract_data_from_html_file(report_file_path)
            return custom_response(data=data, status_code=status.OK_200)

        try:
            response = requests.post(settings.MAIN_SERVER_URL, data={'email': email})
            response.raise_for_status()

            validation = response.json().get('validation')
            url = response.json().get('url')

            if int(validation) == 1 and url:
                return self._handle_successful_validation(url)
            else:
                data_status = self._get_data_status(validation)
                return custom_response(status_code=status.OK_200, extra_data={'status': data_status})

        except requests.RequestException as e:
            return custom_response(error=f'Request failed: {str(e)}', status_code=status.SERVER_ERROR_500)

    def _handle_successful_validation(self, url):
        try:
            report_file = requests.get(url)
            if report_file.status_code == 200:
                data = extract_data_from_html_file(report_file.text)
                return custom_response(data=data, status_code=status.OK_200)
            else:
                return custom_response(
                    error=f'Failed to download file: Status code {report_file.status_code}',
                    status_code=status.SERVER_ERROR_500
                )
        except requests.RequestException as e:
            return custom_response(error=f'Failed to download file: {str(e)}',
                                   status_code=status.SERVER_ERROR_500)

    def _get_data_status(self, validation):
        if int(validation) == 0:
            return constants.REPORT_STATUS_NOT_ENTERED
        elif int(validation) == -1:
            return constants.REPORT_STATUS_PENDING
        else:
            return constants.REPORT_STATUS_FAILURE


class ReportUploadApi(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        email = request.data.get('email')

        if 'file' not in request.FILES:
            return custom_response(error='No file provided.', status_code=status.BAD_REQUEST_400)

        file = request.FILES['file']

        directory = os.path.join(settings.BASE_DIR, f"HTMLs/{transform_email(email)}")
        if not os.path.exists(directory):
            os.makedirs(directory)

        save_path = os.path.join(directory, f'{transform_email(email)}-report.html')

        with open(save_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        return custom_response(status_code=status.CREATED_201,)
