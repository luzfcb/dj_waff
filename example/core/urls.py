from . import views
from django.conf.urls import url, include
from django.contrib import admin

from . import views

urlpatterns = [
    url(r'^$', views.DocumentTemplateFormView.as_view(), name='home'),
    url(r'~a', views.DocumentTemplateAutocomplete.as_view(), name='document-template-autocomplete'),
]
