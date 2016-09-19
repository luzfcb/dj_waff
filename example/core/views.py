from dal import autocomplete
from django.db.models import Q
from django.shortcuts import render
from django.utils import six
from django.utils.decorators import method_decorator
from django.views import generic
from django.views.decorators.cache import never_cache

from .models import DocumentTemplate
from .forms import MyCustomForm


class DocumentTemplateFormView(generic.FormView):
    template_name = 'core/document_form.html'
    form_class = MyCustomForm


class DocumentTemplateAutocomplete(autocomplete.Select2QuerySetView):
    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        return super(DocumentTemplateAutocomplete, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = DocumentTemplate.objects.all()

        if self.q:
            qs = qs.filter(Q(name__icontains=self.q))
        return qs

    def get_result_label(self, result):
        return six.text_type(result.name)
