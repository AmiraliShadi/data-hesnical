from django.urls import path

from . import views

urlpatterns = [
    path('html-parser/', views.HTMLParserApi.as_view(), name='html-parser'),
    path('upload-report/', views.ReportUpdateApi.as_view(), name='upload-report'),
]
