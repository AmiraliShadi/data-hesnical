import os

from bs4 import BeautifulSoup
from django.conf import settings
from rest_framework.views import APIView

from api import status
from api.response import custom_response
from dataparser.utils import extract_data_from_html_file


class HTMLParserApi(APIView):
    def post(self, request, *args, **kwargs):
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
