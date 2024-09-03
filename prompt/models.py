import uuid
from django.db import models


class Prompt(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    prompt = models.TextField()
    response = models.TextField()
    requested_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.prompt[:50]
