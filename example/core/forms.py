from dal import autocomplete
from django import forms

from dj_waff.choice_with_other import ChoiceWithOtherField
from .models import DocumentTemplate

SET_OF_CHOICES = [
    ('choice1', 'choice1111'),
    ('choice2', 'choice2222'),
    # ('choice3', lambda b: DocumentTemplate.objects.get(pk=1)),
]


class MyCustomForm(forms.Form):
    other_form_field = forms.CharField(required=False)
    document_template = ChoiceWithOtherField(
        choices=SET_OF_CHOICES,
        other_form_field=forms.ModelChoiceField(
            queryset=DocumentTemplate.objects.all(),
            required=True,
            # widget=autocomplete.ModelSelect2(url='document-template-autocomplete', ),
        )
    )
    document_template2 = ChoiceWithOtherField(
        choices=SET_OF_CHOICES,
        first_is_preselected=True,
        other_form_field=forms.ModelChoiceField(
            queryset=DocumentTemplate.objects.all(),
            required=True,
            widget=autocomplete.ModelSelect2(url='document-template-autocomplete', ),
        )
    )

    document_template3 = ChoiceWithOtherField(
        choices=SET_OF_CHOICES,
        initial=SET_OF_CHOICES[1][0],
        other_form_field=forms.CharField(
            widget=forms.Textarea()
        )
    )
    document_template4 = ChoiceWithOtherField(
        choices=SET_OF_CHOICES,
        initial=SET_OF_CHOICES[1][0],
        other_form_field=forms.CharField(
            # widget=forms.IntegerField()
        )
    )
    document_template5 = ChoiceWithOtherField(
        choices=SET_OF_CHOICES,
        initial=SET_OF_CHOICES[1][0],
        other_form_field=forms.CharField(
            # widget=forms.TimeField()
        )
    )

    maria = forms.ModelChoiceField(
        queryset=DocumentTemplate.objects.all(),
        required=True,
        widget=autocomplete.ModelSelect2(url='document-template-autocomplete', ),
    )

    teste = forms.ChoiceField(choices=SET_OF_CHOICES, initial=SET_OF_CHOICES[0])
