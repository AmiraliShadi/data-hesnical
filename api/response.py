from rest_framework.response import Response

from api.status import OK_200


def custom_response(status_code: dict = OK_200, data: dict or list = None, error=None, **extra_data):
    response_data = {
        'detail': status_code.get('detail'),
        'code': status_code.get('code', status_code.get('detail').replace(' ', '_').lower()),
        'error': error,
        'data': data if data else {}
    }

    response_data.update(extra_data)

    return Response(
        data=response_data,
        status=status_code.get('code')
    )
