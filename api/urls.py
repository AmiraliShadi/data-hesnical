from django.urls import path, include

urlpatterns = [
    path('data-parser/', include('dataparser.urls')),
    path('prompt/', include('prompt.urls')),
]
