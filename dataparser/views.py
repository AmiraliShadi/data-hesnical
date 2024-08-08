import os

from django.conf import settings
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView

from api import status
from api.response import custom_response
from dataparser.utils import extract_data_from_html_file


class HTMLParserApi(APIView):
    def post(self, request):
        account_id = request.data.get('account_id')
        if not account_id:
            return custom_response(status_code=status.BAD_REQUEST_400)

        htmls_dir = os.path.join(settings.BASE_DIR, 'HTMLs')

        account_dir = os.path.join(htmls_dir, str(account_id))
        if not os.path.exists(account_dir):
            return custom_response(error='Account directory not found!', status_code=status.NOT_FOUND_404)

        report_file = os.path.join(account_dir, f'{account_id}_report.html')
        if not os.path.exists(report_file):
            return custom_response(error='Report file not found!', status_code=status.NOT_FOUND_404)

        data = extract_data_from_html_file(report_file)

        return custom_response(data=data, status_code=status.OK_200)


class ReportUploadApi(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        if 'file' not in request.FILES:
            return custom_response(error='No file provided.', status_code=status.BAD_REQUEST_400)

        file = request.FILES['file']

        filename = file.name
        if not filename.startswith('ReportHistory-') or not filename.endswith('.html'):
            return custom_response(error='File name format is invalid.', status_code=status.BAD_REQUEST_400)

        core_name = filename[len('ReportHistory-'):-len('.html')]
        if not core_name.isdigit():
            return custom_response(error='Account ID must be numeric.', status_code=status.BAD_REQUEST_400)

        account_id = core_name

        directory = os.path.join(settings.BASE_DIR, f"HTMLs/{account_id}")
        if not os.path.exists(directory):
            os.makedirs(directory)

        save_path = os.path.join(directory, f'{account_id}_report.html')

        with open(save_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        return custom_response(status_code=status.CREATED_201)
