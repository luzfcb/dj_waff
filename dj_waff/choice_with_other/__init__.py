# based on https://github.com/DjangoAdminHackers/select-url-field/blob/master/select_url_field/choice_with_other.py
#
from django import forms
from django.utils.encoding import force_text
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .widget_compat import RadioChoiceInput, RadioFieldRenderer, ChoiceFieldRenderer, RadioSelect

OTHER_CHOICE = '__other__'
OTHER_CHOICE_DISPLAY = ''  # 'Other:'


class RadioChoiceInputWithOther(RadioChoiceInput):
    def render(self, name=None, value=None, attrs=None, choices=()):
        if self.id_for_label:
            label_for = format_html(' for="{}"', self.id_for_label)
        else:
            label_for = ''
        attrs = dict(self.attrs, **attrs) if attrs else self.attrs
        tag_attrs = self.tag(attrs)
        return format_html(
            '<label{}>{} {}<div class="other-field">{{other_form_field}}</div></label>',
            label_for,
            tag_attrs,
            self.choice_label
        )


class ChoiceWithOtherRenderer(RadioFieldRenderer):
    """RadioFieldRenderer that renders its last choice with a placeholder."""
    custom_choice_input_class = RadioChoiceInputWithOther

    def render(self):
        """
        Outputs a <ul> for this set of choice fields.
        If an id was given to the field, it is applied to the <ul> (each
        item in the list will get an id of `$id_$i`).
        """
        id_ = self.attrs.get('id', None)
        output = []
        for i, choice in enumerate(self.choices):
            choice_value, choice_label = choice
            if isinstance(choice_label, (tuple, list)):
                attrs_plus = self.attrs.copy()
                if id_:
                    attrs_plus['id'] += '_{}'.format(i)
                sub_ul_renderer = ChoiceFieldRenderer(name=self.name,
                                                      value=self.value,
                                                      attrs=attrs_plus,
                                                      choices=choice_label)
                sub_ul_renderer.choice_input_class = self.choice_input_class
                output.append(format_html(self.inner_html, choice_value=choice_value,
                                          sub_widgets=sub_ul_renderer.render()))
            else:
                attrs = self.attrs.copy()
                attrs.update(
                    {
                        'data-choice-fields': self.name
                    }
                )
                if OTHER_CHOICE == choice[0]:
                    w = self.custom_choice_input_class(self.name, self.value,
                                                       attrs, choice, i)
                    formated_text = format_html(self.inner_html,
                                                choice_value=w, sub_widgets='')
                else:
                    w = self.choice_input_class(self.name, self.value,
                                                attrs, choice, i)
                    formated_text = format_html(self.inner_html,
                                                choice_value=force_text(w), sub_widgets='')
                output.append(formated_text)
        return format_html(self.outer_html,
                           id_attr=format_html(' id="{}"', id_) if id_ else '',
                           content=mark_safe('\n'.join(output)))


class ChoiceWithOtherWidget(forms.MultiWidget):
    """MultiWidget for use with ChoiceWithOtherField"""

    def __init__(self, choice_field_instance, other_form_field, attrs=None):
        self.other_form_field = other_form_field
        self.other_form_field.widget.is_required = False
        self.other_form_field.widget.attrs.update(
            {
                'data-choice-fields-other': 'data-choice-fields-other'
            }
        )
        widgets = [
            choice_field_instance.widget,
            self.other_form_field.widget
        ]
        self.choices = choice_field_instance.choices
        super(ChoiceWithOtherWidget, self).__init__(widgets, attrs=attrs)

    def decompress(self, value):
        if value:
            # return value
            choices = [c[0] for c in self.choices]
            provided_choices, other_choice = choices[:-1], choices[-1:]
            if value in provided_choices:
                return [value, '']
            else:
                return [OTHER_CHOICE, value]
        return ['', '']

    def format_output(self, rendered_widgets):

        """Format the output by substituting the "other" choice into the first widget"""

        ret = u'<div class="choice_with_other_wrapper" style="display: table-row;">{choices_fields}</div>'.format(
            choices_fields=rendered_widgets[0])
        ret = ret.format(other_form_field=rendered_widgets[1])
        return ret

    class Media:
        js = (
            'dj_waff/choice_with_other.js',
        )


class ChoiceWithOtherField(forms.MultiValueField):
    def __init__(self, other_form_field, has_empty_choice=False, first_is_preselected=False, *args, **kwargs):
        choices = list(kwargs.pop('choices'))
        initial = kwargs.pop('initial', None)
        if has_empty_choice:
            choices.insert(0, ('', '---------'))
        choices.append((OTHER_CHOICE, OTHER_CHOICE_DISPLAY))
        if not choices[0][0] == OTHER_CHOICE and not initial and first_is_preselected:
            initial = choices[0][0]
        choice_field = forms.ChoiceField(choices=choices,
                                         widget=RadioSelect(choices=choices, renderer=ChoiceWithOtherRenderer)
                                         )
        fields = [
            choice_field,
            other_form_field
        ]
        widget = ChoiceWithOtherWidget(choice_field_instance=choice_field, other_form_field=other_form_field)
        self._was_required = kwargs.pop('required', True)
        kwargs['required'] = False
        super(ChoiceWithOtherField, self).__init__(widget=widget, fields=fields, initial=initial, *args, **kwargs)

    def compress(self, value):
        if self._was_required and (not value or value[0] in (None, '')):
            raise forms.ValidationError(self.error_messages['required'])
        if not value:
            return None, ''
        if value[0] == OTHER_CHOICE:
            if value[1] is None:
                raise forms.ValidationError(self.error_messages['required'])
            ret = value[1]
        else:
            ret = value[0]
        return value[0], ret
