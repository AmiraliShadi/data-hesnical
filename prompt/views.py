from django.conf import settings
from openai import OpenAI
from rest_framework.views import APIView

from api import status
from api.response import custom_response
from utils.prompt_utils import save_prompt_log, get_chatgpt_response
from .models import Prompt
from .serializers import PromptSerializer


client = OpenAI(
    api_key=settings.OPENAI_API_KEY,
)


class ChatGPTAPIView(APIView):
    def post(self, request):
        serializer = PromptSerializer(data=request.data)

        if serializer.is_valid():
            prompt = serializer.validated_data.get('prompt')

            response, error = get_chatgpt_response(client, prompt)

            if error:
                return custom_response(error=error, status_code=status.SERVER_ERROR_500)

            prompt_instance = Prompt.objects.create(prompt=prompt, response=response)

            save_prompt_log(prompt_instance)

            return custom_response(data=PromptSerializer(prompt_instance).data, status_code=status.CREATED_201)

        return custom_response(error=serializer.errors, status_code=status.BAD_REQUEST_400)
