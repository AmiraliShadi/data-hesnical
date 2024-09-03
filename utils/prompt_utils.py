import os
from datetime import datetime

import openai
from django.conf import settings


def save_prompt_log(prompt_instance):
    log_file_path = os.path.join(settings.BASE_DIR, 'AILogs')
    os.makedirs(log_file_path, exist_ok=True)
    log_file_name = os.path.join(log_file_path, f'{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt')

    with open(log_file_name, 'w') as file:
        file.write(f"Date: {prompt_instance.requested_time}\n\n")
        file.write(f"Prompt:\n{prompt_instance.prompt}\n\n")
        file.write(f"Response:\n{prompt_instance.response}\n\n")


def get_chatgpt_response(client, prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
        )
        return response['choices'][0]['message']['content'], None
    except Exception as e:
        return None, str(e)
